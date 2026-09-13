# Assets, Localization, and Notifications

## Asset authority

MongoDB stores asset metadata, ownership, status, license, and references. Cloudflare R2 stores binary originals and non-image artifacts. Cloudflare Images stores and delivers approved raster variants. Definition objects reference immutable `asset_id` plus revision digest; they never embed public provider URLs.

## Asset lifecycle

`requested -> uploading -> quarantined -> scanning -> approved -> published -> deprecated -> archived -> deleted`

1. An authorized user requests an upload with expected type, size, game, purpose, license, and SHA-256.
2. The asset API returns a short-lived single-object upload URL to a private R2 quarantine bucket.
3. R2 Event Notification publishes to a Cloudflare Queue. Its Worker consumer invokes the authenticated AWS asset-scan API.
4. The Celery asset worker downloads the object, verifies digest/type/size, scans with pinned ClamAV signatures, strips unsafe metadata, and re-encodes supported images.
5. Approved originals move by verified copy into the private approved bucket. Raster variants publish through Cloudflare Images.
6. Publishing resolves asset references and rejects quarantined, missing, unlicensed, wrong-game, deleted, or digest-mismatched assets.

Executables, scripts, archives containing symlinks, SVG with active content, and files exceeding declared limits are rejected. SVG is sanitized and served with restrictive headers or rasterized before player delivery.

## Delivery

`assets.lengeas.com` is a Worker route. The Worker authorizes private assets or validates a short-lived signed token, resolves immutable digest, applies an allowlisted image variant, sets immutable cache headers, and prevents path traversal. Published public assets use content-addressed URLs. Revocation removes the delivery mapping and purges cache.

## Localization

Localization catalogs are versioned definition content using ICU MessageFormat 2 syntax. Every game declares a source locale and supported locales. Fallback is exact locale, language locale, game source locale, then platform English. A published bundle must provide every required player-visible key in source locale and every safety, purchase, and legal key in all enabled locales.

Validation checks missing and unused keys, argument names/types, plural/select branches, markup allowlist, bidirectional-text isolation, maximum rendered length classes, and deterministic catalog digest. Runtime supplies values; definitions cannot inject HTML or executable formatting.

## Notifications

The notification service owns versioned templates, preferences, consent, quiet hours, frequency caps, deduplication, delivery attempts, and provider receipts. Channels are in-game inbox, Resend email, Amazon SNS Mobile Push for APNs/FCM, and VAPID web push.

A send command names template version, recipient, game, locale, variables, channel policy, schedule, expiry, and idempotency key. The server renders from an allowlisted typed variable schema. Economy rewards are never attached directly to a notification; an inbox claim references a separate idempotent reward action.

Critical security and purchase notifications ignore marketing opt-out but still obey legal channel rules. Marketing requires recorded consent. Provider failures retry with bounded exponential backoff and enter a dead-letter queue; they never switch channels without declared policy.

## Required controls

- Per-studio/game asset and notification quotas.
- Copyright/license owner, source, rights territory, expiry, and takedown workflow.
- Asset antivirus signature freshness alert and rescan workflow.
- No PII in asset names, URLs, cache keys, analytics, or notification template IDs.
- Device token encryption, rotation, invalid-token removal, and account-deletion cleanup.
- Render previews in Studio for every locale/channel before publication.
- Audit from upload/request through scan, publish, delivery, send, provider receipt, and deletion.

## Completion tests

Upload valid and malicious files, spoof MIME/digest, replay upload URLs, cross-game/studio reference, revoke a published asset, purge CDN, expire a license, render every plural/select path, test RTL and long text, send/dedupe/retry each channel, rotate device tokens, enforce consent/quiet hours/caps, claim an inbox reward twice, and reconcile provider receipts.
