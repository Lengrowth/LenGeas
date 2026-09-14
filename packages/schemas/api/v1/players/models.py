from __future__ import annotations

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
