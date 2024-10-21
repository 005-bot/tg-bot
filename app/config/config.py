from dataclasses import dataclass
import os


@dataclass
class Redis:
    url: str
    prefix: str


@dataclass
class Telegram:
    token: str


@dataclass
class Config:
    redis: Redis
    telegram: Telegram


config = Config(
    redis=Redis(
        url=os.environ.get("REDIS__URL", "redis://localhost:6379"),
        prefix=os.environ.get("REDIS__PREFIX", "bot-005"),
    ),
    telegram=Telegram(
        token=os.environ.get("TELEGRAM__TOKEN", ""),
    ),
)
