"""
Хэндлеры для управления конфигурационными файлами через Telegram.

Поддерживаемые файлы:
- config/fees.yml: Тарифы стран и фрахта
- config/commissions.yml: Комиссии (включая bank_commission)
- config/rates.yml: Курсы валют и утильсбор
- config/duties.yml: Таблицы пошлин

Команды:
- /get_{config}: Скачать файл
- /set_{config}: Загрузить новый файл
- /reload_configs: Перезагрузить все конфиги в памяти

Безопасность:
- Доступ только для администраторов (через middleware)
- Валидация YAML перед сохранением
- Автоматический бэкап старых версий

Changelog:
- 2025-12-28: CONFIG-01 - Создан базовый модуль с FSM states и helper-функциями
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from aiogram import Router
from aiogram.fsm.state import State, StatesGroup


# ============================================================================
# CONSTANTS
# ============================================================================

CONFIG_DIR = Path("config")

class ConfigFile(str, Enum):
    """Поддерживаемые конфигурационные файлы."""
    FEES = "fees"
    COMMISSIONS = "commissions"
    RATES = "rates"
    DUTIES = "duties"


CONFIG_METADATA: dict[ConfigFile, dict[str, Any]] = {
    ConfigFile.FEES: {
        "filename": "fees.yml",
        "description": "Тарифы стран и фрахта",
        "required_keys": ["countries", "freight"],
    },
    ConfigFile.COMMISSIONS: {
        "filename": "commissions.yml",
        "description": "Комиссии (включая bank_commission)",
        "required_keys": ["company_commission", "bank_commission"],
    },
    ConfigFile.RATES: {
        "filename": "rates.yml",
        "description": "Курсы валют и утильсбор",
        "required_keys": ["rates", "utilization"],
    },
    ConfigFile.DUTIES: {
        "filename": "duties.yml",
        "description": "Таблицы пошлин",
        "required_keys": ["petrol", "electric"],
    },
}


# ============================================================================
# FSM STATES
# ============================================================================

class ConfigUploadStates(StatesGroup):
    """Состояния для загрузки конфигурационных файлов."""
    waiting_for_fees = State()
    waiting_for_commissions = State()
    waiting_for_rates = State()
    waiting_for_duties = State()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_config_path(config_type: ConfigFile) -> Path:
    """
    Получить полный путь к конфигурационному файлу.

    Args:
        config_type: Тип конфигурационного файла из enum ConfigFile

    Returns:
        Path: Полный путь к файлу конфигурации

    Example:
        >>> get_config_path(ConfigFile.FEES)
        PosixPath('config/fees.yml')
    """
    filename = CONFIG_METADATA[config_type]["filename"]
    return CONFIG_DIR / filename


def get_backup_path(config_type: ConfigFile) -> Path:
    """
    Создать путь для backup-файла с timestamp.

    Args:
        config_type: Тип конфигурационного файла из enum ConfigFile

    Returns:
        Path: Путь для backup-файла в формате {filename}.backup.YYYYMMDD_HHMMSS

    Example:
        >>> get_backup_path(ConfigFile.FEES)  # doctest: +SKIP
        PosixPath('config/fees.yml.backup.20251228_143022')
    """
    filename = CONFIG_METADATA[config_type]["filename"]
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    return CONFIG_DIR / f"{filename}.backup.{timestamp}"


# ============================================================================
# ROUTER
# ============================================================================

router = Router(name="config_handlers")

# Хэндлеры будут добавлены в следующих спринтах

