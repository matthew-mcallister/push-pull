"""Initial revision

Revision ID: b6fd054b537f
Revises:
Create Date: 2024-01-20 19:00:37.714686

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b6fd054b537f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'block',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'teacher',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('email', sa.String(length=60), nullable=False),
        sa.Column('active', sa.Boolean(), server_default='true', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_table(
        'student',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(length=60), nullable=False),
        sa.Column('last_name', sa.String(length=60), nullable=False),
        sa.Column('home_teacher_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['home_teacher_id'], ['teacher.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'request',
        sa.Column('block_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('destination_teacher_id', sa.Integer(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=False),
        sa.Column('requester_code', sa.Enum('src', 'dst', 'auto', name='requester'), nullable=False),
        sa.Column('approved_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['block_id'], ['block.id'], ),
        sa.ForeignKeyConstraint(['destination_teacher_id'], ['teacher.id'], ),
        sa.ForeignKeyConstraint(['student_id'], ['student.id'], ),
        sa.PrimaryKeyConstraint('block_id', 'student_id')
    )


def downgrade() -> None:
    op.drop_table('request')
    op.drop_table('student')
    op.drop_table('teacher')
    op.drop_table('block')
