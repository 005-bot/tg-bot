from typing import TYPE_CHECKING

from apis.pubsub_models import Outage

if TYPE_CHECKING:
    from redis.asyncio import Redis


class Listener:
    def __init__(self, redis: "Redis", prefix: str):
        self.redis = redis
        self.channel = f"{prefix}:outages"

    async def listen(self):
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(self.channel)

        async for message in pubsub.listen():
            if message["type"] != "message":
                continue

            data: str = message["data"]
            outage = Outage.from_json(data)

            yield outage
