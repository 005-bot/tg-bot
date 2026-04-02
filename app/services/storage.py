import asyncio
import json
from datetime import datetime, timezone
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
    ads_opt_out: bool = False


class Storage:
    def __init__(self, redis: "Redis", prefix: str):
        self.redis = redis
        self.prefix = prefix
        self.key_version = f"{prefix}:version"
        self.key_filters = f"{prefix}:filters"
        self.key_ads_counter = f"{prefix}:ads:counter"
        self.key_ads_impressions = f"{prefix}:ads:impressions"

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
                    {
                        id: Filter(street=None, ads_opt_out=False).model_dump_json()
                        for id in subscribers
                    },
                )
            )
            await result(self.redis.delete(f"{self.prefix}:subscribers"))

    async def backfill_filters(self) -> None:
        filters = await result(self.redis.hgetall(self.key_filters))
        if not filters:
            return

        updated: dict[str, str] = {}
        for user_id, raw_filter in filters.items():
            parsed = Filter.model_validate_json(raw_filter)
            updated[user_id] = parsed.model_dump_json()

        await result(self.redis.hset(self.key_filters, mapping=updated))

    async def subscribe(self, user_id: str, street: Optional[str] = None) -> None:
        current = await self.get_filter(user_id)
        await result(
            self.redis.hset(
                self.key_filters,
                user_id,
                Filter(street=street, ads_opt_out=current.ads_opt_out).model_dump_json(),
            )
        )

    async def unsubscribe(self, user_id: str) -> None:
        await result(self.redis.hdel(self.key_filters, user_id))
        await result(self.redis.hdel(self.key_ads_counter, user_id))

    async def get_subscribed(self) -> dict[str, Filter]:
        filters = await result(self.redis.hgetall(self.key_filters))
        return {k: Filter.model_validate_json(v) for k, v in filters.items()}

    async def get_filter(self, user_id: str) -> Filter:
        v = await result(self.redis.hget(self.key_filters, user_id))
        if not v:
            return Filter(street=None)

        return Filter.model_validate_json(v)

    async def set_ads_opt_out(self, user_id: str, ads_opt_out: bool) -> None:
        current = await self.get_filter(user_id)
        await result(
            self.redis.hset(
                self.key_filters,
                user_id,
                Filter(street=current.street, ads_opt_out=ads_opt_out).model_dump_json(),
            )
        )

    async def increment_ads_counter(self, user_id: str) -> int:
        return int(await result(self.redis.hincrby(self.key_ads_counter, user_id, 1)))

    async def reset_ads_counter(self, user_id: str) -> None:
        await result(self.redis.hset(self.key_ads_counter, user_id, 0))

    async def log_ad_impression(self, user_id: str, campaign_id: str, status: str) -> None:
        payload = json.dumps(
            {
                "user_id": user_id,
                "campaign_id": campaign_id,
                "status": status,
                "sent_at": datetime.now(tz=timezone.utc).isoformat(),
            },
            ensure_ascii=False,
        )
        await result(self.redis.lpush(self.key_ads_impressions, payload))
        await result(self.redis.ltrim(self.key_ads_impressions, 0, 9999))

    async def set_version(self, version: int) -> None:
        await result(self.redis.set(self.key_version, version))

    async def get_version(self) -> int:
        return int(await result(self.redis.get(self.key_version)) or 0)
