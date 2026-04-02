from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from aiogram import html

from app.config import config
from app.config.config import AdCampaign
from app.services.storage import Filter, Storage

MAX_MESSAGE_LENGTH = 4096
ELLIPSIS = "…"


class AdService:
    def __init__(self, storage: Storage):
        self.storage = storage

    def is_enabled(self) -> bool:
        return config.ads.enabled and bool(config.ads.campaigns)

    async def pick_for_user(self, user_id: str, user_filter: Filter) -> AdCampaign | None:
        if not self.is_enabled() or user_filter.ads_opt_out:
            return None

        counter = await self.storage.increment_ads_counter(user_id)
        if counter < config.ads.frequency:
            return None

        await self.storage.reset_ads_counter(user_id)

        campaigns = config.ads.campaigns
        today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        stable_hash = hashlib.sha256(f"{user_id}:{today}".encode()).hexdigest()
        idx = int(stable_hash, 16) % len(campaigns)
        return campaigns[idx]

    def append_to_message(self, message: str, campaign: AdCampaign | None) -> str:
        if not campaign:
            return message

        ad_lines = [
            "",
            "",
            "———",
            f"<b>{html.quote(config.ads.label)}</b>",
            html.quote(campaign.text),
        ]
        if campaign.cta_url:
            ad_lines.append(html.quote(campaign.cta_url))

        ad_block = "\n".join(ad_lines)
        if len(ad_block) > config.ads.max_chars:
            ad_block = ad_block[: config.ads.max_chars - len(ELLIPSIS)] + ELLIPSIS

        available = MAX_MESSAGE_LENGTH - len(message)
        if available <= 0:
            return message

        if len(ad_block) > available:
            ad_block = ad_block[: max(0, available - len(ELLIPSIS))] + ELLIPSIS

        return f"{message}{ad_block}"

    async def track_impression(
        self, user_id: str, campaign: AdCampaign | None, sent: bool = True
    ) -> None:
        if not campaign:
            return

        await self.storage.log_ad_impression(
            user_id=user_id,
            campaign_id=campaign.campaign_id,
            status="sent" if sent else "failed",
        )
