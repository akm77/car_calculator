"""
Тесты для команд загрузки конфигурационных файлов.

Тестируемые компоненты:
- validate_yaml_structure()
- download_and_validate_config()
- backup_config_file()
- Command handlers: cmd_set_*_start
- Document handlers: handle_*_upload
- cmd_cancel

Changelog:
- 2025-12-28: CONFIG-03 - Созданы тесты для загрузки конфигов с FSM
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.bot.handlers.config import (
    _CONFIG_LOCKS,
    ConfigFile,
    ConfigUploadStates,
    _get_config_lock,
    backup_config_file,
    cmd_cancel,
    cmd_set_commissions_start,
    cmd_set_duties_start,
    cmd_set_fees_start,
    cmd_set_rates_start,
    download_and_validate_config,
    handle_fees_upload,
    validate_yaml_structure,
)


# Использовать anyio для async тестов
pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    """Использовать только asyncio backend."""
    return "asyncio"


# ============================================================================
# TESTS: validate_yaml_structure
# ============================================================================


class TestValidateYamlStructure:
    """Тесты для функции validate_yaml_structure()."""

    def test_success_all_keys_present(self):
        """Тест успешной валидации с всеми ключами."""
        data = {"countries": {}, "freight": {}}
        is_valid, error = validate_yaml_structure(data, ["countries", "freight"])

        assert is_valid is True
        assert error == ""

    def test_success_extra_keys_allowed(self):
        """Тест успешной валидации с дополнительными ключами."""
        data = {"countries": {}, "freight": {}, "extra_key": "value"}
        is_valid, error = validate_yaml_structure(data, ["countries", "freight"])

        assert is_valid is True
        assert error == ""

    def test_missing_single_key(self):
        """Тест валидации с отсутствующим ключом."""
        data = {"countries": {}}
        is_valid, error = validate_yaml_structure(data, ["countries", "freight"])

        assert is_valid is False
        assert "Missing required keys" in error
        assert "freight" in error

    def test_missing_multiple_keys(self):
        """Тест валидации с несколькими отсутствующими ключами."""
        data = {"extra": {}}
        is_valid, error = validate_yaml_structure(data, ["countries", "freight"])

        assert is_valid is False
        assert "Missing required keys" in error
        assert "countries" in error
        assert "freight" in error

    def test_not_dict_but_list(self):
        """Тест валидации списка вместо словаря."""
        data = ["list", "of", "items"]
        is_valid, error = validate_yaml_structure(data, ["key"])

        assert is_valid is False
        assert "must be a dictionary" in error

    def test_not_dict_but_string(self):
        """Тест валидации строки вместо словаря."""
        data = "just a string"
        is_valid, error = validate_yaml_structure(data, ["key"])

        assert is_valid is False
        assert "must be a dictionary" in error

    def test_empty_dict_no_required_keys(self):
        """Тест пустого словаря без обязательных ключей."""
        data = {}
        is_valid, error = validate_yaml_structure(data, [])

        assert is_valid is True
        assert error == ""

    def test_empty_dict_with_required_keys(self):
        """Тест пустого словаря с обязательными ключами."""
        data = {}
        is_valid, error = validate_yaml_structure(data, ["required_key"])

        assert is_valid is False
        assert "Missing required keys" in error


# ============================================================================
# TESTS: backup_config_file
# ============================================================================


class TestBackupConfigFile:
    """Тесты для функции backup_config_file()."""

    def test_backup_existing_file(self, tmp_path):
        """Тест создания бэкапа существующего файла."""
        config_file = tmp_path / "fees.yml"
        config_file.write_text("test: data\n")

        with (
            patch("app.bot.handlers.config.get_config_path", return_value=config_file),
            patch("app.bot.handlers.config.get_backup_path") as mock_backup,
        ):
            backup_path = tmp_path / "fees.yml.backup.20251228_120000"
            mock_backup.return_value = backup_path

            result = backup_config_file(ConfigFile.FEES)

            assert result == backup_path
            assert backup_path.exists()
            assert backup_path.read_text() == "test: data\n"

    def test_backup_nonexistent_file(self, tmp_path):
        """Тест попытки бэкапа несуществующего файла."""
        config_file = tmp_path / "nonexistent.yml"

        with patch("app.bot.handlers.config.get_config_path", return_value=config_file):
            result = backup_config_file(ConfigFile.FEES)

            assert result is None

    def test_backup_preserves_permissions(self, tmp_path):
        """Тест сохранения метаданных файла при бэкапе."""
        config_file = tmp_path / "rates.yml"
        config_file.write_text("rates: {}\n")
        original_stat = config_file.stat()

        with (
            patch("app.bot.handlers.config.get_config_path", return_value=config_file),
            patch("app.bot.handlers.config.get_backup_path") as mock_backup,
        ):
            backup_path = tmp_path / "rates.yml.backup.20251228_120000"
            mock_backup.return_value = backup_path

            result = backup_config_file(ConfigFile.RATES)

            assert result is not None
            backup_stat = backup_path.stat()
            # shutil.copy2 preserves modification time
            assert backup_stat.st_mtime == original_stat.st_mtime


# ============================================================================
# TESTS: Command Handlers - Upload Start
# ============================================================================


class TestUploadStartCommands:
    """Тесты для команд начала загрузки /set_*."""

    async def test_cmd_set_fees_start(self):
        """Тест начала загрузки fees.yml."""
        message = MagicMock()
        message.answer = AsyncMock()
        state = MagicMock()
        state.set_state = AsyncMock()

        await cmd_set_fees_start(message, state)

        state.set_state.assert_called_once_with(ConfigUploadStates.waiting_for_fees)
        message.answer.assert_called_once()
        call_text = message.answer.call_args[0][0]
        assert "Upload new fees.yml" in call_text
        assert "1MB" in call_text
        assert "/cancel" in call_text

    async def test_cmd_set_commissions_start(self):
        """Тест начала загрузки commissions.yml."""
        message = MagicMock()
        message.answer = AsyncMock()
        state = MagicMock()
        state.set_state = AsyncMock()

        await cmd_set_commissions_start(message, state)

        state.set_state.assert_called_once_with(ConfigUploadStates.waiting_for_commissions)
        message.answer.assert_called_once()
        call_text = message.answer.call_args[0][0]
        assert "Upload new commissions.yml" in call_text

    async def test_cmd_set_rates_start(self):
        """Тест начала загрузки rates.yml."""
        message = MagicMock()
        message.answer = AsyncMock()
        state = MagicMock()
        state.set_state = AsyncMock()

        await cmd_set_rates_start(message, state)

        state.set_state.assert_called_once_with(ConfigUploadStates.waiting_for_rates)
        message.answer.assert_called_once()
        call_text = message.answer.call_args[0][0]
        assert "Upload new rates.yml" in call_text

    async def test_cmd_set_duties_start(self):
        """Тест начала загрузки duties.yml."""
        message = MagicMock()
        message.answer = AsyncMock()
        state = MagicMock()
        state.set_state = AsyncMock()

        await cmd_set_duties_start(message, state)

        state.set_state.assert_called_once_with(ConfigUploadStates.waiting_for_duties)
        message.answer.assert_called_once()
        call_text = message.answer.call_args[0][0]
        assert "Upload new duties.yml" in call_text


# ============================================================================
# TESTS: Cancel Command
# ============================================================================


class TestCancelCommand:
    """Тесты для команды /cancel."""

    async def test_cancel_with_active_state(self):
        """Тест отмены при активном FSM state."""
        message = MagicMock()
        message.answer = AsyncMock()
        state = MagicMock()
        state.get_state = AsyncMock(return_value="some_state")
        state.clear = AsyncMock()

        await cmd_cancel(message, state)

        state.clear.assert_called_once()
        message.answer.assert_called_once()
        call_text = message.answer.call_args[0][0]
        assert "cancelled" in call_text.lower()

    async def test_cancel_without_active_state(self):
        """Тест отмены без активного FSM state."""
        message = MagicMock()
        message.answer = AsyncMock()
        state = MagicMock()
        state.get_state = AsyncMock(return_value=None)
        state.clear = AsyncMock()

        await cmd_cancel(message, state)

        state.clear.assert_not_called()
        message.answer.assert_called_once()
        call_text = message.answer.call_args[0][0]
        assert "No active operation" in call_text


# ============================================================================
# TESTS: Download and Validate
# ============================================================================


class TestDownloadAndValidate:
    """Тесты для функции download_and_validate_config()."""

    async def test_wrong_filename(self):
        """Тест загрузки файла с неправильным именем."""
        document = MagicMock()
        document.file_name = "wrong_name.yml"
        document.file_size = 1024
        bot = MagicMock()

        success, error, path = await download_and_validate_config(document, bot, ConfigFile.FEES)

        assert success is False
        assert "Filename must be" in error
        assert "fees.yml" in error
        assert path is None

    async def test_file_too_large(self):
        """Тест загрузки слишком большого файла."""
        document = MagicMock()
        document.file_name = "fees.yml"
        document.file_size = 2 * 1024 * 1024  # 2MB > 1MB limit
        bot = MagicMock()

        success, error, path = await download_and_validate_config(document, bot, ConfigFile.FEES)

        assert success is False
        assert "too large" in error
        assert "2.00MB" in error
        assert path is None

    async def test_download_failure(self, tmp_path):
        """Тест ошибки при скачивании файла."""
        document = MagicMock()
        document.file_name = "fees.yml"
        document.file_size = 1024
        document.file_unique_id = "test123"

        bot = MagicMock()
        bot.download = AsyncMock(side_effect=Exception("Network error"))

        success, error, path = await download_and_validate_config(document, bot, ConfigFile.FEES)

        assert success is False
        assert "Download failed" in error
        assert path is None

    async def test_invalid_yaml_syntax(self, tmp_path):
        """Тест загрузки файла с невалидным YAML."""
        document = MagicMock()
        document.file_name = "fees.yml"
        document.file_size = 1024
        document.file_unique_id = "test123"

        invalid_yaml = tmp_path / "invalid.yml"
        invalid_yaml.write_text("invalid: yaml: syntax: [[[")

        bot = MagicMock()

        async def mock_download(doc, destination):
            destination.write_text("invalid: yaml: syntax: [[[")

        bot.download = AsyncMock(side_effect=mock_download)

        with patch("app.bot.handlers.config.Path") as mock_path_cls:
            mock_temp_path = MagicMock()
            mock_temp_path.open = invalid_yaml.open
            mock_temp_path.unlink = MagicMock()
            mock_path_cls.return_value = mock_temp_path

            success, error, path = await download_and_validate_config(
                document, bot, ConfigFile.FEES
            )

        assert success is False
        assert "Invalid YAML syntax" in error

    async def test_missing_required_keys(self, tmp_path):
        """Тест загрузки файла без обязательных ключей."""
        document = MagicMock()
        document.file_name = "fees.yml"
        document.file_size = 1024
        document.file_unique_id = "test123"

        valid_yaml = tmp_path / "valid.yml"
        valid_yaml.write_text("only_one_key: {}\n")

        bot = MagicMock()

        async def mock_download(doc, destination):
            destination.write_text("only_one_key: {}\n")

        bot.download = AsyncMock(side_effect=mock_download)

        with patch("app.bot.handlers.config.Path") as mock_path_cls:
            mock_temp_path = MagicMock()
            mock_temp_path.open = valid_yaml.open
            mock_temp_path.unlink = MagicMock()
            mock_path_cls.return_value = mock_temp_path

            success, error, path = await download_and_validate_config(
                document, bot, ConfigFile.FEES
            )

        assert success is False
        assert "Validation failed" in error
        assert "Missing required keys" in error


# ============================================================================
# TESTS: Document Upload Handlers
# ============================================================================


class TestDocumentUploadHandlers:
    """Тесты для обработчиков загрузки документов."""

    async def test_handle_fees_upload_success(self, tmp_path):
        """Тест успешной загрузки fees.yml."""
        valid_yaml_content = "countries: {}\nfreight: {}\n"
        temp_file = tmp_path / "fees_test.yml"
        temp_file.write_text(valid_yaml_content)

        document = MagicMock()
        document.file_name = "fees.yml"
        document.file_size = len(valid_yaml_content)
        document.file_unique_id = "test123"

        message = MagicMock()
        message.document = document
        message.answer = AsyncMock()
        message.bot = MagicMock()

        async def mock_download(doc, destination):
            destination.write_text(valid_yaml_content)

        message.bot.download = AsyncMock(side_effect=mock_download)

        state = MagicMock()
        state.clear = AsyncMock()

        config_path = tmp_path / "fees.yml"
        backup_path = tmp_path / "fees.yml.backup.20251228_120000"

        with (
            patch("app.bot.handlers.config.get_config_path", return_value=config_path),
            patch("app.bot.handlers.config.backup_config_file", return_value=backup_path),
            patch("app.bot.handlers.config.Path") as mock_path_cls,
            patch("app.bot.handlers.config.shutil.move"),
        ):
            mock_temp_path = MagicMock()
            mock_temp_path.open = temp_file.open
            mock_temp_path.unlink = MagicMock()
            mock_path_cls.return_value = mock_temp_path

            await handle_fees_upload(message, state)

        state.clear.assert_called_once()
        assert message.answer.call_count >= 2  # Multiple status messages
        # Find success message
        success_found = any(
            "updated successfully" in str(call[0][0]) for call in message.answer.call_args_list
        )
        assert success_found

    async def test_handle_upload_no_document(self):
        """Тест обработки сообщения без документа."""
        message = MagicMock()
        message.document = None
        message.answer = AsyncMock()

        state = MagicMock()
        state.clear = AsyncMock()

        await handle_fees_upload(message, state)

        message.answer.assert_called_once()
        call_text = message.answer.call_args[0][0]
        assert "Please send a document" in call_text
        state.clear.assert_not_called()


# ============================================================================
# TESTS: Concurrency Protection
# ============================================================================


class TestConcurrencyProtection:
    """Тесты для защиты от race condition при одновременной загрузке."""

    async def test_get_config_lock_creates_lock(self):
        """Тест создания Lock при первом обращении."""

        # Очищаем кэш (если есть)
        if ConfigFile.FEES in _CONFIG_LOCKS:
            del _CONFIG_LOCKS[ConfigFile.FEES]

        lock = _get_config_lock(ConfigFile.FEES)

        assert lock is not None
        assert isinstance(lock, __import__("asyncio").Lock)
        assert ConfigFile.FEES in _CONFIG_LOCKS

    async def test_get_config_lock_returns_same_lock(self):
        """Тест, что для одного конфига всегда возвращается один и тот же Lock."""

        lock1 = _get_config_lock(ConfigFile.FEES)
        lock2 = _get_config_lock(ConfigFile.FEES)

        assert lock1 is lock2

    async def test_different_configs_have_different_locks(self):
        """Тест, что разные конфиги имеют разные Locks."""

        lock_fees = _get_config_lock(ConfigFile.FEES)
        lock_rates = _get_config_lock(ConfigFile.RATES)

        assert lock_fees is not lock_rates

    async def test_concurrent_same_config_serialized(self, tmp_path):
        """Тест, что одновременные загрузки одного конфига идут последовательно."""

        lock = _get_config_lock(ConfigFile.FEES)
        call_order = []

        async def mock_upload(upload_id):
            async with lock:
                call_order.append(f"{upload_id}_start")
                await asyncio.sleep(0.05)  # Simulate work under lock
                call_order.append(f"{upload_id}_end")

        # Запускаем две загрузки одновременно
        await asyncio.gather(
            mock_upload("upload1"),
            mock_upload("upload2"),
        )

        # Проверяем, что операции не перемежались
        # Либо upload1 полностью завершился до upload2, либо наоборот
        valid_orders = {
            ("upload1_start", "upload1_end", "upload2_start", "upload2_end"),
            ("upload2_start", "upload2_end", "upload1_start", "upload1_end"),
        }
        assert tuple(call_order) in valid_orders

    async def test_concurrent_different_configs_parallel(self, tmp_path):
        """Тест, что загрузки разных конфигов идут параллельно."""

        lock_fees = _get_config_lock(ConfigFile.FEES)
        lock_rates = _get_config_lock(ConfigFile.RATES)
        call_order = []

        async def mock_upload(config_name, lock):
            async with lock:
                call_order.append(f"{config_name}_start")
                await asyncio.sleep(0.05)
                call_order.append(f"{config_name}_end")

        # Запускаем загрузки разных конфигов одновременно
        await asyncio.gather(
            mock_upload("fees", lock_fees),
            mock_upload("rates", lock_rates),
        )

        # Проверяем, что операции перемежались (т.е. шли параллельно)
        fees_start = call_order.index("fees_start")
        fees_end = call_order.index("fees_end")
        rates_start = call_order.index("rates_start")
        rates_end = call_order.index("rates_end")

        # Если операции параллельны, то одна началась до завершения другой
        parallel = fees_start < rates_end and rates_start < fees_end
        assert parallel, f"Operations should be parallel, got order: {call_order}"
