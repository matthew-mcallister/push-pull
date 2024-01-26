"""Make approved_at nullable

Revision ID: d59037bd4ed3
Revises: 1198b577bbd1
Create Date: 2024-01-25 22:09:35.286013

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd59037bd4ed3'
down_revision: Union[str, None] = '1198b577bbd1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('request', 'approved_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)


def downgrade() -> None:
    op.alter_column('request', 'approved_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
