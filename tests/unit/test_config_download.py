"""
Тесты для команд скачивания конфигурационных файлов.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.types import Chat, Message, User
import pytest

from app.bot.handlers.config import (
    ConfigFile,
    cmd_get_commissions,
    cmd_get_duties,
    cmd_get_fees,
    cmd_get_rates,
    cmd_list_configs,
    format_config_list,
    send_config_file,
)


# Использовать anyio для async тестов
pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    """Использовать только asyncio backend."""
    return "asyncio"


@pytest.fixture
def mock_message():
    """Мок Telegram Message."""
    message = MagicMock(spec=Message)
    message.answer = AsyncMock()
    message.answer_document = AsyncMock()
    message.from_user = User(id=123456, is_bot=False, first_name="Admin")
    message.chat = Chat(id=123456, type="private")
    return message


async def test_send_config_file_success(mock_message, tmp_path):
    """Тест успешной отправки конфига."""
    # Создать временный файл
    config_file = tmp_path / "fees.yml"
    config_file.write_text("countries:\n  japan: 1000\n")

    with patch("app.bot.handlers.config.get_config_path", return_value=config_file):
        result = await send_config_file(mock_message, ConfigFile.FEES)

    assert result is True
    mock_message.answer_document.assert_called_once()

    # Проверить caption
    call_args = mock_message.answer_document.call_args
    caption = call_args.kwargs["caption"]
    assert "fees.yml" in caption
    assert "Тарифы стран и фрахта" in caption
    assert "bytes" in caption


async def test_send_config_file_not_found(mock_message, tmp_path):
    """Тест отправки несуществующего конфига."""
    non_existent = tmp_path / "missing.yml"

    with patch("app.bot.handlers.config.get_config_path", return_value=non_existent):
        result = await send_config_file(mock_message, ConfigFile.FEES)

    assert result is False
    mock_message.answer.assert_called_once()

    # Проверить сообщение об ошибке
    call_args = mock_message.answer.call_args
    error_msg = call_args.args[0]
    assert "File not found" in error_msg
    assert "fees.yml" in error_msg


async def test_send_config_file_all_types(mock_message, tmp_path):
    """Тест отправки всех типов конфигов."""
    config_types = [
        ConfigFile.FEES,
        ConfigFile.COMMISSIONS,
        ConfigFile.RATES,
        ConfigFile.DUTIES,
    ]

    for config_type in config_types:
        # Создать временный файл
        config_file = tmp_path / f"{config_type.value}.yml"
        config_file.write_text(f"{config_type.value}:\n  test: value\n")

        with patch("app.bot.handlers.config.get_config_path", return_value=config_file):
            result = await send_config_file(mock_message, config_type)

        assert result is True


def test_format_config_list_all_exist(tmp_path):
    """Тест форматирования списка конфигов (все существуют)."""
    with patch("app.bot.handlers.config.get_config_path") as mock_path:
        # Все файлы существуют
        mock_file = MagicMock(spec=Path)
        mock_file.exists.return_value = True
        mock_path.return_value = mock_file

        result = format_config_list()

        # Проверить содержимое
        assert "Available Configuration Files" in result
        assert "/get_fees" in result
        assert "/get_commissions" in result
        assert "/get_rates" in result
        assert "/get_duties" in result

        # Все файлы должны быть отмечены как существующие
        assert result.count("✅") == 4
        assert "❌" not in result


def test_format_config_list_some_missing(tmp_path):
    """Тест форматирования списка конфигов (некоторые отсутствуют)."""
    with patch("app.bot.handlers.config.get_config_path") as mock_path:
        # Только fees и rates существуют
        def mock_exists_side_effect(config_type):
            mock_file = MagicMock(spec=Path)
            mock_file.exists.return_value = config_type in [ConfigFile.FEES, ConfigFile.RATES]
            return mock_file

        mock_path.side_effect = lambda ct: mock_exists_side_effect(ct)

        result = format_config_list()

        # Проверить что есть и существующие и отсутствующие
        assert "✅" in result
        assert "❌" in result


def test_format_config_list_structure():
    """Тест структуры отформатированного списка."""
    with patch("app.bot.handlers.config.get_config_path") as mock_path:
        mock_file = MagicMock(spec=Path)
        mock_file.exists.return_value = True
        mock_path.return_value = mock_file

        result = format_config_list()

        # Проверить что каждый конфиг имеет описание и команду
        assert "fees.yml" in result
        assert "Тарифы стран и фрахта" in result

        assert "commissions.yml" in result
        assert "Комиссии" in result

        assert "rates.yml" in result
        assert "Курсы валют и утильсбор" in result

        assert "duties.yml" in result
        assert "Таблицы пошлин" in result


async def test_cmd_list_configs(mock_message):
    """Тест команды /list_configs."""


    with patch("app.bot.handlers.config.get_config_path") as mock_path:
        mock_file = MagicMock(spec=Path)
        mock_file.exists.return_value = True
        mock_path.return_value = mock_file

        await cmd_list_configs(mock_message)

    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args
    response = call_args.args[0]
    assert "Available Configuration Files" in response
    assert "/get_fees" in response
    assert "Tip" in response


async def test_cmd_get_fees(mock_message, tmp_path):
    """Тест команды /get_fees."""


    config_file = tmp_path / "fees.yml"
    config_file.write_text("countries:\n  japan: 1000\n")

    with patch("app.bot.handlers.config.get_config_path", return_value=config_file):
        await cmd_get_fees(mock_message)

    mock_message.answer_document.assert_called_once()


async def test_cmd_get_commissions(mock_message, tmp_path):
    """Тест команды /get_commissions."""


    config_file = tmp_path / "commissions.yml"
    config_file.write_text("company_commission: 0.05\n")

    with patch("app.bot.handlers.config.get_config_path", return_value=config_file):
        await cmd_get_commissions(mock_message)

    mock_message.answer_document.assert_called_once()


async def test_cmd_get_rates(mock_message, tmp_path):
    """Тест команды /get_rates."""


    config_file = tmp_path / "rates.yml"
    config_file.write_text("rates:\n  usd: 75.0\n")

    with patch("app.bot.handlers.config.get_config_path", return_value=config_file):
        await cmd_get_rates(mock_message)

    mock_message.answer_document.assert_called_once()


async def test_cmd_get_duties(mock_message, tmp_path):
    """Тест команды /get_duties."""


    config_file = tmp_path / "duties.yml"
    config_file.write_text("petrol:\n  - rate: 0.54\n")

    with patch("app.bot.handlers.config.get_config_path", return_value=config_file):
        await cmd_get_duties(mock_message)

    mock_message.answer_document.assert_called_once()


