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


@dataclass(frozen=True, slots=True)
class AdCampaign:
    campaign_id: str
    text: str
    cta_url: Optional[str]


@dataclass(frozen=True, slots=True)
class Ads:
    enabled: bool
    frequency: int
    label: str
    max_chars: int
    campaigns: tuple[AdCampaign, ...]


@dataclass
class Config:
    http: Http
    redis: Redis
    telegram: Telegram
    admin: Admin
    ads: Ads


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_campaigns(value: str) -> tuple[AdCampaign, ...]:
    campaigns: list[AdCampaign] = []
    for idx, chunk in enumerate(value.split("||"), start=1):
        chunk = chunk.strip()
        if not chunk:
            continue

        parts = [part.strip() for part in chunk.split("::")]
        text = parts[0] if parts else ""
        cta_url = parts[1] if len(parts) > 1 and parts[1] else None
        if not text:
            continue

        campaigns.append(
            AdCampaign(campaign_id=f"campaign-{idx}", text=text, cta_url=cta_url)
        )

    return tuple(campaigns)


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
    ads=Ads(
        enabled=_env_bool("ADS__ENABLED", False),
        frequency=max(1, int(os.environ.get("ADS__FREQUENCY", "3"))),
        label=os.environ.get("ADS__LABEL", "Партнерское сообщение"),
        max_chars=max(32, int(os.environ.get("ADS__MAX_CHARS", "320"))),
        campaigns=_parse_campaigns(os.environ.get("ADS__CAMPAIGNS", "")),
    ),
)
