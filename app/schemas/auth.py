from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from app.models.user import UserRole


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class LoginResponse(BaseModel):
    ok: bool = True
    redirect: str
    role: UserRole
    name: str


class MeResponse(BaseModel):
    username: str
    role: UserRole
    name: str


class UserOut(BaseModel):
    id: uuid.UUID
    username: str
    name: str
    role: UserRole

    model_config = {"from_attributes": True}


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=6, max_length=256)
    name: str = Field(min_length=1, max_length=128)
    role: UserRole = UserRole.OPERATOR


class UserUpdateRequest(BaseModel):
    password: str | None = Field(default=None, min_length=6, max_length=256)
    name: str | None = Field(default=None, min_length=1, max_length=128)
    role: UserRole | None = None
