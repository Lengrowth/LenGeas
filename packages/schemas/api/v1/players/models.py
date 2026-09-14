from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MergePreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_player_id: str = Field(min_length=1, max_length=64)
    target_player_id: str = Field(min_length=1, max_length=64)
    source_credential: str | None = Field(default=None, min_length=20, max_length=256)
    target_credential: str | None = Field(default=None, min_length=20, max_length=256)


class MergeCommitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    preview_id: str = Field(min_length=1, max_length=128)
    choices: dict[str, str] = Field(default_factory=dict, max_length=100)
    idempotency_key: str = Field(min_length=8, max_length=128)
    source_credential: str | None = Field(default=None, min_length=20, max_length=256)
    target_credential: str | None = Field(default=None, min_length=20, max_length=256)


class PrivacyRequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation: str = Field(pattern="^(export|correction|deletion|restriction|legal_hold)$")


class MergeCollisionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    game_id: str
    source_profile_id: str
    target_profile_id: str
    choices: tuple[str, ...]


class MergePreviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    preview_id: str
    source_player_id: str
    target_player_id: str
    collisions: tuple[MergeCollisionResponse, ...]
    entitlements: tuple[str, ...]
    expires_at: datetime
    studio_id: str
    game_id: str | None = None


class MergeCommitResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    player_id: str


class PrivacyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    request_id: str
    account_id: str
    operation: str
    requested_at: datetime
    status: str
    legal_hold: bool = False
    studio_id: str | None = None
