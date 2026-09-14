from __future__ import annotations

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


class CredentialRotateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    identity_id: str = Field(min_length=1, max_length=128)
    refresh_token: str = Field(min_length=20, max_length=256)
