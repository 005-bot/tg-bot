import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class Http:
    host: str
    port: int
    webhook_path: Optional[str]


@dataclass(frozen=True, slots=True)
class Redis:
    url: str
    prefix: str


@dataclass(frozen=True, slots=True)
class Telegram:
    token: str
    webhook_url: Optional[str]


@dataclass(frozen=True, slots=True)
class Admin:
    telegram_id: Optional[int]


@dataclass
class Config:
    http: Http
    redis: Redis
    telegram: Telegram
    admin: Admin


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
    admin=Admin(
        telegram_id=int(os.environ.get("ADMIN__TELEGRAM_ID", 0)) or None,
    ),
)
