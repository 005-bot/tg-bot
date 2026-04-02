# Feature Plan: Ads in Bot Messages

## 1. Goal and non-goals

### Goal
Add promotional/ad content to outgoing bot messages in a controlled and measurable way, without breaking the outage-notification UX.

### Non-goals (phase 1)
- Building a full ad auction/bidding system.
- Supporting rich media ads (images/video) in the first release.
- Personalized targeting beyond simple subscription metadata.

## 2. Current message flow (baseline)

The bot currently composes outage messages in `app/bot.py` (`listen`) and sends one HTML-formatted text message per subscriber. This is the insertion point for an ad block.

## 3. Product requirements

1. Ads must be optional and controlled by config/feature flag.
2. Ads must preserve critical outage information as the primary content.
3. Ad frequency must be capped (e.g., every Nth message per user).
4. Ads must be auditable (which ad was sent, to whom, when).
5. Users should be able to opt out of ads (if business/legal requires).
6. Failures in ad selection/rendering must never block outage delivery.

## 4. Proposed architecture

### 4.1 Data model

Add ad-related entities to storage:

- `ads`: ad campaign data.
  - `id`
  - `title`
  - `body` (plain text/HTML-safe text)
  - `cta_text`
  - `cta_url`
  - `start_at`, `end_at`
  - `is_active`
  - `priority`
  - `target_street` (optional, nullable)
  - `target_resource_type` (optional, nullable)
  - `daily_impression_cap` (optional)
  - `created_at`, `updated_at`

- `ad_impressions`: delivery log.
  - `id`
  - `ad_id`
  - `user_id`
  - `outage_id` (or hash/period marker if outage id unavailable)
  - `sent_at`
  - `delivery_status` (`sent`, `failed`)

- `ad_user_state` (Redis or persistent):
  - `user_id`
  - `messages_since_last_ad`
  - `last_ad_id`
  - `last_ad_sent_at`
  - `ads_opt_out` (if not stored in existing subscriber profile)

### 4.2 Service layer

Introduce `AdService` with clear responsibilities:

- `get_candidate_ads(context) -> list[Ad]`
- `select_ad(user_id, context) -> Ad | None`
- `render_ad(ad) -> str`
- `track_impression(...)`

`context` should include:
- outage resource type
- affected streets
- current timestamp
- user subscription filters

### 4.3 Message composition strategy

Keep outage message first. Append ad in a distinct block:

```text
<OUTAGE_MESSAGE>

———
Партнерское сообщение:
<AD_TEXT>
<CTA>
```

Rules:
- Enforce Telegram message limit (4096 chars) after ad append.
- If message exceeds limit, trim ad first; never trim critical outage summary below minimum threshold.
- Escape/validate ad text for HTML mode.

### 4.4 Delivery and resilience

Inside `listen`:
1. Build core outage message (existing behavior).
2. If ad feature enabled and user eligible:
   - request ad from `AdService`
   - append rendered ad
3. Send message.
4. Best-effort impression logging (non-fatal on failure).

Any ad-related error should log and fall back to outage-only message.

## 5. Config and feature flags

Add config options:

- `ads.enabled` (bool)
- `ads.default_frequency` (int, e.g. show ad every 3 messages)
- `ads.max_ad_chars` (int)
- `ads.fallback_mode` (`off`, `house_ad`, `pass_through`)

Use gradual rollout:
- stage 0: disabled
- stage 1: internal users/admin only
- stage 2: 5–10% of users
- stage 3: 100%

## 6. Admin operations

Create simple admin workflows (CLI or internal command handlers):

- create/update/pause ad campaign
- list active campaigns
- inspect impression metrics by date/ad

If no admin UI yet, start with migration + script-based management.

## 7. Privacy/compliance checks

Before launch:
- confirm ad labeling requirements in target jurisdiction.
- add clear “sponsored/partner” marker.
- validate CTA links against allowlist.
- document retention policy for impression logs.

## 8. Metrics and observability

Track:
- `ads_selected_total`
- `ads_appended_total`
- `ads_selection_errors_total`
- `ads_impressions_logged_total`
- message send success rate (with and without ads)
- unsubscribe rate delta after ads rollout

Add structured logs with `user_id`, `ad_id`, and rollout cohort.

## 9. Testing plan

### Unit tests
- ad eligibility/filtering
- frequency capping
- render escaping and truncation
- fallback behavior on `AdService` exceptions

### Integration tests
- listener sends outage-only when ads disabled
- listener appends ad when enabled and ad exists
- listener keeps sending outage message if tracking fails

### Manual verification
- send sample outage with long street list + ad
- verify HTML parse mode is valid
- verify no message exceeds Telegram limit

## 10. Incremental implementation plan

### Milestone 1 (foundation)
- Add config flags and data models/migrations.
- Add `AdService` interface + no-op implementation.
- Wire ad hook into message pipeline behind feature flag.

### Milestone 2 (basic delivery)
- Implement campaign selection and frequency cap.
- Implement ad append + length-safe truncation.
- Add impression logging.

### Milestone 3 (operability)
- Add admin scripts/commands for campaign lifecycle.
- Add metrics dashboards and alert on ad errors.
- Rollout by cohort.

### Milestone 4 (optimization)
- Targeting refinements.
- A/B tests for ad wording/placement.
- Reporting exports.

## 11. Risks and mitigations

- **Risk:** Ads reduce trust or increase unsubscribes.
  - **Mitigation:** low frequency cap + clear labeling + cohort rollback.

- **Risk:** Message length overflows with long outages.
  - **Mitigation:** deterministic truncation policy prioritizing outage text.

- **Risk:** Ad subsystem outage affects notification path.
  - **Mitigation:** strict fail-open design (outage message always sent).

- **Risk:** Malicious/broken ad content.
  - **Mitigation:** HTML escaping, URL validation, and admin-only campaign authoring.

## 12. Suggested first engineering tasks

1. Add `ads` settings to config schema and `.env.example`.
2. Create migration for ad tables.
3. Add `app/services/ads.py` with no-op + simple selector implementation.
4. Refactor message formatting into helper function to simplify tests.
5. Add tests for truncation and fail-open behavior.
