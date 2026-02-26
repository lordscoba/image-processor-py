"""add base64 action types2

Revision ID: 2e780105bfe1
Revises: 74cea5226e13
Create Date: 2026-02-26 12:30:25.514872

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e780105bfe1'
down_revision: Union[str, Sequence[str], None] = '74cea5226e13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'TO_BASE64';")
    op.execute("ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'FROM_BASE64';")

def downgrade() -> None:
    """Downgrade schema."""
    pass
