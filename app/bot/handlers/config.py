# ruff: noqa: RUF002
"""
Хэндлеры для управления конфигурационными файлами через Telegram.


Поддерживаемые файлы:
- config/fees.yml: Тарифы стран и фрахта
- config/commissions.yml: Комиссии (включая bank_commission)
- config/rates.yml: Курсы валют и утильсбор
- config/duties.yml: Таблицы пошлин

Команды:
- /get_{config}: Скачать файл
- /set_{config}: Загрузить новый файл (с FSM и валидацией)
- /reload_configs: Перезагрузить все конфиги в памяти
- /cancel: Прервать текущую операцию загрузки

Безопасность:
- Доступ только для администраторов (через middleware)
- Валидация YAML перед сохранением (4 уровня)
- Автоматический бэкап старых версий с timestamp
- Ограничение размера файла (1MB)
- Атомарная замена файлов

Changelog:
- 2025-12-28: CONFIG-01 - Создан базовый модуль с FSM states и helper-функциями
- 2025-12-28: CONFIG-02 - Добавлены команды скачивания конфигов
- 2025-12-28: CONFIG-03 - Добавлены команды загрузки с FSM и валидацией
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from enum import Enum
import hashlib
import html
from pathlib import Path
import shutil
from typing import TYPE_CHECKING, Any

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Document, FSInputFile, Message
import yaml

from app.core.settings import _dict_hash, _read_yaml, get_configs, reload_configs


if TYPE_CHECKING:
    from aiogram.fsm.context import FSMContext


# ============================================================================
# CONSTANTS
# ============================================================================

CONFIG_DIR = Path("config")

MAX_CONFIG_SIZE_MB = 1
MAX_CONFIG_SIZE_BYTES = MAX_CONFIG_SIZE_MB * 1024 * 1024

# Locks для предотвращения одновременной загрузки одного и того же конфига
# Каждый тип конфига имеет свой Lock, чтобы разные конфиги можно было загружать параллельно
_CONFIG_LOCKS: dict[ConfigFile, asyncio.Lock] = {}


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
        "required_keys": ["default_commission_usd", "bank_commission"],
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


def _get_config_lock(config_type: ConfigFile) -> asyncio.Lock:
    """
    Получить Lock для конкретного типа конфига (lazy initialization).

    Args:
        config_type: Тип конфигурационного файла

    Returns:
        asyncio.Lock для этого типа конфига

    Note:
        Каждый ConfigFile имеет свой Lock, чтобы можно было загружать
        разные конфиги параллельно, но один и тот же конфиг - только последовательно.
    """
    if config_type not in _CONFIG_LOCKS:
        _CONFIG_LOCKS[config_type] = asyncio.Lock()
    return _CONFIG_LOCKS[config_type]


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
# VALIDATION FUNCTIONS
# ============================================================================


def validate_yaml_structure(data: dict[str, Any], required_keys: list[str]) -> tuple[bool, str]:
    """
    Валидация структуры YAML конфига.

    Args:
        data: Распарсенный YAML
        required_keys: Список обязательных ключей верхнего уровня

    Returns:
        (success: bool, error_message: str)
    """
    if not isinstance(data, dict):
        return False, "Root element must be a dictionary"

    missing_keys = [key for key in required_keys if key not in data]
    if missing_keys:
        return False, f"Missing required keys: {', '.join(missing_keys)}"

    return True, ""


async def download_and_validate_config(  # noqa: PLR0911 - Multiple returns for validation is acceptable
    document: Document,
    bot,
    config_type: ConfigFile,
) -> tuple[bool, str, Path | None]:
    """
    Скачать документ из Telegram, валидировать и вернуть временный путь.

    Args:
        document: Telegram Document объект
        bot: Bot instance
        config_type: Тип конфига

    Returns:
        (success: bool, error_message: str, temp_path: Path | None)
    """
    metadata = CONFIG_METADATA[config_type]
    expected_filename = metadata["filename"]

    # 1. Проверка имени файла
    if document.file_name != expected_filename:
        return False, f"Filename must be `{expected_filename}`, got `{document.file_name}`", None

    # 2. Проверка размера
    if document.file_size > MAX_CONFIG_SIZE_BYTES:
        max_mb = MAX_CONFIG_SIZE_MB
        actual_mb = document.file_size / (1024 * 1024)
        return False, f"File too large: {actual_mb:.2f}MB (max {max_mb}MB)", None

    # 3. Скачивание во временный файл
    temp_path = Path(f"/tmp/{config_type.value}_{document.file_unique_id}.yml")
    try:
        await bot.download(document, destination=temp_path)
    except Exception as e:
        return False, f"Download failed: {e!s}", None

    # 4. Парсинг YAML
    try:
        with temp_path.open(encoding="utf-8") as f:  # noqa: ASYNC230 - Small config files, sync is fine
            config_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        temp_path.unlink(missing_ok=True)
        return False, f"Invalid YAML syntax:\n{e!s}", None
    except Exception as e:
        temp_path.unlink(missing_ok=True)
        return False, f"Failed to read file: {e!s}", None

    # 5. Валидация структуры
    is_valid, error_msg = validate_yaml_structure(config_data, metadata["required_keys"])
    if not is_valid:
        temp_path.unlink(missing_ok=True)
        return False, f"Validation failed: {error_msg}", None

    return True, "", temp_path


def backup_config_file(config_type: ConfigFile) -> Path | None:
    """
    Создать бэкап конфигурационного файла.

    Returns:
        Path к backup-файлу или None если оригинала не существует
    """
    source_path = get_config_path(config_type)
    if not source_path.exists():
        return None

    backup_path = get_backup_path(config_type)
    shutil.copy2(source_path, backup_path)
    return backup_path


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

    # Escape HTML special characters to prevent parsing errors
    # <name> would be interpreted as an HTML tag without escaping
    tip_text = html.escape("/get_<name>")
    set_text = html.escape("/set_<name>")

    await message.answer(
        f"{config_list}\n"
        f"💡 <b>Tip:</b> Use <code>{tip_text}</code> to download a config file.\n"
        f"📤 Use <code>{set_text}</code> to upload a new version."
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


# ============================================================================
# COMMAND HANDLERS - UPLOAD START
# ============================================================================


@router.message(Command("set_fees"))
async def cmd_set_fees_start(message: Message, state: FSMContext):
    """Начать загрузку нового fees.yml."""
    await state.set_state(ConfigUploadStates.waiting_for_fees)
    await message.answer(
        "📤 **Upload new fees.yml**\n\n"
        f"⚠️ File will be validated before saving.\n"
        f"📏 Max size: {MAX_CONFIG_SIZE_MB}MB\n\n"
        "Send the file or use /cancel to abort."
    )


@router.message(Command("set_commissions"))
async def cmd_set_commissions_start(message: Message, state: FSMContext):
    """Начать загрузку нового commissions.yml."""
    await state.set_state(ConfigUploadStates.waiting_for_commissions)
    await message.answer(
        "📤 **Upload new commissions.yml**\n\n"
        f"⚠️ File will be validated before saving.\n"
        f"📏 Max size: {MAX_CONFIG_SIZE_MB}MB\n\n"
        "Send the file or use /cancel to abort."
    )


@router.message(Command("set_rates"))
async def cmd_set_rates_start(message: Message, state: FSMContext):
    """Начать загрузку нового rates.yml."""
    await state.set_state(ConfigUploadStates.waiting_for_rates)
    await message.answer(
        "📤 **Upload new rates.yml**\n\n"
        f"⚠️ File will be validated before saving.\n"
        f"📏 Max size: {MAX_CONFIG_SIZE_MB}MB\n\n"
        "Send the file or use /cancel to abort."
    )


@router.message(Command("set_duties"))
async def cmd_set_duties_start(message: Message, state: FSMContext):
    """Начать загрузку нового duties.yml."""
    await state.set_state(ConfigUploadStates.waiting_for_duties)
    await message.answer(
        "📤 **Upload new duties.yml**\n\n"
        f"⚠️ File will be validated before saving.\n"
        f"📏 Max size: {MAX_CONFIG_SIZE_MB}MB\n\n"
        "Send the file or use /cancel to abort."
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Отменить текущую операцию загрузки."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("❌ No active operation to cancel.")
        return

    await state.clear()
    await message.answer("✅ Operation cancelled.")


# ============================================================================
# DOCUMENT HANDLERS - UPLOAD PROCESSING
# ============================================================================


async def process_config_upload(
    message: Message,
    state: FSMContext,
    config_type: ConfigFile,
):
    """
    Обработать загрузку конфигурационного файла (generic handler).

    Workflow:
    1. Download and validate file (без lock - может идти параллельно)
    2. Acquire lock для данного config_type
    3. Backup old config (под lock)
    4. Replace with new config (под lock)
    5. Release lock
    6. Clear FSM state

    Race Condition Protection:
    - Использует asyncio.Lock для каждого типа конфига
    - Разные конфиги можно загружать параллельно
    - Один и тот же конфиг загружается последовательно
    - Предотвращает потерю данных при одновременной загрузке
    """
    document = message.document
    if not document:
        await message.answer("❌ Please send a document file.")
        return

    metadata = CONFIG_METADATA[config_type]

    # 1. Скачивание и валидация (БЕЗ LOCK - может идти параллельно для экономии времени)
    await message.answer("⏳ Downloading and validating...")

    success, error_msg, temp_path = await download_and_validate_config(
        document, message.bot, config_type
    )

    if not success:
        await message.answer(f"❌ **Validation failed:**\n\n{error_msg}")
        await state.clear()
        return

    # 2-4. Получаем lock перед модификацией файловой системы
    lock = _get_config_lock(config_type)

    async with lock:
        await message.answer("🔒 Acquiring lock and saving...")

        # 2. Бэкап старого файла
        backup_path = backup_config_file(config_type)
        backup_info = ""
        if backup_path:
            backup_info = f"📦 Backup: `{backup_path.name}`\n"

        # 3. Замена файла
        target_path = get_config_path(config_type)
        try:
            shutil.move(str(temp_path), str(target_path))
        except Exception as e:
            temp_path.unlink(missing_ok=True)
            await message.answer(f"❌ **Failed to save config:**\n\n{e!s}")
            await state.clear()
            return

    # Lock released - файл успешно сохранен

    # 5. Успех
    await message.answer(
        f"✅ **{metadata['filename']} updated successfully!**\n\n"
        f"{backup_info}"
        f"⚠️ Use /reload_configs to apply changes in runtime."
    )
    await state.clear()


@router.message(ConfigUploadStates.waiting_for_fees)
async def handle_fees_upload(message: Message, state: FSMContext):
    """Обработать загруженный fees.yml."""
    await process_config_upload(message, state, ConfigFile.FEES)


@router.message(ConfigUploadStates.waiting_for_commissions)
async def handle_commissions_upload(message: Message, state: FSMContext):
    """Обработать загруженный commissions.yml."""
    await process_config_upload(message, state, ConfigFile.COMMISSIONS)


@router.message(ConfigUploadStates.waiting_for_rates)
async def handle_rates_upload(message: Message, state: FSMContext):
    """Обработать загруженный rates.yml."""
    await process_config_upload(message, state, ConfigFile.RATES)


@router.message(ConfigUploadStates.waiting_for_duties)
async def handle_duties_upload(message: Message, state: FSMContext):
    """Обработать загруженный duties.yml."""
    await process_config_upload(message, state, ConfigFile.DUTIES)


# ============================================================================
# WHOAMI COMMAND
# ============================================================================


@router.message(Command("whoami"))
async def cmd_whoami(message: Message):
    """
    Показать информацию о текущем пользователе.

    Полезно для получения своего user ID для добавления в ADMIN_USER_IDS.
    """
    user = message.from_user

    if not user:
        await message.answer("❌ Unable to identify user")
        return

    info = [
        "👤 **Your Telegram Profile:**\n",
        f"🆔 User ID: `{user.id}`",
        f"👤 Username: @{user.username}" if user.username else "👤 Username: (not set)",
        f"📛 First Name: {user.first_name}",
    ]

    if user.last_name:
        info.append(f"📛 Last Name: {user.last_name}")

    info.append(f"🤖 Is Bot: {'Yes' if user.is_bot else 'No'}")
    info.append(f"💬 Language: {user.language_code or 'unknown'}")

    info.append("\n💡 **Tip:** Share your User ID with the admin to get access.")

    await message.answer("\n".join(info))


# ============================================================================
# CONFIG MANAGEMENT COMMANDS
# ============================================================================


@router.message(Command("reload_configs"))
async def cmd_reload_configs(message: Message):
    """
    Перезагрузить все конфигурационные файлы в памяти.

    Очищает кэш ConfigRegistry и принудительно загружает конфиги из файлов.
    Валидирует загруженные конфиги и обновляет hash/timestamp.
    """
    await message.answer("⏳ **Reloading configs...**")



    success, msg, metrics = reload_configs()

    await message.answer(msg)

    if success and metrics.get("hash_changed"):
        await message.answer(
            "💡 **Tip:** All API endpoints will use the new configs immediately.\n"
            "No server restart required!"
        )


@router.message(Command("config_status"))
async def cmd_config_status(message: Message):
    """
    Показать текущий статус конфигурационных файлов.

    Отображает:
    - Config hash (версия)
    - Время загрузки
    - Список файлов и их размеры
    """


    try:
        configs = get_configs()

        # Информация о файлах
        config_files = []
        total_size = 0

        for config_type in ConfigFile:
            file_path = get_config_path(config_type)
            metadata = CONFIG_METADATA[config_type]

            if file_path.exists():
                size = file_path.stat().st_size
                total_size += size
                status = "✅"
                size_str = f"{size:,} bytes"
            else:
                status = "❌"
                size_str = "N/A"

            config_files.append(f"{status} `{metadata['filename']}` - {size_str}")

        files_list = "\n".join(config_files)

        message_text = (
            "📊 **Configuration Status**\n\n"
            f"🔑 Config hash: `{configs.hash}`\n"
            f"📅 Loaded at: `{configs.loaded_at}`\n"
            f"📦 Total size: `{total_size:,} bytes`\n\n"
            f"**Files:**\n{files_list}\n\n"
            "💡 Use /reload_configs to reload from disk."
        )

        await message.answer(message_text)

    except Exception as e:
        await message.answer(
            f"❌ **Failed to get config status:**\n\n"
            f"`{type(e).__name__}: {e!s}`"
        )


@router.message(Command("config_diff"))
async def cmd_config_diff(message: Message):
    """
    Показать различия между конфигами на диске и в памяти.

    Полезно после загрузки нового файла, чтобы проверить,
    нужен ли reload.
    """
    try:
        # Текущий hash в памяти
        memory_configs = get_configs()
        memory_hash = memory_configs.hash

        # Вычислить hash файлов на диске
        disk_hashes = {}
        for config_type in ConfigFile:
            file_path = get_config_path(config_type)
            if file_path.exists():
                content = file_path.read_bytes()
                file_hash = hashlib.sha256(content).hexdigest()[:8]
                disk_hashes[config_type.value] = file_hash

        # Объединить в общий hash (используем тот же метод что и _dict_hash)
        disk_aggregate = {
            "fees": _read_yaml("fees.yml"),
            "commissions": _read_yaml("commissions.yml"),
            "rates": _read_yaml("rates.yml"),
            "duties": _read_yaml("duties.yml"),
        }

        disk_hash = _dict_hash(disk_aggregate)

        files_info = []
        for config_type in ConfigFile:
            metadata = CONFIG_METADATA[config_type]
            if config_type.value in disk_hashes:
                files_info.append(
                    f"📄 `{metadata['filename']}`: `{disk_hashes[config_type.value]}`"
                )

        files_list = "\n".join(files_info)

        if memory_hash == disk_hash:
            status = "✅ **Up to date** - Memory and disk are synchronized"
        else:
            status = "⚠️ **Out of sync** - Use /reload_configs to apply disk changes"

        message_text = (
            "🔄 **Config Diff Check**\n\n"
            f"💾 Memory hash: `{memory_hash}`\n"
            f"💿 Disk hash: `{disk_hash}`\n\n"
            f"{status}\n\n"
            f"**Disk files:**\n{files_list}"
        )

        await message.answer(message_text)

    except Exception as e:
        await message.answer(
            f"❌ **Failed to check diff:**\n\n"
            f"`{type(e).__name__}: {e!s}`"
        )


