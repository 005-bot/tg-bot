from dataclasses import dataclass
from typing import Optional

from aiogram import Bot, types


@dataclass(frozen=True, slots=True)
class Config:
    admin_id: Optional[int]


class Notificator:
    def __init__(self, config: Config, bot: Bot):
        self.config = config
        self.bot = bot

    async def new_user(self, user: types.User):
        await self.notify(
            f"👤 *Новая подписка:* @{user.username or user.first_name or user.id}"
        )

    async def feedback(self, message: types.Message):
        if self.config.admin_id is None:
            return

        await self.bot.forward_message(
            self.config.admin_id, message.chat.id, message.message_id
        )

    async def notify(self, message: str):
        if self.config.admin_id is None:
            return

        await self.bot.send_message(self.config.admin_id, message)
