import logging

from aiogram import Router
from aiogram.types import ErrorEvent

from app.errors import APIError, UserInputError

logger = logging.getLogger(__name__)


async def handle_error(event: ErrorEvent) -> bool:
    """Global error handler for user-facing exceptions"""
    error = event.exception
    update = event.update
    message = update.message

    # Generate user message based on error type
    if isinstance(error, UserInputError):
        text = f"⚠️ Ошибка ввода: {error}"
    elif isinstance(error, APIError):
        text = "🔧 Временная проблема с сервисом, пожалуйста, попробуйте позже"
    else:
        text = "🚨 Системная ошибка - наша команда уведомлена"

    # Send response and log details
    if message:
        await message.answer(text)

    logger.error("Error handling update %s", update.update_id, exc_info=error)

    # Prevent propagation to other error handlers
    return True


def register_errors(router: Router) -> None:
    """Register error handlers with the router"""
    router.error.register(handle_error)
