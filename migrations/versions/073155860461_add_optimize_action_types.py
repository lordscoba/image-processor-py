"""add optimize action types

Revision ID: 073155860461
Revises: 2e780105bfe1
Create Date: 2026-02-26 13:01:26.756584

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '073155860461'
down_revision: Union[str, Sequence[str], None] = '2e780105bfe1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'OPTIMIZE_TWITTER';")
    op.execute("ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'OPTIMIZE_WHATSAPP';")
    op.execute("ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'OPTIMIZE_WEB';")
    op.execute("ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'OPTIMIZE_CUSTOM';")
    op.execute("ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'OPTIMIZE_INSTAGRAM';")
    op.execute("ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'OPTIMIZE_YOUTUBE';")
    op.execute("ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'OPTIMIZE_SEO';")


def downgrade() -> None:
    """Downgrade schema."""
    pass
