"""Synchronous domain façades backed by MongoDB for the FastAPI domain services.

The API domain services are intentionally synchronous value-object services.  This
adapter keeps that contract while making every durable write go to MongoDB and
hydrating cache misses from Mongo, so multiple API workers share identity state.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

from packages.domain.audit.events import EventEnvelope
from packages.domain.identity.models import (
    Account,
    AuditEvent,
    GameProfile,
    IdentityKind,
    PlayerIdentity,
    StudioPlayer,
)
from packages.domain.identity.privacy import PrivacyOperation, PrivacyRequest
from packages.domain.identity.repository import InMemoryIdentityRepository
from packages.domain.tenancy.models import (
    Membership,
    MembershipRole,
    ServiceAccount,
    Studio,
)
from packages.domain.tenancy.repository import InMemoryTenantRepository


class MongoIdentityDomainRepository(InMemoryIdentityRepository):
    def __init__(self, database: Any) -> None:
        super().__init__()
        self.database = database

    def _hydrate_account(self, document: dict[str, Any]) -> Account:
        account = self.accounts.get(document["account_id"])
        if account is None:
            account = Account(
                document["account_id"],
                document.get("created_at", datetime.now(UTC)),
                document.get("email_hash"),
                document.get("deleted_at"),
                bool(document.get("restricted", False)),
                int(document.get("session_epoch", 0)),
                document.get("player_id"),
            )
            self.accounts[account.account_id] = account
        return account

    def _hydrate_player(self, document: dict[str, Any]) -> StudioPlayer:
        player = self.players.get(document["player_id"])
        if player is None:
            player = StudioPlayer(
                document["player_id"],
                document.get("created_at", datetime.now(UTC)),
                document.get("deleted_at"),
                bool(document.get("tombstone", False)),
            )
            self.players[player.player_id] = player
            self.player_studios.setdefault(player.player_id, set())
        return player

    def account_for_id(self, account_id: str) -> Account | None:
        if account_id in self.accounts:
            return self.accounts[account_id]
        document = self.database.accounts.find_one({"account_id": account_id})
        return self._hydrate_account(document) if document else None

    def save_account(self, account: Account) -> None:
        self.database.accounts.update_one(
            {"account_id": account.account_id},
            {
                "$set": {
                    "player_id": account.player_id,
                    "deleted_at": account.deleted_at,
                    "email_hash": account.email_hash,
                    "restricted": account.restricted,
                    "session_epoch": account.session_epoch,
                }
            },
            upsert=True,
        )

    def player_for_id(self, player_id: str) -> StudioPlayer | None:
        if player_id in self.players:
            return self.players[player_id]
        document = self.database.studio_players.find_one({"player_id": player_id})
        return self._hydrate_player(document) if document else None

    def create_account(self, email_hash: str | None = None) -> Account:
        account = super().create_account(email_hash)
        self.database.accounts.insert_one(
            {
                "account_id": account.account_id,
                "created_at": account.created_at,
                "email_hash": account.email_hash,
                "session_epoch": account.session_epoch,
                "player_id": account.player_id,
            }
        )
        return account

    def create_player(self) -> StudioPlayer:
        player = super().create_player()
        self.database.studio_players.insert_one(
            {
                "player_id": player.player_id,
                "created_at": player.created_at,
                "tombstone": False,
            }
        )
        self.database.global_profiles.insert_one(
            {"player_id": player.player_id, "entitlements": [], "cosmetics": []}
        )
        return player

    def identity_for_provider(self, provider: str, value: str) -> PlayerIdentity | None:
        identity = super().identity_for_provider(provider, value)
        if identity is not None:
            return identity
        document = self.database.player_identities.find_one(
            {
                "provider": provider,
                "subject_or_credential_hash": value,
                "revoked_at": {"$exists": False},
            }
        )
        if not document:
            return None
        identity = PlayerIdentity(
            document["identity_id"],
            document["player_id"],
            IdentityKind(document["kind"]),
            document["provider"],
            document["subject_or_credential_hash"],
            document.get("created_at", datetime.now(UTC)),
            document.get("revoked_at"),
            document.get("device_key_fingerprint"),
            document.get("account_id"),
        )
        self.identities[identity.identity_id] = identity
        self._provider_subject[(provider, value)] = identity.identity_id
        self._hydrate_player({"player_id": identity.player_id})
        return identity

    def link_identity(self, *args: Any, **kwargs: Any) -> PlayerIdentity:
        identity = super().link_identity(*args, **kwargs)
        self.database.player_identities.insert_one(
            {
                "identity_id": identity.identity_id,
                "player_id": identity.player_id,
                "kind": identity.kind.value,
                "provider": identity.provider,
                "subject_or_credential_hash": identity.subject_or_credential_hash,
                "created_at": identity.created_at,
                "device_key_fingerprint": identity.device_key_fingerprint,
                "account_id": identity.account_id,
            }
        )
        return identity

    def replace_device_key(
        self, identity_id: str, old_fingerprint: str, new_fingerprint: str
    ) -> None:
        super().replace_device_key(identity_id, old_fingerprint, new_fingerprint)
        self.database.player_identities.update_one(
            {"identity_id": identity_id}, {"$set": {"device_key_fingerprint": new_fingerprint}}
        )

    def create_profile(self, scope: Any, player_id: str, game_id: str) -> GameProfile:
        profile = super().create_profile(scope, player_id, game_id)
        self.database.game_profiles.insert_one(
            {
                "profile_id": profile.profile_id,
                "player_id": profile.player_id,
                "studio_id": profile.studio_id,
                "game_id": profile.game_id,
                "state": profile.state,
                "entitlements": list(profile.entitlements),
                "state_version": profile.state_version,
            }
        )
        return profile

    def profiles_for(self, scope: Any, player_id: str) -> list[GameProfile]:
        profiles = super().profiles_for(scope, player_id)
        if profiles:
            return profiles
        documents = self.database.game_profiles.find(
            {
                "studio_id": scope.studio_id,
                "player_id": player_id,
                **({"game_id": scope.game_id} if scope.game_id is not None else {}),
            }
        )
        for document in documents:
            profile = GameProfile(
                document["profile_id"],
                document["player_id"],
                document["studio_id"],
                document["game_id"],
                dict(document.get("state", {})),
                set(document.get("entitlements", [])),
                int(document.get("state_version", 0)),
            )
            self.profiles[profile.profile_id] = profile
            self.player_studios.setdefault(player_id, set()).add(scope.studio_id)
            profiles.append(profile)
        return profiles

    def all_identities(self) -> Iterator[PlayerIdentity]:
        for document in self.database.player_identities.find({}):
            self.identity_for_provider(document["provider"], document["subject_or_credential_hash"])
        return super().all_identities()

    def record_audit(self, *args: Any, **kwargs: Any) -> AuditEvent:
        event = super().record_audit(*args, **kwargs)
        self.database.audit_events.insert_one(
            {
                "event_id": event.event_id,
                "action": event.action,
                "actor_id": event.actor_id,
                "studio_id": event.studio_id,
                "subject_id": event.subject_id,
                "occurred_at": event.occurred_at,
                "metadata": event.metadata,
            }
        )
        return event

    def emit(self, event: EventEnvelope) -> None:
        super().emit(event)
        self.database.event_outbox.insert_one(
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "occurred_at": event.occurred_at,
                "producer": event.producer,
                "studio_id": event.studio_id,
                "game_id": event.game_id,
                "player_id": event.player_id,
                "payload": event.payload,
            }
        )

    def persist_privacy_request(self, request: Any) -> None:
        self.database.privacy_requests.update_one(
            {"request_id": request.request_id},
            {
                "$set": {
                    "request_id": request.request_id,
                    "account_id": request.account_id,
                    "operation": request.operation.value,
                    "requested_at": request.requested_at,
                    "status": request.status,
                    "legal_hold": request.legal_hold,
                    "studio_id": request.studio_id,
                }
            },
            upsert=True,
        )

    def persist_privacy_completion(self, request: Any) -> None:
        self.persist_privacy_request(request)
        self.database.privacy_requests.update_one(
            {"request_id": request.request_id}, {"$set": {"completed_at": datetime.now(UTC)}}
        )

    def privacy_request_for(self, request_id: str) -> PrivacyRequest | None:
        document = self.database.privacy_requests.find_one({"request_id": request_id})
        if document is None:
            return None
        return PrivacyRequest(
            document["request_id"],
            document["account_id"],
            PrivacyOperation(document["operation"]),
            document.get("requested_at", datetime.now(UTC)),
            document.get("status", "queued"),
            bool(document.get("legal_hold", False)),
            document.get("studio_id"),
        )

    def persist_financial_record(
        self, studio_id: str | None, account_id: str, pseudonym: str, request_id: str
    ) -> None:
        self.database.financial_history.update_one(
            {"studio_id": studio_id, "account_id": account_id},
            {
                "$set": {
                    "studio_id": studio_id,
                    "account_id": account_id,
                    "pseudonym": pseudonym,
                    "request_id": request_id,
                    "updated_at": datetime.now(UTC),
                }
            },
            upsert=True,
        )

    def merge_result(
        self,
        scope: Any,
        source_player: str,
        target_player: str,
        idempotency_key: str,
        fingerprint: str | None = None,
    ) -> str | None:
        result = super().merge_result(
            scope, source_player, target_player, idempotency_key, fingerprint
        )
        if result is not None:
            return result
        document = self.database.merge_idempotency.find_one(
            {
                "studio_id": scope.studio_id,
                "actor_id": scope.actor_id,
                "idempotency_key": idempotency_key,
            }
        )
        if document is None:
            return None
        if fingerprint is not None and document.get("payload_digest") != fingerprint:
            raise ValueError("idempotency_conflict")
        super().save_merge_result(
            scope, idempotency_key, document["target_player_id"], document.get("payload_digest")
        )
        return str(document["target_player_id"])

    def save_merge_result(
        self, scope: Any, idempotency_key: str, player_id: str, fingerprint: str | None = None
    ) -> None:
        super().save_merge_result(scope, idempotency_key, player_id, fingerprint)
        self.database.merge_idempotency.update_one(
            {
                "studio_id": scope.studio_id,
                "actor_id": scope.actor_id,
                "idempotency_key": idempotency_key,
            },
            {
                "$set": {
                    "studio_id": scope.studio_id,
                    "actor_id": scope.actor_id,
                    "idempotency_key": idempotency_key,
                    "target_player_id": player_id,
                    "payload_digest": fingerprint,
                }
            },
            upsert=True,
        )

    def commit(self) -> None:
        super().commit()
        for account in self.accounts.values():
            self.database.accounts.update_one(
                {"account_id": account.account_id},
                {
                    "$set": {
                        "player_id": account.player_id,
                        "deleted_at": account.deleted_at,
                        "email_hash": account.email_hash,
                        "restricted": account.restricted,
                        "session_epoch": account.session_epoch,
                    }
                },
            )
        for player in self.players.values():
            self.database.studio_players.update_one(
                {"player_id": player.player_id},
                {"$set": {"tombstone": player.tombstone, "deleted_at": player.deleted_at}},
                upsert=True,
            )
        for identity in self.identities.values():
            self.database.player_identities.update_one(
                {"identity_id": identity.identity_id},
                {"$set": {"revoked_at": identity.revoked_at}},
            )
        for profile in self.profiles.values():
            self.database.game_profiles.update_one(
                {"profile_id": profile.profile_id},
                {
                    "$set": {
                        "state": profile.state,
                        "entitlements": list(profile.entitlements),
                        "state_version": profile.state_version,
                    }
                },
            )


class MongoTenantDomainRepository(InMemoryTenantRepository):
    def __init__(self, database: Any) -> None:
        super().__init__()
        self.database = database

    def membership_for(self, studio_id: str, account_id: str) -> Membership | None:
        membership = super().membership_for(studio_id, account_id)
        if membership is not None:
            return membership
        document = self.database.studio_memberships.find_one(
            {"studio_id": studio_id, "account_id": account_id, "active": True}
        )
        if document is None:
            return None
        membership = Membership(
            document["membership_id"],
            document["studio_id"],
            document["account_id"],
            MembershipRole(document["role"]),
            document.get("created_at", datetime.now(UTC)),
            bool(document.get("mfa_required", False)),
            bool(document.get("active", True)),
            frozenset(document.get("game_ids", [])),
        )
        self.memberships[membership.membership_id] = membership
        return membership

    def create_studio(self, scope: Any, name: str, slug: str) -> Studio:
        studio = super().create_studio(scope, name, slug)
        self.database.studios.insert_one(
            studio.__dict__
            if hasattr(studio, "__dict__")
            else {
                "studio_id": studio.studio_id,
                "name": studio.name,
                "slug": studio.slug,
                "created_at": studio.created_at,
                "restricted": studio.restricted,
            }
        )
        return studio

    def create_membership(self, scope: Any, account_id: str, role: MembershipRole) -> Membership:
        membership = super().create_membership(scope, account_id, role)
        self.database.studio_memberships.insert_one(
            {
                "membership_id": membership.membership_id,
                "studio_id": membership.studio_id,
                "account_id": membership.account_id,
                "role": membership.role.value,
                "created_at": membership.created_at,
                "active": membership.active,
                "game_ids": list(membership.game_ids),
            }
        )
        return membership

    def change_role(self, scope: Any, membership_id: str, role: MembershipRole) -> Membership:
        membership = super().change_role(scope, membership_id, role)
        self.database.studio_memberships.update_one(
            {"membership_id": membership_id, "studio_id": scope.studio_id},
            {"$set": {"role": role.value}},
        )
        return membership

    def create_service_account(
        self, scope: Any, name: str, scopes: frozenset[str]
    ) -> ServiceAccount:
        account = super().create_service_account(scope, name, scopes)
        self.database.service_accounts.insert_one(
            {
                "service_account_id": account.service_account_id,
                "studio_id": account.studio_id,
                "client_id": account.client_id,
                "name": account.name,
                "scopes": list(account.scopes),
                "created_at": account.created_at,
                "credential_hash": account.credential_hash,
                "revoked_at": None,
            }
        )
        return account

    def revoke_service_account(self, scope: Any, service_account_id: str) -> None:
        account = self.service_accounts.get(service_account_id)
        if account is None:
            document = self.database.service_accounts.find_one(
                {"service_account_id": service_account_id, "studio_id": scope.studio_id}
            )
            if document is None:
                raise KeyError("service_account_not_found")
            account = ServiceAccount(
                document["service_account_id"],
                document["studio_id"],
                document["client_id"],
                document["name"],
                frozenset(document.get("scopes", [])),
                document.get("created_at", datetime.now(UTC)),
                document.get("revoked_at"),
                document.get("credential_hash"),
            )
            self.service_accounts[account.service_account_id] = account
        if account.revoked_at is not None:
            raise KeyError("service_account_not_found")
        if not ({MembershipRole.OWNER, MembershipRole.ADMIN} & set(scope.roles)):
            raise PermissionError("service_account_admin_required")
        now = datetime.now(UTC)
        event = EventEnvelope.create(
            "studio.service_account_revoked.v1",
            "MongoTenantDomainRepository",
            studio_id=scope.studio_id,
            payload={"service_account_id": service_account_id, "action": "revoked"},
        )
        with self.database.client.start_session() as session:
            with session.start_transaction():
                result = self.database.service_accounts.update_one(
                    {
                        "service_account_id": service_account_id,
                        "studio_id": scope.studio_id,
                        "revoked_at": None,
                    },
                    {"$set": {"revoked_at": now}},
                    session=session,
                )
                if result.matched_count != 1:
                    raise KeyError("service_account_not_found")
                self.database.audit_events.insert_one(
                    {
                        "event_id": event.event_id,
                        "action": "service_account.revoked",
                        "studio_id": scope.studio_id,
                        "subject_id": service_account_id,
                        "occurred_at": now,
                    },
                    session=session,
                )
                self.database.event_outbox.insert_one(
                    {
                        "event_id": event.event_id,
                        "event_type": event.event_type,
                        "studio_id": scope.studio_id,
                        "payload": event.payload,
                        "occurred_at": now,
                    },
                    session=session,
                )
        account.revoked_at = now
        self.events.append(event)

    def verify_service_credential(self, service_account_id: str, credential: str) -> bool:
        account = self.service_accounts.get(service_account_id)
        if account is None:
            document = self.database.service_accounts.find_one(
                {"service_account_id": service_account_id}
            )
            if document is None:
                return False
            account = ServiceAccount(
                document["service_account_id"],
                document["studio_id"],
                document["client_id"],
                document["name"],
                frozenset(document.get("scopes", [])),
                document.get("created_at", datetime.now(UTC)),
                document.get("revoked_at"),
                document.get("credential_hash"),
            )
            self.service_accounts[account.service_account_id] = account
        return super().verify_service_credential(service_account_id, credential)
