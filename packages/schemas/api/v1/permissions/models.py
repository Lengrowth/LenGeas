from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PolicyDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str = Field(min_length=1, max_length=64)
    resource_type: str = Field(min_length=1, max_length=64)
    resource_id: str | None = Field(default=None, max_length=128)
    game_id: str | None = Field(default=None, max_length=128)
