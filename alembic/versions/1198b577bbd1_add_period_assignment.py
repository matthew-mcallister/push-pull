"""Add period, assignment

Revision ID: 1198b577bbd1
Revises: b6fd054b537f
Create Date: 2024-01-22 00:57:00.179152

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1198b577bbd1'
down_revision: Union[str, None] = 'b6fd054b537f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'period',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_period'))
    )
    op.create_table(
        'assignment',
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('period_id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['period_id'], ['period.id'], name=op.f('fk_assignment_period_id_period')),
        sa.ForeignKeyConstraint(['student_id'], ['student.id'], name=op.f('fk_assignment_student_id_student')),
        sa.ForeignKeyConstraint(['teacher_id'], ['teacher.id'], name=op.f('fk_assignment_teacher_id_teacher')),
        sa.PrimaryKeyConstraint('student_id', 'period_id', name=op.f('pk_assignment'))
    )
    op.add_column('block', sa.Column('day', sa.Date(), nullable=False))
    op.add_column('block', sa.Column('period_id', sa.Integer(), nullable=False))
    op.create_unique_constraint(op.f('uq_block_day'), 'block', ['day', 'period_id'])
    op.create_foreign_key(op.f('fk_block_period_id_period'), 'block', 'period', ['period_id'], ['id'])
    op.drop_column('block', 'start_time')
    op.drop_constraint('student_home_teacher_id_fkey', 'student', type_='foreignkey')
    op.drop_column('student', 'home_teacher_id')
    op.drop_constraint('teacher_email_key', 'teacher', type_='unique')
    op.create_unique_constraint(op.f('uq_teacher_email'), 'teacher', ['email'])


def downgrade() -> None:
    op.drop_constraint(op.f('uq_teacher_email'), 'teacher', type_='unique')
    op.create_unique_constraint('teacher_email_key', 'teacher', ['email'])
    op.add_column('student', sa.Column('home_teacher_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.create_foreign_key('student_home_teacher_id_fkey', 'student', 'teacher', ['home_teacher_id'], ['id'])
    op.add_column('block', sa.Column('start_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=False))
    op.drop_constraint(op.f('fk_block_period_id_period'), 'block', type_='foreignkey')
    op.drop_constraint(op.f('uq_block_day'), 'block', type_='unique')
    op.drop_column('block', 'period_id')
    op.drop_column('block', 'day')
    op.drop_table('assignment')
    op.drop_table('period')
