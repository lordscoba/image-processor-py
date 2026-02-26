"""add base64 action types

Revision ID: 74cea5226e13
Revises: 
Create Date: 2026-02-26 12:21:26.172768

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '74cea5226e13'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'TO_BASE64';")
    op.execute("ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'FROM_BASE64';")


def downgrade() -> None:
    """Downgrade schema."""
    pass
