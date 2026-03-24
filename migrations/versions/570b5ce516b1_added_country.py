"""added country

Revision ID: 570b5ce516b1
Revises: f9ed3ad82db1
Create Date: 2026-03-24 15:34:08.936651

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '570b5ce516b1'
down_revision: Union[str, Sequence[str], None] = 'f9ed3ad82db1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usage_logs",
        sa.Column("country", sa.String(length=40), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("usage_logs", "country")
