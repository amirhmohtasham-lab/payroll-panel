"""greenhouse_runs table

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-01
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "greenhouse_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("temp_filename", sa.String(255), nullable=False),
        sa.Column("humi_filename", sa.String(255), nullable=False),
        sa.Column("temp_path", sa.String(500), nullable=False),
        sa.Column("humi_path", sa.String(500), nullable=False),
        sa.Column("output_dir", sa.String(500), nullable=False),
        sa.Column("zip_path", sa.String(500), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("metrics", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("tables", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_greenhouse_runs_uploaded_at", "greenhouse_runs", ["uploaded_at"])


def downgrade() -> None:
    op.drop_index("ix_greenhouse_runs_uploaded_at", table_name="greenhouse_runs")
    op.drop_table("greenhouse_runs")
