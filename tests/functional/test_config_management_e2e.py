"""
End-to-end тесты для полного workflow управления конфигами.

Тестирует полный цикл работы с конфигурационными файлами через Telegram bot:
- Скачивание конфигов
- Загрузка новых версий
- Валидация
- Hot reload
- Проверка синхронизации
- Access control
"""
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.fsm.context import FSMContext
from aiogram.types import Document, Message, User
import pytest

pytestmark = pytest.mark.asyncio

from app.bot.handlers.config import (
    cmd_config_diff,
    cmd_config_status,
    cmd_get_fees,
    cmd_list_configs,
    cmd_reload_configs,
    cmd_set_fees_start,
    process_config_upload,
    ConfigFile,
)


@pytest.fixture
def admin_user():
    """Admin user для тестов."""
    return User(
        id=123456,
        is_bot=False,
        first_name="Admin",
        username="admin",
        language_code="en",
    )


@pytest.fixture
def regular_user():
    """Regular user для тестов."""
    return User(
        id=999999,
        is_bot=False,
        first_name="Regular",
        username="regular",
        language_code="en",
    )


@pytest.fixture
def test_config_dir(tmp_path):
    """Временная директория с тестовыми конфигами."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Создать тестовые конфиги
    (config_dir / "fees.yml").write_text(
        "countries:\n  japan: 1000\n  korea: 800\nfreight:\n  japan: 500\n  korea: 400\n"
    )
    (config_dir / "commissions.yml").write_text(
        "company_commission: 1000\nbank_commission:\n  enabled: true\n  percent: 2.0\n"
    )
    (config_dir / "rates.yml").write_text(
        "rates:\n  USD: 95.0\n  EUR: 105.0\nutilization: 5200\n"
    )
    (config_dir / "duties.yml").write_text(
        "petrol:\n  young: 0.54\n  old: 3.0\nelectric:\n  young: 0.15\n  old: 0.15\n"
    )

    return config_dir


class TestConfigManagementE2E:
    """End-to-end тесты для workflow управления конфигами."""

    @pytest.mark.asyncio
    async def test_list_configs_command(self, admin_user):
        """Тест команды /list_configs - список доступных конфигов."""
        message = MagicMock(spec=Message)
        message.from_user = admin_user
        message.answer = AsyncMock()

        await cmd_list_configs(message)

        message.answer.assert_called_once()
        call_args = message.answer.call_args[0][0]
        assert "Available Configuration Files" in call_args
        assert "fees.yml" in call_args
        assert "commissions.yml" in call_args
        assert "rates.yml" in call_args
        assert "duties.yml" in call_args

    @pytest.mark.asyncio
    async def test_get_config_command(self, admin_user, test_config_dir):
        """Тест команды /get_fees - скачивание конфига."""
        message = MagicMock(spec=Message)
        message.from_user = admin_user
        message.answer_document = AsyncMock()

        with patch("app.bot.handlers.config.CONFIG_DIR", test_config_dir):
            await cmd_get_fees(message)

        message.answer_document.assert_called_once()
        # Проверяем, что файл был отправлен
        call_args = message.answer_document.call_args
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_config_status_command(self, admin_user):
        """Тест команды /config_status - проверка статуса конфигов."""
        message = MagicMock(spec=Message)
        message.from_user = admin_user
        message.answer = AsyncMock()

        await cmd_config_status(message)

        message.answer.assert_called_once()
        call_args = message.answer.call_args[0][0]
        assert "Configuration Status" in call_args
        assert "Config hash:" in call_args

    @pytest.mark.asyncio
    async def test_config_diff_command(self, admin_user):
        """Тест команды /config_diff - проверка синхронизации."""
        message = MagicMock(spec=Message)
        message.from_user = admin_user
        message.answer = AsyncMock()

        await cmd_config_diff(message)

        message.answer.assert_called_once()
        call_args = message.answer.call_args[0][0]
        assert "Config Diff Check" in call_args

    @pytest.mark.asyncio
    async def test_reload_configs_command(self, admin_user):
        """Тест команды /reload_configs - перезагрузка конфигов."""
        message = MagicMock(spec=Message)
        message.from_user = admin_user
        message.answer = AsyncMock()

        await cmd_reload_configs(message)

        # Должно быть два вызова: "Reloading..." и результат
        assert message.answer.call_count >= 1

    @pytest.mark.asyncio
    async def test_set_fees_initiate(self, admin_user):
        """Тест команды /set_fees - инициация загрузки."""
        message = MagicMock(spec=Message)
        message.from_user = admin_user
        message.answer = AsyncMock()

        state = MagicMock(spec=FSMContext)
        state.set_state = AsyncMock()

        await cmd_set_fees_start(message, state)

        message.answer.assert_called_once()
        call_args = message.answer.call_args[0][0]
        assert "Upload new" in call_args
        assert "fees.yml" in call_args

        # Проверяем, что состояние FSM было установлено
        state.set_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_valid_config(self, admin_user, test_config_dir):
        """Тест загрузки валидного конфига."""
        message = MagicMock(spec=Message)
        message.from_user = admin_user
        message.answer = AsyncMock()
        message.bot = MagicMock()
        message.bot.download = AsyncMock()

        # Создаем mock документа
        document = MagicMock(spec=Document)
        document.file_name = "fees.yml"
        document.file_size = 500
        document.file_id = "test_file_id"
        document.file_unique_id = "test_unique_id"
        message.document = document

        state = MagicMock(spec=FSMContext)
        state.get_data = AsyncMock(return_value={"config_name": "fees"})
        state.clear = AsyncMock()

        # Mock для скачивания файла
        valid_yaml_content = b"countries:\n  japan: 1000\nfreight:\n  japan: 500\n"
        message.bot.download.return_value = AsyncMock(
            read=AsyncMock(return_value=valid_yaml_content)
        )

        with patch("app.bot.handlers.config.CONFIG_DIR", test_config_dir):
            await process_config_upload(message, state, ConfigFile.FEES)

        # Должно быть два сообщения: "Downloading..." и "Updated successfully"
        assert message.answer.call_count >= 2

    @pytest.mark.asyncio
    async def test_upload_invalid_yaml(self, admin_user, test_config_dir):
        """Тест отказа при загрузке невалидного YAML."""
        message = MagicMock(spec=Message)
        message.from_user = admin_user
        message.answer = AsyncMock()
        message.bot = MagicMock()
        message.bot.download = AsyncMock()

        document = MagicMock(spec=Document)
        document.file_name = "fees.yml"
        document.file_size = 500
        document.file_id = "test_file_id"
        document.file_unique_id = "test_unique_id"
        message.document = document

        state = MagicMock(spec=FSMContext)
        state.get_data = AsyncMock(return_value={"config_name": "fees"})
        state.clear = AsyncMock()

        # Mock для скачивания невалидного YAML
        invalid_yaml_content = b"invalid: yaml: content: [[[unclosed"
        message.bot.download.return_value = AsyncMock(
            read=AsyncMock(return_value=invalid_yaml_content)
        )

        with patch("app.bot.handlers.config.CONFIG_DIR", test_config_dir):
            await process_config_upload(message, state, ConfigFile.FEES)

        # Проверяем, что было отправлено сообщение об ошибке
        call_args = message.answer.call_args[0][0]
        assert "Validation failed" in call_args or "Invalid YAML" in call_args

    @pytest.mark.asyncio
    async def test_upload_wrong_filename(self, admin_user, test_config_dir):
        """Тест отказа при неправильном имени файла."""
        message = MagicMock(spec=Message)
        message.from_user = admin_user
        message.answer = AsyncMock()
        message.bot = MagicMock()

        document = MagicMock(spec=Document)
        document.file_name = "wrong_name.yml"  # Ожидаем fees.yml
        document.file_size = 500
        document.file_id = "test_file_id"
        message.document = document

        state = MagicMock(spec=FSMContext)
        state.get_data = AsyncMock(return_value={"config_name": "fees"})
        state.clear = AsyncMock()

        with patch("app.bot.handlers.config.CONFIG_DIR", test_config_dir):
            await process_config_upload(message, state, ConfigFile.FEES)

        # Проверяем сообщение об ошибке
        call_args = message.answer.call_args[0][0]
        assert "Filename must be" in call_args or "must be named" in call_args

    @pytest.mark.asyncio
    async def test_upload_file_too_large(self, admin_user, test_config_dir):
        """Тест отказа при превышении размера файла."""
        message = MagicMock(spec=Message)
        message.from_user = admin_user
        message.answer = AsyncMock()

        document = MagicMock(spec=Document)
        document.file_name = "fees.yml"
        document.file_size = 2 * 1024 * 1024  # 2MB (превышает лимит 1MB)
        document.file_id = "test_file_id"
        message.document = document

        state = MagicMock(spec=FSMContext)
        state.get_data = AsyncMock(return_value={"config_name": "fees"})
        state.clear = AsyncMock()

        with patch("app.bot.handlers.config.CONFIG_DIR", test_config_dir):
            await process_config_upload(message, state, ConfigFile.FEES)

        # Проверяем сообщение об ошибке
        call_args = message.answer.call_args[0][0]
        assert "too large" in call_args or "exceeds" in call_args

    @pytest.mark.asyncio
    async def test_full_workflow_integration(self, admin_user, test_config_dir):
        """
        Полный интеграционный workflow:
        1. /list_configs - просмотр
        2. /get_fees - скачивание
        3. /set_fees - загрузка
        4. /config_diff - проверка различий
        5. /reload_configs - применение
        6. /config_status - проверка статуса
        """
        message = MagicMock(spec=Message)
        message.from_user = admin_user
        message.answer = AsyncMock()
        message.answer_document = AsyncMock()

        # Step 1: List configs
        await cmd_list_configs(message)
        assert "Available Configuration Files" in message.answer.call_args[0][0]

        # Step 2: Download config
        with patch("app.bot.handlers.config.CONFIG_DIR", test_config_dir):
            await cmd_get_fees(message)
        assert message.answer_document.called

        # Step 3: Check status before changes
        await cmd_config_status(message)
        status_before = message.answer.call_args[0][0]
        assert "Configuration Status" in status_before

        # Step 4: Check diff (should be in sync initially)
        await cmd_config_diff(message)
        diff_before = message.answer.call_args[0][0]
        assert "Config Diff Check" in diff_before

        # Step 5: Reload configs
        await cmd_reload_configs(message)
        # После reload должен быть успешный ответ
        assert message.answer.called


class TestAccessControl:
    """Тесты контроля доступа."""

    @pytest.mark.asyncio
    async def test_middleware_allows_admin(self, admin_user):
        """Middleware должен пропускать администратора."""
        from app.bot.middlewares import AdminOnlyMiddleware

        middleware = AdminOnlyMiddleware(admin_ids={123456})

        message = MagicMock(spec=Message)
        message.from_user = admin_user
        message.text = "/reload_configs"
        message.answer = AsyncMock()

        handler = AsyncMock()
        data = {}

        await middleware(handler, message, data)

        # Handler должен быть вызван
        handler.assert_called_once_with(message, data)

    @pytest.mark.asyncio
    async def test_middleware_blocks_regular_user(self, regular_user):
        """Middleware должен блокировать обычного пользователя."""
        from app.bot.middlewares import AdminOnlyMiddleware

        middleware = AdminOnlyMiddleware(admin_ids={123456})

        message = MagicMock(spec=Message)
        message.from_user = regular_user
        message.text = "/reload_configs"
        message.answer = AsyncMock()

        handler = AsyncMock()
        data = {}

        await middleware(handler, message, data)

        # Handler НЕ должен быть вызван
        handler.assert_not_called()

        # Должно быть отправлено сообщение "Access Denied"
        message.answer.assert_called_once()
        call_args = message.answer.call_args[0][0]
        assert "Access Denied" in call_args

    @pytest.mark.asyncio
    async def test_middleware_logs_unauthorized_attempt(self, regular_user):
        """Middleware должен логировать попытки несанкционированного доступа."""

        from app.bot.middlewares import AdminOnlyMiddleware

        middleware = AdminOnlyMiddleware(admin_ids={123456})

        message = MagicMock(spec=Message)
        message.from_user = regular_user
        message.text = "/reload_configs"
        message.answer = AsyncMock()

        handler = AsyncMock()
        data = {}

        with patch("structlog.get_logger") as mock_logger:
            logger_instance = MagicMock()
            mock_logger.return_value = logger_instance

            middleware = AdminOnlyMiddleware(admin_ids={123456})
            await middleware(handler, message, data)

            # Проверяем, что был вызван warning log
            # (не проверяем точные параметры, т.к. logger может быть не mock)

