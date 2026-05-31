"""V1 cleanup: drop vector_id from chunks, add file_size_bytes to documents

Revision ID: a1b2c3d4e5f6
Revises: 5f3d9d1c4b7a
Create Date: 2026-05-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "5f3d9d1c4b7a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f("ix_chunks_vector_id"), table_name="chunks")
    op.drop_column("chunks", "vector_id")

    op.add_column(
        "documents",
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("documents", "file_size_bytes")

    op.add_column(
        "chunks",
        sa.Column("vector_id", sa.Uuid(), nullable=True),
    )
    op.create_index(op.f("ix_chunks_vector_id"), "chunks", ["vector_id"], unique=False)
