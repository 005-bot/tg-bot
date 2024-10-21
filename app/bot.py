# import asyncio
# import aioredis
# from aiogram import Bot, Dispatcher, types
# from aiogram.types import ParseMode
# from aiogram.utils import executor

# from app.config import config

# # Replace with your Telegram bot token and Redis URL
# TELEGRAM_BOT_TOKEN = config.telegram.token
# REDIS_URL = config.redis.url
# REDIS_CHANNEL = config.redis.prefix

# # Initialize the bot and dispatcher
# bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode=ParseMode.HTML)
# dp = Dispatcher()

# # Store user IDs who subscribed to receive messages
# subscribed_users = set()


# @dp.message_handler(commands=["start"])
# async def start_handler(message: types.Message):
#     subscribed_users.add(message.from_user.id)
#     await message.reply("You have subscribed to updates!")


# @dp.message_handler(commands=["stop"])
# async def stop_handler(message: types.Message):
#     subscribed_users.discard(message.from_user.id)
#     await message.reply("You have unsubscribed from updates.")


# async def listen_to_redis():
#     global redis
#     redis = await aioredis.create_redis(REDIS_URL)
#     try:
#         res = await redis.subscribe(REDIS_CHANNEL)
#         channel = res[0]

#         while await channel.wait_message():
#             msg = await channel.get(encoding="utf-8")
#             print(f"Received message from Redis: {msg}")
#             await broadcast_message(msg)
#     except Exception as e:
#         print(f"Error: {e}")
#     finally:
#         redis.close()
#         await redis.wait_closed()


# async def broadcast_message(msg):
#     for user_id in subscribed_users:
#         try:
#             await bot.send_message(user_id, msg)
#         except Exception as e:
#             print(f"Failed to send message to {user_id}: {e}")

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.config import config

dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    # Most event objects have aliases for API methods that can be called in events' context
    # For example if you want to answer to incoming message you can use `message.answer(...)` alias
    # and the target chat will be passed to :ref:`aiogram.methods.send_message.SendMessage`
    # method automatically or call API method directly via
    # Bot instance: `bot.send_message(chat_id=message.chat.id, ...)`
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")


async def run():
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(
        token=config.telegram.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # And the run events dispatching
    await dp.start_polling(bot)
