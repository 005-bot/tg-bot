import logging
from typing import TYPE_CHECKING
from aiogram import Router, types, filters

if TYPE_CHECKING:
    from app.services import Storage

logger = logging.getLogger(__name__)

router = Router(name=__name__)


@router.message(filters.CommandStart())
async def start_handler(message: types.Message, storage: "Storage"):
    if not message.from_user:
        return

    user_id = message.from_user.id
    await storage.subscribe(str(user_id))
    await message.answer("Вы подписались на уведомления об отключениях")

    logger.info("User %d subscribed to updates", user_id)


@router.message(filters.Command("stop"))
async def stop_handler(message: types.Message, storage: "Storage"):
    if not message.from_user:
        return

    user_id = message.from_user.id
    await storage.unsubscribe(str(user_id))
    await message.answer("Вы отписались от уведомлений об отключениях")

    logger.info("User %d unsubscribed from updates", user_id)
