"""
Тесты для hot reload конфигурационных файлов.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.types import Message
import pytest

from app.bot.handlers.config import cmd_config_diff, cmd_config_status, cmd_reload_configs
from app.core.settings import ConfigRegistry, get_configs, reload_configs


if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def anyio_backend():
    """Restrict to asyncio backend only (no trio)."""
    return "asyncio"


def test_reload_configs_success():
    """Тест успешной перезагрузки конфигов."""
    # Очистить кэш перед тестом
    get_configs.cache_clear()  # type: ignore[attr-defined]

    success, message, metrics = reload_configs()

    assert success is True
    assert "reloaded successfully" in message
    assert "new_hash" in metrics
    assert "load_time_ms" in metrics
    assert metrics["config_count"] == 4


def test_reload_configs_with_hash_change(tmp_path: Path):
    """Тест reload с изменением hash."""
    # Mock config files
    with (
        patch("app.core.settings.CONFIG_DIR", tmp_path),
        patch("app.core.settings._read_yaml") as mock_read,
    ):
        # Первая загрузка
        get_configs.cache_clear()  # type: ignore[attr-defined]
        mock_read.return_value = {"test": "data1"}

        success1, msg1, metrics1 = reload_configs()
        old_hash = metrics1["new_hash"]

        # Изменить данные
        mock_read.return_value = {"test": "data2"}

        # Вторая загрузка
        success2, msg2, metrics2 = reload_configs()

        assert success2 is True
        assert metrics2["old_hash"] == old_hash
        assert metrics2["new_hash"] != old_hash
        assert metrics2["hash_changed"] is True


def test_reload_configs_failure():
    """Тест reload с ошибкой валидации."""
    # Очистить кэш
    get_configs.cache_clear()  # type: ignore[attr-defined]

    with patch("app.core.settings.ConfigRegistry.load") as mock_load:
        # Первая загрузка успешна (чтобы было old_hash)

        mock_load.return_value = ConfigRegistry(
            fees={},
            commissions={},
            rates={},
            duties={},
            hash="old_hash",
            loaded_at="2025-01-01T00:00:00",
        )
        get_configs()

        # При reload вызовет исключение
        mock_load.side_effect = ValueError("Invalid YAML structure")

        success, message, metrics = reload_configs()

        assert success is False
        assert "failed" in message.lower()
        assert "error" in metrics


def test_reload_configs_no_old_configs():
    """Тест reload когда старых конфигов нет в кэше."""
    get_configs.cache_clear()  # type: ignore[attr-defined]

    # Первый раз загрузка не проходила
    with patch("app.core.settings.ConfigRegistry.load") as mock_load:
        # При первом get_configs() - ошибка
        mock_load.side_effect = ValueError("No config files")

        success, message, metrics = reload_configs()

        assert success is False
        assert "failed" in message.lower()
        assert metrics.get("error")


@pytest.mark.anyio
async def test_cmd_reload_configs():
    """Тест команды /reload_configs."""

    message = MagicMock(spec=Message)
    message.answer = AsyncMock()

    await cmd_reload_configs(message)

    # Должны быть отправлены сообщения
    assert message.answer.call_count >= 2  # "Reloading..." + result


@pytest.mark.anyio
async def test_cmd_reload_configs_with_hash_change():
    """Тест команды /reload_configs с изменением hash."""

    message = MagicMock(spec=Message)
    message.answer = AsyncMock()

    with patch("app.core.settings.reload_configs") as mock_reload:
        mock_reload.return_value = (
            True,
            "Success message",
            {"hash_changed": True, "new_hash": "abc123"},
        )

        await cmd_reload_configs(message)

        # Должны быть отправлены 3 сообщения: "Reloading...", success, tip
        assert message.answer.call_count == 3


@pytest.mark.anyio
async def test_cmd_config_status():
    """Тест команды /config_status."""

    message = MagicMock(spec=Message)
    message.answer = AsyncMock()

    await cmd_config_status(message)

    # Должно быть отправлено сообщение со статусом
    message.answer.assert_called_once()
    call_args = message.answer.call_args[0][0]
    assert "Configuration Status" in call_args
    assert "Config hash" in call_args


@pytest.mark.anyio
async def test_cmd_config_status_error():
    """Тест команды /config_status с ошибкой."""

    message = MagicMock(spec=Message)
    message.answer = AsyncMock()

    with patch("app.core.settings.get_configs") as mock_get:
        mock_get.side_effect = ValueError("Config error")

        await cmd_config_status(message)

        message.answer.assert_called_once()
        call_args = message.answer.call_args[0][0]
        assert "Failed to get config status" in call_args
        assert "ValueError" in call_args


@pytest.mark.anyio
async def test_cmd_config_diff():
    """Тест команды /config_diff."""

    message = MagicMock(spec=Message)
    message.answer = AsyncMock()

    await cmd_config_diff(message)

    # Должно быть отправлено сообщение с diff
    message.answer.assert_called_once()
    call_args = message.answer.call_args[0][0]
    assert "Config Diff Check" in call_args
    assert "Memory hash" in call_args
    assert "Disk hash" in call_args


@pytest.mark.anyio
async def test_cmd_config_diff_synchronized():
    """Тест команды /config_diff когда память и диск синхронизированы."""

    message = MagicMock(spec=Message)
    message.answer = AsyncMock()

    # Убедимся что hash одинаковый
    with patch("app.core.settings.get_configs") as mock_get:
        mock_get.return_value = ConfigRegistry(
            fees={},
            commissions={},
            rates={},
            duties={},
            hash="test_hash",
            loaded_at="2025-01-01T00:00:00",
        )

        with patch("app.core.settings._dict_hash") as mock_hash:
            mock_hash.return_value = "test_hash"  # Тот же hash

            await cmd_config_diff(message)

            call_args = message.answer.call_args[0][0]
            assert "Up to date" in call_args


@pytest.mark.anyio
async def test_cmd_config_diff_out_of_sync():
    """Тест команды /config_diff когда память и диск не синхронизированы."""

    message = MagicMock(spec=Message)
    message.answer = AsyncMock()

    # Hash разный - патчим в модуле handlers.config
    with patch("app.bot.handlers.config.get_configs") as mock_get:
        mock_get.return_value = ConfigRegistry(
            fees={},
            commissions={},
            rates={},
            duties={},
            hash="memory_hash",
            loaded_at="2025-01-01T00:00:00",
        )

        with patch("app.bot.handlers.config._dict_hash") as mock_hash:
            mock_hash.return_value = "disk_hash"  # Другой hash

            await cmd_config_diff(message)

            call_args = message.answer.call_args[0][0]
            assert "Out of sync" in call_args


@pytest.mark.anyio
async def test_cmd_config_diff_error():
    """Тест команды /config_diff с ошибкой."""

    message = MagicMock(spec=Message)
    message.answer = AsyncMock()

    # Патчим в модуле handlers.config
    with patch("app.bot.handlers.config.get_configs") as mock_get:
        mock_get.side_effect = ValueError("Config error")

        await cmd_config_diff(message)

        message.answer.assert_called_once()
        call_args = message.answer.call_args[0][0]
        assert "Failed to check diff" in call_args
        assert "ValueError" in call_args


def test_reload_metrics_structure():
    """Тест структуры метрик reload."""
    get_configs.cache_clear()  # type: ignore[attr-defined]

    success, message, metrics = reload_configs()

    if success:
        assert "config_count" in metrics
        assert "old_hash" in metrics
        assert "new_hash" in metrics
        assert "loaded_at" in metrics
        assert "load_time_ms" in metrics
        assert "hash_changed" in metrics

        assert isinstance(metrics["config_count"], int)
        assert isinstance(metrics["load_time_ms"], int | float)
        assert isinstance(metrics["hash_changed"], bool)
