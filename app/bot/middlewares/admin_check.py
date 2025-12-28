"""
Middleware для проверки прав доступа администраторов.
"""
import structlog
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from typing import Callable, Dict, Any, Awaitable

logger = structlog.get_logger()


class AdminOnlyMiddleware(BaseMiddleware):
    """
    Middleware для проверки прав доступа к административным командам.

    Разрешает выполнение команд только пользователям из белого списка.
    Логирует все попытки несанкционированного доступа.

    Args:
        admin_ids: Множество Telegram user IDs администраторов
    """

    def __init__(self, admin_ids: set[int]):
        super().__init__()
        self.admin_ids = admin_ids
        logger.info(
            "admin_middleware_initialized",
            admin_count=len(admin_ids),
        )

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        """
        Проверить права доступа перед выполнением хэндлера.

        Args:
            handler: Следующий обработчик в цепочке
            event: Telegram message
            data: Контекст обработки

        Returns:
            Результат handler'а или None (если доступ запрещён)
        """
        user = event.from_user

        if not user:
            logger.warning("message_without_user", message_id=event.message_id)
            return None

        # Проверка прав доступа
        if user.id not in self.admin_ids:
            logger.warning(
                "unauthorized_access_attempt",
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                command=event.text,
            )

            await event.answer(
                "🚫 **Access Denied**\n\n"
                "This command is restricted to administrators only.\n\n"
                f"Your user ID: `{user.id}`\n"
                "Contact the system administrator if you need access."
            )
            return None

        # Логирование успешного доступа
        logger.info(
            "admin_command_executed",
            user_id=user.id,
            username=user.username,
            command=event.text,
        )

        # Продолжить выполнение
        return await handler(event, data)

