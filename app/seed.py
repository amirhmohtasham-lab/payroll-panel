"""Seed default operator/accountant roles on first run. Replaces users.json auto-seed.

Run with: python -m app.seed
Idempotent: skips users that already exist. Reads initial passwords from env vars
so no plaintext credentials are hardcoded in source.
"""
from __future__ import annotations

import os
import sys

from app.core.security import hash_password
from app.db import SessionLocal
from app.models.user import User, UserRole


def seed() -> None:
    db = SessionLocal()
    try:
        seeds = [
            (
                os.environ.get("SEED_OPERATOR_USERNAME", "operator1"),
                os.environ.get("SEED_OPERATOR_PASSWORD"),
                os.environ.get("SEED_OPERATOR_NAME", "اپراتور"),
                UserRole.OPERATOR,
            ),
            (
                os.environ.get("SEED_ACCOUNTANT_USERNAME", "admin1"),
                os.environ.get("SEED_ACCOUNTANT_PASSWORD"),
                os.environ.get("SEED_ACCOUNTANT_NAME", "حسابدار"),
                UserRole.ACCOUNTANT,
            ),
        ]
        for username, password, name, role in seeds:
            existing = db.query(User).filter(User.username == username).one_or_none()
            if existing:
                print(f"[seed] user '{username}' already exists, skipping")
                continue
            if not password:
                print(
                    f"[seed] SKIP '{username}': set SEED_{role.value.upper()}_PASSWORD env var "
                    "to create this user on first run",
                    file=sys.stderr,
                )
                continue
            user = User(
                username=username,
                name=name,
                password_hash=hash_password(password),
                role=role,
            )
            db.add(user)
            db.commit()
            print(f"[seed] created user '{username}' with role '{role.value}'")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
