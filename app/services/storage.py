import asyncio
from typing import TYPE_CHECKING, Awaitable, Optional, TypeVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from redis.asyncio import Redis

T = TypeVar("T")


async def result(value: T | Awaitable[T]) -> T:
    if asyncio.iscoroutine(value):
        return await value
    return value  # type: ignore


class Filter(BaseModel):
    street: Optional[str]


class Storage:
    def __init__(self, redis: "Redis", prefix: str):
        self.redis = redis
        self.prefix = prefix
        self.key_filters = f"{prefix}:filters"

    async def migrate(self) -> None:
        if await self.redis.exists(f"{self.prefix}:subscribed"):
            await self.redis.rename(
                f"{self.prefix}:subscribed", f"{self.prefix}:subscribers"
            )

        if await self.redis.exists(f"{self.prefix}:subscribers"):
            subscribers = await result(
                self.redis.smembers(f"{self.prefix}:subscribers")
            )
            await result(
                self.redis.hmset(
                    self.key_filters,
                    {id: Filter(street=None).model_dump_json() for id in subscribers},
                )
            )
            await result(self.redis.delete(f"{self.prefix}:subscribers"))

    async def subscribe(self, user_id: str, street: Optional[str] = None) -> None:
        await result(
            self.redis.hset(
                self.key_filters, user_id, Filter(street=street).model_dump_json()
            )
        )

    async def unsubscribe(self, user_id: str) -> None:
        await result(self.redis.hdel(self.key_filters, user_id))

    async def get_subscribed(self) -> dict[str, Filter]:
        filters = await result(self.redis.hgetall(self.key_filters))
        return {k: Filter.model_validate_json(v) for k, v in filters.items()}

    async def get_filter(self, user_id: str) -> Filter:
        v = await result(self.redis.hget(self.key_filters, user_id))
        if not v:
            return Filter(street=None)

        return Filter.model_validate_json(v)
