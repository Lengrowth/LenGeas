from __future__ import annotations

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
