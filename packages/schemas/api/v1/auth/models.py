from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GuestCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    turnstile_proof: str = Field(min_length=1, max_length=4096)
    device_public_key: str = Field(min_length=32, max_length=128)


class CredentialResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    player_id: str
    identity_id: str
    refresh_token: str
    expires_at: str


class IdentityLinkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: str = Field(min_length=1, max_length=32)
    subject: str = Field(min_length=1, max_length=256)
    provider_proof: str | None = Field(default=None, min_length=1, max_length=4096)


class CredentialRotateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    identity_id: str = Field(min_length=1, max_length=128)
    refresh_token: str = Field(min_length=20, max_length=256)


class IdentityLinkResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    identity_id: str
    player_id: str


class RefreshTokenResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    refresh_token: str


class AccountResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    account_id: str
    created_at: datetime
    email_hash: str | None = None
    deleted_at: datetime | None = None
    restricted: bool = False
    session_epoch: int = 0
    player_id: str | None = None
