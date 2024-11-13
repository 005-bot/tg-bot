import asyncio
import logging
import signal
from typing import Optional

from aiogram import Bot, Dispatcher, exceptions, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from redis.asyncio import Redis

from app import handlers
from app.admin import Notificator, Config
from app.config import config
from app.services import Listener, Storage

logger = logging.getLogger(__name__)


def create_bot():
    return Bot(
        token=config.telegram.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


async def set_webhook(url: str):
    async with create_bot() as bot:
        await bot.set_webhook(url, allowed_updates=["message"])


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

    bot = create_bot()
    await bot.set_my_commands(
        commands=[
            BotCommand(command="start", description="Подписаться на уведомления"),
            BotCommand(command="stop", description="Отписаться от уведомлений"),
            BotCommand(
                command="filter",
                description="Подписаться на уведомления только по определенной улице",
            ),
            BotCommand(command="feedback", description="Отправить отзыв"),
            BotCommand(command="help", description="Показать справку"),
        ]
    )

    notificator = Notificator(Config(admin_id=config.admin.telegram_id), bot)

    listener = Listener(r, config.redis.prefix)

    loop = asyncio.get_event_loop()
    loop.create_task(listen(bot, listener, s))

    register_signal_handlers(loop)

    # And the run events dispatching
    try:
        if not config.http.webhook_path:
            await start_polling(bot, dp, storage=s, notificator=notificator)
        else:
            await start_webhook(
                bot,
                dp,
                config.telegram.webhook_url,
                config.http.webhook_path,
                storage=s,
                notificator=notificator,
            )
    except asyncio.CancelledError:
        pass
    finally:
        await r.close()


async def start_polling(bot: Bot, dp: Dispatcher, **kwargs):
    await bot.delete_webhook()
    await dp.start_polling(bot, handle_signals=False, **kwargs)


async def start_webhook(
    bot: Bot, dp: Dispatcher, webhook_url: Optional[str], webhook_path: str, **kwargs
):
    async def on_startup(_):
        logger.info("Starting webhook")
        if webhook_url:
            await bot.set_webhook(webhook_url)

    async def on_shutdown(_):
        logger.info("Shutting down webhook")
        if webhook_url:
            await bot.delete_webhook()

    # Create aiohttp.web.Application instance
    app = web.Application()

    # Register startup and shutdown callbacks
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Create an instance of request handler,
    # aiogram has few implementations for different cases of usage
    # In this example we use SimpleRequestHandler which is designed to handle simple cases
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot, **kwargs)
    # Register webhook handler on application
    webhook_requests_handler.register(app, path=webhook_path)

    # Mount dispatcher startup and shutdown hooks to aiohttp application
    setup_application(app, dp, bot=bot)

    # And finally start webserver
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=config.http.host, port=config.http.port)
    await site.start()

    # wait forever
    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        logger.info("Shutting down")
        await site.stop()
        await runner.cleanup()


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
