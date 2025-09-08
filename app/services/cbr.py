from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
import os
from threading import Lock
import time
from typing import Any, NamedTuple
import xml.etree.ElementTree as ET

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.settings import get_configs, get_settings
from app.struct_logger import logger


@lru_cache(maxsize=1)
def _load_currency_codes() -> set[str]:
    cfg = get_configs().rates
    codes = cfg.get("live_currency_codes") or []
    result = {str(c).upper().strip() for c in codes if c}
    if not result:
        result = {"USD", "EUR", "JPY", "CNY", "AED"}
    return result


def reset_currency_codes_cache() -> None:  # helper if configs refreshed dynamically
    _load_currency_codes.cache_clear()  # type: ignore[attr-defined]


class CacheEntry(NamedTuple):
    rates: dict[str, float]
    fetched_at: float


class CBRFetchError(Exception):
    pass


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

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(CBRFetchError),
    )
    def _do_fetch(self, url: str) -> dict[str, float]:
        try:
            resp = httpx.get(url, timeout=10.0)
            resp.raise_for_status()
        except Exception as e:  # pragma: no cover
            raise CBRFetchError(str(e)) from e
        parsed = self._parse_xml(resp.text)
        if not parsed:
            raise CBRFetchError("empty_or_unparsed_response")
        return parsed

    def fetch_rates(self, force: bool = False) -> dict[str, float] | None:
        """Thread-safe получение курсов валют от ЦБ РФ."""
        settings = get_settings()

        # Deterministic tests: never fetch live inside pytest unless force=True
        if os.getenv("PYTEST_CURRENT_TEST") and not force:
            return None
        if not settings.enable_live_cbr and not force:
            return None

        # Быстрая проверка кеша под блокировкой чтения
        with self._lock:
            if not force and self._is_cache_valid(settings.cbr_cache_ttl_seconds):
                # Возвращаем копию данных для безопасности
                return dict(self._cache.rates)

        # Кеш невалиден, загружаем новые данные
        try:
            parsed = self._do_fetch(settings.cbr_url)
            # Обновляем кеш под блокировкой
            with self._lock:
                self._cache = CacheEntry(rates=parsed, fetched_at=time.time())
            logger.info("cbr_rates_fetched", count=len(parsed), retries="ok")
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
                return {"cached": False, "rates_count": 0, "currencies": sorted(_load_currency_codes())}

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


cbr_service = CBRRatesService()


def fetch_cbr_rates(force: bool = False) -> dict[str, float] | None:
    """Публичный API для получения курсов ЦБ РФ (совместимость)."""
    return cbr_service.fetch_rates(force)


def parse_cbr_xml(xml_text: str) -> dict[str, float]:
    """Совместимый экспорт парсера для тестов (оборачивает метод сервиса)."""
    return cbr_service._parse_xml(xml_text)


def get_effective_rates(
    base_rates_conf: dict[str, Any],
    rates_service: CBRRatesService | None = None,
) -> dict[str, Any]:
    """Возвращает объединенную конфигурацию курсов (статические + живые)."""
    merged = dict(base_rates_conf)
    currencies = dict(merged.get("currencies", {}))

    live = fetch_cbr_rates() if rates_service is None else rates_service.fetch_rates()

    if live:
        currencies.update(live)
        merged["live_source"] = "cbr"
        merged["live_codes"] = sorted(_load_currency_codes())
    else:
        merged["live_source"] = None

    merged["currencies"] = currencies
    if "EUR_RUB" not in currencies:
        logger.error("eur_rate_missing", source=merged.get("live_source"))
    return merged
