import logging

from aiogram import Router, filters, types

logger = logging.getLogger(__name__)

router = Router(name=__name__)


@router.message(filters.Command("help"))
async def help_handler(message: types.Message):
    if not message.from_user:
        return

    help_text = (
        "👋 *Добро пожаловать!*\n\n"
        "📋 **Доступные команды:**\n"
        "- /start - Подписаться на уведомления об отключениях 🔔\n"
        "- /stop - Отписаться от уведомлений 🔕\n"
        "- /filter - Подписаться на уведомления по конкретной улице 🏘️\n"
        "- /feedback - Оставить отзыв 💬\n"
        "- /help - Показать эту справку ❓\n\n"
        "📬 *По всем вопросам:*\n"
        "Пишите нам: help@xn--005-ddd9dya.xn--p1ai\n\n"
        "ℹ️ *Источник информации об отключениях:*\n"
        "https://005красноярск.рф"
    )
    await message.answer(help_text)

    logger.info("User %d used help command", message.from_user.id)
