"""Тесты для AdminOnlyMiddleware."""

from unittest.mock import AsyncMock, MagicMock

from aiogram.types import Message, User
import pytest

from app.bot.middlewares.admin_check import AdminOnlyMiddleware


@pytest.fixture
def anyio_backend():
    """Use only asyncio backend (not trio)."""
    return "asyncio"


@pytest.fixture
def admin_middleware():
    return AdminOnlyMiddleware(admin_ids={123456, 789012})


@pytest.fixture
def mock_handler():
    handler = AsyncMock()
    handler.return_value = "handler_result"
    return handler


@pytest.fixture
def mock_message():
    message = MagicMock(spec=Message)
    message.answer = AsyncMock()
    message.message_id = 1
    message.text = "/test_command"
    return message


@pytest.mark.anyio
async def test_admin_access_granted(admin_middleware, mock_handler, mock_message):
    mock_message.from_user = User(id=123456, is_bot=False, first_name="Admin")
    result = await admin_middleware(mock_handler, mock_message, {})
    mock_handler.assert_called_once()
    assert result == "handler_result"
    mock_message.answer.assert_not_called()


@pytest.mark.anyio
async def test_non_admin_access_denied(admin_middleware, mock_handler, mock_message):
    mock_message.from_user = User(id=999999, is_bot=False, first_name="User", username="user")
    result = await admin_middleware(mock_handler, mock_message, {})
    mock_handler.assert_not_called()
    assert result is None
    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "Access Denied" in call_args
    assert "999999" in call_args


@pytest.mark.anyio
async def test_message_without_user(admin_middleware, mock_handler, mock_message):
    mock_message.from_user = None
    result = await admin_middleware(mock_handler, mock_message, {})
    mock_handler.assert_not_called()
    assert result is None


def test_empty_admin_list():
    middleware = AdminOnlyMiddleware(admin_ids=set())
    assert len(middleware.admin_ids) == 0
