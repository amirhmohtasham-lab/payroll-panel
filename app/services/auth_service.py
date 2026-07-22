"""Auth business logic: login, logout, user CRUD. Single session-based auth scheme."""
from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.core.security import destroy_session, hash_password, verify_password
from app.models.user import User, UserRole


def authenticate(db: DbSession, username: str, password: str) -> User:
    user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="نام کاربری یا رمز نادرست است")
    return user


def logout(db: DbSession, token: str | None) -> None:
    destroy_session(db, token)


def list_users(db: DbSession) -> list[User]:
    return list(db.execute(select(User).order_by(User.username)).scalars())


def create_user(db: DbSession, *, username: str, password: str, name: str, role: UserRole) -> User:
    existing = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="کاربر وجود دارد")
    user = User(username=username, password_hash=hash_password(password), name=name, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(
    db: DbSession,
    user_id: uuid.UUID,
    *,
    password: str | None = None,
    name: str | None = None,
    role: UserRole | None = None,
) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="کاربر یافت نشد")
    if password:
        user.password_hash = hash_password(password)
    if name:
        user.name = name
    if role:
        user.role = role
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: DbSession, user_id: uuid.UUID) -> None:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="کاربر یافت نشد")
    db.delete(user)
    db.commit()
