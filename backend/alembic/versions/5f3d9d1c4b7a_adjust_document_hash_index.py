"""Adjust document hash index for session-scoped dedupe

Revision ID: 5f3d9d1c4b7a
Revises: 92c0a144db29
Create Date: 2026-05-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5f3d9d1c4b7a"
down_revision: Union[str, Sequence[str], None] = "92c0a144db29"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_index(op.f("ix_documents_file_hash"), table_name="documents")
    op.create_index(
        "ix_documents_file_hash_session_id",
        "documents",
        ["file_hash", "session_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_documents_file_hash_session_id", table_name="documents")
    op.create_index(op.f("ix_documents_file_hash"), "documents", ["file_hash"], unique=True)
