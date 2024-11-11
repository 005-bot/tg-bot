import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Http:
    host: str
    port: int
    webhook_path: Optional[str]


@dataclass
class Redis:
    url: str
    prefix: str


@dataclass
class Telegram:
    token: str
    webhook_url: Optional[str]


@dataclass
class Config:
    http: Http
    redis: Redis
    telegram: Telegram


config = Config(
    http=Http(
        host=os.environ.get("HTTP__HOST", "0.0.0.0"),
        port=int(os.environ.get("HTTP__PORT", "8000")),
        webhook_path=os.environ.get("HTTP__WEBHOOK_PATH", None),
    ),
    redis=Redis(
        url=os.environ.get("REDIS__URL", "redis://localhost:6379"),
        prefix=os.environ.get("REDIS__PREFIX", "bot-005"),
    ),
    telegram=Telegram(
        token=os.environ.get("TELEGRAM__TOKEN", ""),
        webhook_url=os.environ.get("TELEGRAM__WEBHOOK_URL", None),
    ),
)
