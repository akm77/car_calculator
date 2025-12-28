"""Middlewares для Telegram-бота."""
from .admin_check import AdminOnlyMiddleware
__all__ = ["AdminOnlyMiddleware"]
