import asyncio
from typing import TYPE_CHECKING, Set


if TYPE_CHECKING:
    from redis.asyncio import Redis


class Storage:
    def __init__(self, redis: "Redis", prefix: str):
        self.redis = redis
        self.key_subscribed = f"{prefix}:subscribed"

    async def subscribe(self, user_id: str) -> None:
        call = self.redis.sadd(self.key_subscribed, user_id)
        if asyncio.iscoroutine(call):
            await call

    async def unsubscribe(self, user_id: str) -> None:
        call = self.redis.srem(self.key_subscribed, user_id)
        if asyncio.iscoroutine(call):
            await call

    async def get_subscribed(self) -> Set[str]:
        call = self.redis.smembers(self.key_subscribed)
        if asyncio.iscoroutine(call):
            return await call

        return call  # type: ignore
