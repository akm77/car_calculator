from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
import time
from typing import Any, NamedTuple
import xml.etree.ElementTree as ET

import httpx

from app.core.settings import get_settings, get_configs
from app.struct_logger import logger


# Removed hardcoded currencies; will load from config
CURRENCY_CODES_OF_INTEREST: set[str] | None = None


def _load_currency_codes() -> set[str]:
    global CURRENCY_CODES_OF_INTEREST
    if CURRENCY_CODES_OF_INTEREST is None:
        cfg = get_configs().rates
        codes = cfg.get("live_currency_codes") or []
        CURRENCY_CODES_OF_INTEREST = {str(c).upper().strip() for c in codes if c}
        if not CURRENCY_CODES_OF_INTEREST:
            # Fallback default if config missing
            CURRENCY_CODES_OF_INTEREST = {"USD", "EUR", "JPY", "CNY", "AED"}
    return CURRENCY_CODES_OF_INTEREST


class CacheEntry(NamedTuple):
    rates: dict[str, float]
    fetched_at: float


@dataclass
class CBRRatesService:
    """Thread-safe сервис для получения курсов валют от ЦБ РФ."""

    _cache: CacheEntry | None = field(default=None, init=False)
    _lock: Lock = field(default_factory=Lock, init=False)

    def _parse_xml(self, xml_text: str) -> dict[str, float]:
        """Парсит XML ответ от ЦБ РФ."""
        rates: dict[str, float] = {}
        root = ET.fromstring(xml_text)
        interested = _load_currency_codes()
        for valute in root.findall("Valute"):
            code_el = valute.find("CharCode")
            vunit_el = valute.find("VunitRate")
            if code_el is None or vunit_el is None:
                continue
            code = (code_el.text or "").strip().upper()
            if code not in interested:
                continue
            raw_val = (vunit_el.text or "").strip().replace(",", ".")
            try:
                value = float(raw_val)
                rates[f"{code}_RUB"] = value
            except ValueError:  # pragma: no cover
                logger.warning("cbr_parse_failed", code=code, raw=raw_val)
                continue
        return rates

    def _is_cache_valid(self, ttl_seconds: int) -> bool:
        """Проверяет валидность кеша. ДОЛЖЕН вызываться внутри блокировки!"""
        if not self._cache:
            return False
        return (time.time() - self._cache.fetched_at) < ttl_seconds

    def fetch_rates(self, force: bool = False) -> dict[str, float] | None:
        """Thread-safe получение курсов валют от ЦБ РФ."""
        settings = get_settings()

        if not settings.enable_live_cbr and not force:
            return None

        # Быстрая проверка кеша под блокировкой чтения
        with self._lock:
            if not force and self._is_cache_valid(settings.cbr_cache_ttl_seconds):
                # Возвращаем копию данных для безопасности
                return dict(self._cache.rates)

        # Кеш невалиден, загружаем новые данные
        try:
            resp = httpx.get(settings.cbr_url, timeout=10.0)
            resp.raise_for_status()

            parsed = self._parse_xml(resp.text)

            # Обновляем кеш под блокировкой
            with self._lock:
                self._cache = CacheEntry(rates=parsed, fetched_at=time.time())

            logger.info("cbr_rates_fetched", count=len(parsed))
        except Exception as e:  # pragma: no cover
            logger.warning("cbr_fetch_failed", error=str(e))
            return None
        else:
            return parsed

    def get_cached_rates(self) -> dict[str, float] | None:
        """Получает курсы только из кеша без обращения к API."""
        with self._lock:
            if self._cache:
                return dict(self._cache.rates)
            return None

    def clear_cache(self) -> None:
        """Очищает кеш курсов."""
        with self._lock:
            self._cache = None

    def get_cache_info(self) -> dict[str, Any]:
        """Возвращает информацию о состоянии кеша."""
        with self._lock:
            if not self._cache:
                return {"cached": False, "rates_count": 0}

            settings = get_settings()
            age_seconds = time.time() - self._cache.fetched_at
            is_valid = age_seconds < settings.cbr_cache_ttl_seconds

            return {
                "cached": True,
                "rates_count": len(self._cache.rates),
                "fetched_at": self._cache.fetched_at,
                "age_seconds": age_seconds,
                "is_valid": is_valid,
                "ttl_seconds": settings.cbr_cache_ttl_seconds,
                "currencies": sorted(_load_currency_codes()),
            }


_cbr_service = CBRRatesService()


def fetch_cbr_rates(force: bool = False) -> dict[str, float] | None:
    """Публичный API для получения курсов ЦБ РФ (совместимость)."""
    return _cbr_service.fetch_rates(force)


def parse_cbr_xml(xml_text: str) -> dict[str, float]:
    """Совместимый экспорт парсера для тестов (оборачивает метод сервиса)."""
    return _cbr_service._parse_xml(xml_text)


def get_effective_rates(
    base_rates_conf: dict[str, Any],
    rates_service: CBRRatesService | None = None,
) -> dict[str, Any]:
    """Возвращает объединенную конфигурацию курсов (статические + живые).
    Если сервис не передан явно – используем fetch_cbr_rates() чтобы сохранить
    обратную совместимость с тестами, которые monkeypatch'ят функцию.
    """
    merged = dict(base_rates_conf)
    currencies = dict(merged.get("currencies", {}))

    live = fetch_cbr_rates() if rates_service is None else rates_service.fetch_rates()

    if live:
        currencies.update(live)
        merged["live_source"] = "cbr"
        merged["live_codes"] = sorted(_load_currency_codes())

    merged["currencies"] = currencies
    return merged
