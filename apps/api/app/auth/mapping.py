"""Map verified provider subjects to internal accounts."""

from __future__ import annotations

from packages.domain.identity.models import Account, IdentityKind
from packages.domain.identity.repository import InMemoryIdentityRepository


class InternalAccountMapper:
    def __init__(self, repository: InMemoryIdentityRepository) -> None:
        self.repository = repository

    def map_subject(self, subject: str) -> Account:
        identity = self.repository.identity_for_provider("supabase", subject)
        if identity is not None:
            account = self.repository.accounts.get(identity.account_id or identity.player_id)
            if account is None or identity.revoked_at is not None or account.deleted_at is not None:
                raise KeyError("mapped_account_missing")
            account.player_id = identity.player_id
            return account
        account = self.repository.create_account()
        player = self.repository.create_player()
        account.player_id = player.player_id
        self.repository.link_identity(
            player.player_id,
            IdentityKind.SUPABASE,
            "supabase",
            subject,
            account_id=account.account_id,
        )
        return account
