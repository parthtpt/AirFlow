"""add pools and run timing columns

Revision ID: d1a2b3c4e5f6
Revises: c0ffee10ab01
Create Date: 2026-06-19 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1a2b3c4e5f6'
down_revision: Union[str, Sequence[str], None] = 'c0ffee10ab01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # pools table
    op.create_table(
        'pools',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slots', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_pools_name'), 'pools', ['name'], unique=True)

    # seed the default pool
    op.execute(
        "INSERT INTO pools (id, name, slots, description, created_at, updated_at) "
        "VALUES (gen_random_uuid(), 'default_pool', 16, "
        "'Default pool for tasks with no explicit pool', now(), now())"
    )

    # tasks.pool
    op.add_column(
        'tasks',
        sa.Column('pool', sa.String(length=255), nullable=False,
                  server_default='default_pool'),
    )
    op.create_index(op.f('ix_tasks_pool'), 'tasks', ['pool'])

    # dag_runs timing
    op.add_column('dag_runs',
                  sa.Column('started_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('dag_runs',
                  sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True))

    # task_runs timing
    op.add_column('task_runs',
                  sa.Column('queued_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('task_runs',
                  sa.Column('started_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('task_runs',
                  sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('task_runs', 'finished_at')
    op.drop_column('task_runs', 'started_at')
    op.drop_column('task_runs', 'queued_at')

    op.drop_column('dag_runs', 'finished_at')
    op.drop_column('dag_runs', 'started_at')

    op.drop_index(op.f('ix_tasks_pool'), table_name='tasks')
    op.drop_column('tasks', 'pool')

    op.drop_index(op.f('ix_pools_name'), table_name='pools')
    op.drop_table('pools')
