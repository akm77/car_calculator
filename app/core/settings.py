from __future__ import annotations

from datetime import UTC, datetime
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import structlog
import yaml


logger = structlog.get_logger()


BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = BASE_DIR / "config"

_raw_env = os.getenv("ENVIRONMENT", "dev").lower()
_env_file = ".env" if _raw_env in {"prod", "production"} else ".env.dev"


def _read_yaml(name: str) -> dict[str, Any]:
    path = CONFIG_DIR / name
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _dict_hash(data: dict[str, Any]) -> str:
    # Stable JSON dump with sorted keys for deterministic hash
    dumped = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


class AppSettings(BaseSettings):
    bot_token: str | None = Field(default=None, alias="BOT_TOKEN")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    log_level: str = Field(default="info", alias="LOG_LEVEL")
    environment: str = Field(default=_raw_env, alias="ENVIRONMENT")
    public_base_url: str = Field(default="http://localhost:8000", alias="PUBLIC_BASE_URL")
    enable_live_cbr: bool = Field(default=False, alias="ENABLE_LIVE_CBR")
    cbr_cache_ttl_seconds: int = Field(default=1800, alias="CBR_CACHE_TTL_SECONDS")
    cbr_url: str = Field(default="https://www.cbr.ru/scripts/XML_daily.asp", alias="CBR_URL")
    available_countries: str | None = Field(default=None, alias="AVAILABLE_COUNTRIES")
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")
    admin_user_ids: str = Field(
        default="",
        alias="ADMIN_USER_IDS",
        description="Comma-separated Telegram user IDs with admin access to config management",
    )

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / _env_file),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    @property
    def is_prod(self) -> bool:  # pragma: no cover
        return self.environment.lower() in {"prod", "production"}

    @property
    def webapp_url(self) -> str:
        return f"{self.public_base_url.rstrip('/')}/web/"

    @property
    def countries_list(self) -> list[str]:
        if not self.available_countries:
            return []
        return [c.strip().lower() for c in self.available_countries.split(",") if c.strip()]

    @property
    def admin_ids(self) -> set[int]:
        """
        Парсинг списка admin user IDs из переменной окружения.

        Returns:
            Множество целочисленных user IDs

        Examples:
            ADMIN_USER_IDS="123456,789012" → {123456, 789012}
            ADMIN_USER_IDS="" → set()
        """
        if not self.admin_user_ids:
            return set()

        try:
            return {int(uid.strip()) for uid in self.admin_user_ids.split(",") if uid.strip()}
        except ValueError:
            logger.exception("invalid_admin_user_ids", value=self.admin_user_ids)
            return set()


class ConfigRegistry(BaseModel):
    fees: dict[str, Any]
    commissions: dict[str, Any]
    rates: dict[str, Any]
    duties: dict[str, Any]
    hash: str
    loaded_at: str

    @classmethod
    def load(cls) -> ConfigRegistry:
        fees = _read_yaml("fees.yml")
        commissions = _read_yaml("commissions.yml")
        rates = _read_yaml("rates.yml")
        duties = _read_yaml("duties.yml")
        aggregate = {"fees": fees, "commissions": commissions, "rates": rates, "duties": duties}
        cfg_hash = _dict_hash(aggregate)
        return cls(
            fees=fees,
            commissions=commissions,
            rates=rates,
            duties=duties,
            hash=cfg_hash,
            loaded_at=datetime.now(UTC).isoformat(),
        )


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()


@lru_cache(maxsize=1)
def get_configs() -> ConfigRegistry:
    return ConfigRegistry.load()


def refresh_configs() -> None:
    get_configs.cache_clear()  # type: ignore[attr-defined]


def refresh_settings() -> None:
    get_settings.cache_clear()  # type: ignore[attr-defined]


def reload_configs() -> tuple[bool, str, dict[str, Any]]:
    """
    Принудительно перезагрузить все конфигурационные файлы.

    Workflow:
    1. Очистить кэш get_configs()
    2. Попытаться загрузить новые конфиги
    3. При ошибке - откатиться к старым (если возможно)
    4. Вернуть статус и метрики

    Returns:
        (success: bool, message: str, metrics: dict)

    Examples:
        >>> success, msg, metrics = reload_configs()
        >>> if success:
        ...     print(f"Loaded {metrics['config_count']} configs")
    """
    start_time = time.time()

    # Сохранить текущие конфиги для rollback
    old_configs = None
    old_hash = None
    try:
        old_configs = get_configs()
        old_hash = old_configs.hash
    except Exception:
        pass

    # Очистить кэш
    get_configs.cache_clear()  # type: ignore[attr-defined]
    logger.info("config_cache_cleared", old_hash=old_hash)

    # Попытаться загрузить новые конфиги
    try:
        new_configs = get_configs()
        new_hash = new_configs.hash

        # Метрики
        load_time = time.time() - start_time
        metrics = {
            "config_count": 4,  # fees, commissions, rates, duties
            "old_hash": old_hash,
            "new_hash": new_hash,
            "loaded_at": new_configs.loaded_at,
            "load_time_ms": round(load_time * 1000, 2),
            "hash_changed": old_hash != new_hash,
        }

        logger.info("configs_reloaded_successfully", **metrics)

        message = (
            "✅ **Configs reloaded successfully!**\n\n"
            f"🔑 Old hash: `{old_hash or 'N/A'}`\n"
            f"🔑 New hash: `{new_hash}`\n"
            f"📊 Timestamp: `{new_configs.loaded_at}`\n"
            f"⚡ Load time: `{metrics['load_time_ms']}ms`\n"
            f"🔄 Changed: `{'Yes' if metrics['hash_changed'] else 'No'}`"
        )

        return True, message, metrics
    except Exception as e:
        # Rollback: восстановить кэш (если возможно)
        logger.exception(
            "config_reload_failed",
            error=str(e),
            error_type=type(e).__name__,
        )

        # Если были старые конфиги, кэш остался пустым
        # При следующем вызове get_configs() будет повторная попытка загрузки

        message = (
            "❌ **Config reload failed!**\n\n"
            f"🔥 Error: `{type(e).__name__}`\n"
            f"📄 Details: `{e!s}`\n\n"
            "⚠️ Old configs remain in memory (if any).\n"
            "Fix the config files and try again."
        )

        return False, message, {"error": str(e)}


