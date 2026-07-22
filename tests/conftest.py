"""Shared pytest fixtures: isolated in-memory SQLite DB per test, FastAPI TestClient."""
from __future__ import annotations

import os
import tempfile

os.environ.setdefault("APP_SECRET_KEY", "test-secret-key-not-for-production-use-0123456789")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("UPLOAD_DIR", os.path.join(tempfile.gettempdir(), "payroll_panel_test_uploads"))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db import Base, get_db
from app.main import app
from app.models.user import User, UserRole


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def operator_user(db_session):
    user = User(
        username="operator1",
        name="اپراتور",
        password_hash=hash_password("op-pass-123"),
        role=UserRole.OPERATOR,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def accountant_user(db_session):
    user = User(
        username="admin1",
        name="حسابدار",
        password_hash=hash_password("acc-pass-123"),
        role=UserRole.ACCOUNTANT,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def login(client: TestClient, username: str, password: str) -> TestClient:
    res = client.post("/api/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return client
