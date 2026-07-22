"""Password hashing, session helpers, and RBAC dependency guards."""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session as DbSession

from app.config import get_settings
from app.db import get_db
from app.models.user import Session as SessionRow
from app.models.user import User, UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def generate_session_token() -> str:
    return secrets.token_hex(32)


def create_session(db: DbSession, user: User) -> tuple[str, datetime]:
    settings = get_settings()
    token = generate_session_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.session_ttl_hours)
    db.add(SessionRow(token=token, user_id=user.id, expires_at=expires_at))
    db.commit()
    return token, expires_at


def destroy_session(db: DbSession, token: str | None) -> None:
    if not token:
        return
    row = db.get(SessionRow, token)
    if row:
        db.delete(row)
        db.commit()


def _as_aware_utc(value: datetime) -> datetime:
    """Normalize a datetime to timezone-aware UTC.

    Some backends (notably SQLite, used in tests) return naive datetimes even for
    `DateTime(timezone=True)` columns, so we can't blindly compare against an
    aware `datetime.now(timezone.utc)`.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def current_user_dep(request: Request, db: DbSession = Depends(get_db)) -> User:
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="لطفاً ابتدا وارد شوید.")
    row = db.get(SessionRow, token)
    if not row or _as_aware_utc(row.expires_at) < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="نشست منقضی شده. دوباره وارد شوید.")
    user = db.get(User, row.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="کاربر یافت نشد.")
    return user


def require_roles(*roles: UserRole):
    def dependency(user: User = Depends(current_user_dep)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="دسترسی ندارید")
        return user

    return dependency
