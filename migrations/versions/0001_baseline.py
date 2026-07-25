"""baseline schema: users, sessions, uploads, audit_issues

Revision ID: 0001
Revises:
Create Date: 2026-07-22

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE user_role AS ENUM ('OPERATOR', 'ACCOUNTANT')")
    op.execute("CREATE TYPE upload_type AS ENUM ('PAYROLL', 'FERTILIZER')")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", postgresql.ENUM("OPERATOR", "ACCOUNTANT", name="user_role", create_type=False), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_username", "users", ["username"])

    op.create_table(
        "sessions",
        sa.Column("token", sa.String(64), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "uploads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("upload_type", postgresql.ENUM("PAYROLL", "FERTILIZER", name="upload_type", create_type=False), nullable=False),
        sa.Column("month_key", sa.String(16), nullable=False),
        sa.Column("month_label", sa.String(64), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("stored_path", sa.String(500), nullable=False),
        sa.Column("highlight_path", sa.String(500), nullable=True),
        sa.Column("drive_file_id", sa.String(128), nullable=True),
        sa.Column("drive_error", sa.String(500), nullable=True),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("warn_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("crop", sa.String(128), nullable=True),
        sa.Column("season", sa.String(64), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("fertilizer_count", sa.Integer(), nullable=True),
        sa.Column("audit_summary", sa.JSON(), nullable=True),
        sa.Column(
            "uploaded_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("upload_type", "month_key", name="uq_upload_type_month"),
    )
    op.create_index("ix_uploads_month_key", "uploads", ["month_key"])
    op.create_index("ix_uploads_sha256", "uploads", ["sha256"])

    op.create_table(
        "audit_issues",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "upload_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("uploads.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("sheet", sa.String(128), nullable=True),
        sa.Column("message", sa.String(1000), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("audit_issues")
    op.drop_table("uploads")
    op.drop_table("sessions")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS upload_type")
    op.execute("DROP TYPE IF EXISTS user_role")
