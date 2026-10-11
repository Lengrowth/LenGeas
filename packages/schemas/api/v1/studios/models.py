from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StudioCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)
    slug: str = Field(pattern="^[a-z][a-z0-9-]{2,63}$")


class MembershipRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account_id: str = Field(min_length=1, max_length=64)
    role: str = Field(pattern="^(admin|developer|designer|writer|analyst|support|viewer|ai_agent)$")


class ServiceAccountRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)
    scopes: list[str] = Field(min_length=1, max_length=50)


class InvitationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=3, max_length=320)
    role: str = Field(pattern="^(admin|developer|designer|writer|analyst|support|viewer|ai_agent)$")


class RoleChangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    membership_id: str = Field(min_length=1, max_length=128)
    role: str = Field(pattern="^(admin|developer|designer|writer|analyst|support|viewer|ai_agent)$")


class StudioResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    studio_id: str
    name: str
    slug: str
    created_at: datetime
    restricted: bool = False


class MembershipResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    membership_id: str
    studio_id: str
    account_id: str
    role: str
    created_at: datetime
    mfa_required: bool = False
    active: bool = True
    game_ids: frozenset[str] = frozenset()


class ServiceAccountResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    service_account_id: str
    client_id: str
    credential: str | None = None
    scopes: list[str]


class InvitationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    invitation_id: str
    studio_id: str
    email_hash: str
    role: str
    expires_at: datetime
    created_at: datetime
    accepted_at: datetime | None = None
