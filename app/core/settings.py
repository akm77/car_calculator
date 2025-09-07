from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml


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


class ConfigRegistry(BaseModel):
    fees: dict[str, Any]
    commissions: dict[str, Any]
    rates: dict[str, Any]
    duties: dict[str, Any]

    @classmethod
    def load(cls) -> ConfigRegistry:
        return cls(
            fees=_read_yaml("fees.yml"),
            commissions=_read_yaml("commissions.yml"),
            rates=_read_yaml("rates.yml"),
            duties=_read_yaml("duties.yml"),
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
