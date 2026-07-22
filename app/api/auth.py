"""Login/logout/me + user CRUD (accountant-only). Single httpOnly cookie session scheme."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session as DbSession

from app.config import get_settings
from app.core.security import create_session, current_user_dep, destroy_session, require_roles
from app.db import get_db
from app.models.user import User, UserRole
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    MeResponse,
    UserCreateRequest,
    UserOut,
    UserUpdateRequest,
)
from app.services import auth_service

router = APIRouter(tags=["auth"])


@router.post("/api/login", response_model=LoginResponse)
def login(body: LoginRequest, response: Response, db: DbSession = Depends(get_db)):
    settings = get_settings()
    user = auth_service.authenticate(db, body.username, body.password)
    token, expires_at = create_session(db, user)

    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        samesite="strict",
        secure=settings.is_production,
        max_age=settings.session_ttl_hours * 3600,
    )
    redirect = "/operator" if user.role == UserRole.OPERATOR else "/index"
    return LoginResponse(redirect=redirect, role=user.role, name=user.name)


@router.post("/api/logout")
def logout(request: Request, response: Response, db: DbSession = Depends(get_db)):
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    destroy_session(db, token)
    response.delete_cookie(settings.session_cookie_name)
    return {"ok": True}


@router.get("/api/me", response_model=MeResponse)
def me(user: User = Depends(current_user_dep)):
    return MeResponse(username=user.username, role=user.role, name=user.name)


@router.get("/api/users", response_model=list[UserOut])
def list_users(
    db: DbSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ACCOUNTANT)),
):
    return auth_service.list_users(db)


@router.post("/api/users", response_model=UserOut, status_code=201)
def create_user(
    body: UserCreateRequest,
    db: DbSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ACCOUNTANT)),
):
    return auth_service.create_user(
        db, username=body.username, password=body.password, name=body.name, role=body.role
    )


@router.patch("/api/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: uuid.UUID,
    body: UserUpdateRequest,
    db: DbSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ACCOUNTANT)),
):
    return auth_service.update_user(
        db, user_id, password=body.password, name=body.name, role=body.role
    )


@router.delete("/api/users/{user_id}", status_code=204)
def delete_user(
    user_id: uuid.UUID,
    db: DbSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ACCOUNTANT)),
):
    auth_service.delete_user(db, user_id)
