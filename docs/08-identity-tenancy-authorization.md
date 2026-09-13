# Identity, Tenancy, and Authorization

## Identity model

- `Account` represents a permanent authenticated human in Supabase Auth.
- `StudioPlayer` is the universal LenGeas player ID and is independent of an external provider.
- `PlayerIdentity` links a StudioPlayer to a guest credential or Supabase `sub`.
- `GameProfile` isolates one StudioPlayer's state for one game.
- `GlobalProfile` contains only explicitly global achievements, entitlements, cosmetics, and cross-game rewards.
- `StudioUser` links an Account to studio memberships and operator roles.

External provider IDs never appear as primary keys outside the identity collection.

## Authentication

Supabase Auth uses asymmetric signing keys and exposes JWKS. FastAPI validates signature, issuer, audience, expiry, not-before, and key ID, then maps `sub` to the internal account. The Edge Gateway performs no final authorization. It rejects malformed tokens and forwards the bearer token to the origin over authenticated TLS.

Supported v1 sign-in methods are email one-time password, Apple, and Google. Studio operators require MFA. Production service accounts use OAuth client credentials issued by the LenGeas control plane and short-lived signed tokens.

## Guest flow

1. A client requests a guest challenge and submits device-generated public key material plus Turnstile proof.
2. The identity service creates a guest PlayerIdentity, StudioPlayer, and device-bound refresh credential.
3. The guest plays with normal game isolation and stricter abuse/rate limits.
4. After sign-in, the account requests merge with proofs for both identities.
5. A merge plan lists profile collisions, entitlements, balances, and selected domain strategies.
6. The backend executes the plan once under a merge idempotency key and writes an irreversible identity link plus audit event.
7. Old guest credentials are revoked and redirected to the permanent StudioPlayer.

Automatic merge is allowed only when no game-profile collision exists. Collisions require the player to choose a profile per game; currencies are never summed automatically.

## Authorization model

RBAC provides coarse roles: `owner`, `admin`, `developer`, `designer`, `writer`, `analyst`, `support`, `viewer`, and `ai_agent`. ABAC adds studio, game, environment, resource type, action, ownership, support case, data sensitivity, and time-bound grant.

The FastAPI policy decision point evaluates every request. Handlers cannot implement ad hoc role checks. MongoDB repository scope is derived from the authorized context, not request fields.

## Separation of duties

- An author cannot approve the same definition version.
- An AI agent cannot approve or publish.
- Production publishing requires two human approvals: a game owner and a platform release approver.
- Support can view redacted player data only while an open support case grants access.
- Financial correction requires two-person approval and a compensating ledger transaction.
- Infrastructure production apply requires an approved plan and protected GitHub environment.

## Cross-game contracts

A contract names source game, target game, qualifying event, minimal payload, reward mapping, delivery limits, expiry, revocation, and both game-owner approvals. The cross-game service receives the event and issues a target-game action. Source code cannot query the target profile.

## Account lifecycle

Account export, correction, restriction, deletion, and legal hold are workflow-backed, audited operations. Deletion revokes credentials immediately, removes personal identifiers on schedule, pseudonymizes retained financial records, and creates a non-authenticating tombstone to prevent accidental relink.

## Security evidence

Supabase documents verification against asymmetric JWKS and the relevant token claims at <https://supabase.com/docs/guides/auth/jwts>. Phase 03 includes key rotation and cache-purge drills before authentication is accepted for production.
