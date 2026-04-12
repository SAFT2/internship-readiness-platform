"""add assessment resume metadata

Revision ID: 20260328_000002
Revises: 20260328_000001
Create Date: 2026-03-28 13:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260328_000002"
down_revision: Union[str, Sequence[str], None] = "20260328_000001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = {column["name"] for column in inspector.get_columns("assessments")}

    if "source_type" not in existing:
        op.add_column(
            "assessments",
            sa.Column("source_type", sa.String(length=20), nullable=False, server_default="profile"),
        )
    if "resume_filename" not in existing:
        op.add_column("assessments", sa.Column("resume_filename", sa.String(length=255), nullable=True))
    if "resume_sha256" not in existing:
        op.add_column("assessments", sa.Column("resume_sha256", sa.String(length=64), nullable=True))
    if "resume_uri" not in existing:
        op.add_column("assessments", sa.Column("resume_uri", sa.String(length=500), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = {column["name"] for column in inspector.get_columns("assessments")}

    if "resume_uri" in existing:
        op.drop_column("assessments", "resume_uri")
    if "resume_sha256" in existing:
        op.drop_column("assessments", "resume_sha256")
    if "resume_filename" in existing:
        op.drop_column("assessments", "resume_filename")
    if "source_type" in existing:
        op.drop_column("assessments", "source_type")
