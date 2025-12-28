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
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile, Message


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


async def send_config_file(
    message: Message,
    config_type: ConfigFile,
) -> bool:
    """
    Отправить конфигурационный файл администратору.

    Args:
        message: Telegram message объект
        config_type: Тип конфигурационного файла

    Returns:
        True если файл успешно отправлен, False если файл не найден
    """
    file_path = get_config_path(config_type)
    metadata = CONFIG_METADATA[config_type]

    # Проверка существования файла
    if not file_path.exists():
        await message.answer(
            f"❌ **File not found:** `{metadata['filename']}`\n\n"
            f"Config file may have been deleted or moved."
        )
        return False

    # Отправка файла
    document = FSInputFile(file_path, filename=metadata["filename"])
    caption = (
        f"📄 **{metadata['filename']}**\n"
        f"📝 {metadata['description']}\n\n"
        f"📊 Size: {file_path.stat().st_size:,} bytes"
    )

    await message.answer_document(document, caption=caption)
    return True


def format_config_list() -> str:
    """Отформатировать список всех доступных конфигов."""
    lines = ["📁 **Available Configuration Files:**\n"]

    for config_type in ConfigFile:
        metadata = CONFIG_METADATA[config_type]
        file_path = get_config_path(config_type)

        status = "✅" if file_path.exists() else "❌"
        lines.append(
            f"{status} `{metadata['filename']}`\n"
            f"   └─ {metadata['description']}\n"
            f"   └─ Command: `/get_{config_type.value}`\n"
        )

    return "\n".join(lines)


# ============================================================================
# ROUTER
# ============================================================================

router = Router(name="config_handlers")


# ============================================================================
# COMMAND HANDLERS
# ============================================================================

@router.message(Command("list_configs"))
async def cmd_list_configs(message: Message):
    """Показать список всех конфигурационных файлов."""
    config_list = format_config_list()

    await message.answer(
        f"{config_list}\n"
        f"💡 **Tip:** Use `/get_<name>` to download a config file.\n"
        f"📤 Use `/set_<name>` to upload a new version (available in next sprint)."
    )


@router.message(Command("get_fees"))
async def cmd_get_fees(message: Message):
    """Отправить fees.yml администратору."""
    await send_config_file(message, ConfigFile.FEES)


@router.message(Command("get_commissions"))
async def cmd_get_commissions(message: Message):
    """Отправить commissions.yml администратору."""
    await send_config_file(message, ConfigFile.COMMISSIONS)


@router.message(Command("get_rates"))
async def cmd_get_rates(message: Message):
    """Отправить rates.yml администратору."""
    await send_config_file(message, ConfigFile.RATES)


@router.message(Command("get_duties"))
async def cmd_get_duties(message: Message):
    """Отправить duties.yml администратору."""
    await send_config_file(message, ConfigFile.DUTIES)

