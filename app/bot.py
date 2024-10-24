import asyncio
import logging
import signal

from aiogram import Bot, Dispatcher, exceptions, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.storage.base import DefaultKeyBuilder
from redis.asyncio import Redis

from app import handlers
from app.config import config
from app.services import Listener, Storage

logger = logging.getLogger(__name__)


async def run():
    r = Redis.from_url(url=config.redis.url, decode_responses=True)
    s = Storage(redis=r, prefix=config.redis.prefix)

    await s.migrate()

    dp = Dispatcher(
        storage=RedisStorage(
            r, key_builder=DefaultKeyBuilder(prefix=f"{config.redis.prefix}:fsm")
        ),
    )
    dp.include_router(handlers.router)
    bot = Bot(
        token=config.telegram.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    await bot.set_my_commands(
        commands=[
            BotCommand(command="start", description="Подписаться на уведомления"),
            BotCommand(command="stop", description="Отписаться от уведомлений"),
            BotCommand(
                command="filter",
                description="Подписаться на уведомления только по определенной улице",
            ),
            BotCommand(command="help", description="Показать эту справку"),
        ]
    )

    listener = Listener(r, config.redis.prefix)

    loop = asyncio.get_event_loop()
    loop.create_task(listen(bot, listener, s))

    register_signal_handlers(loop)

    # And the run events dispatching
    try:
        await dp.start_polling(bot, storage=s, handle_signals=False)
    except asyncio.CancelledError:
        pass
    finally:
        await r.close()


async def listen(bot: Bot, listener: Listener, storage: Storage):
    async for outage in listener.listen():
        subscribers = await storage.get_subscribed()
        for user_id, f in subscribers.items():
            if f.street and f.street.lower() not in outage.address.lower():
                continue

            logger.info("Sending message to user %s", user_id)
            try:
                await bot.send_message(
                    user_id,
                    f"""
{html.bold(html.quote(outage.area))}

{html.quote(outage.address)}

{html.quote(outage.dates)}

{html.quote(outage.organization)}
                    """,
                )
            except exceptions.TelegramForbiddenError:
                await storage.unsubscribe(user_id)
                logger.info("User %s unsubscribed from updates", user_id)
            except Exception as e:
                logger.error(e)


def register_signal_handlers(loop):
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(loop)))

    logger.info("Registered signal handlers for SIGINT and SIGTERM")


async def shutdown(loop: "asyncio.AbstractEventLoop"):
    logger.info("Shutting down Telegram bot gracefully")

    # Cancel any outstanding tasks in the event loop
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

    # await dispatcher.storage.close()
    # await dispatcher.storage.wait_closed()

    logger.info("Telegram bot shutdown complete")
