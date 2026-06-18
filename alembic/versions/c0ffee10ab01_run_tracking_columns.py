"""add run tracking columns (dag_run_id, log_path, execution_date)

Revision ID: c0ffee10ab01
Revises: 3a31cec57b0c
Create Date: 2026-06-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c0ffee10ab01'
down_revision: Union[str, Sequence[str], None] = '3a31cec57b0c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'dag_runs',
        sa.Column('execution_date', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        op.f('ix_dag_runs_execution_date'), 'dag_runs', ['execution_date'],
    )

    op.add_column(
        'task_runs',
        sa.Column('dag_run_id', sa.UUID(), nullable=True),
    )
    op.add_column(
        'task_runs',
        sa.Column('log_path', sa.Text(), nullable=True),
    )
    op.create_index(
        op.f('ix_task_runs_dag_run_id'), 'task_runs', ['dag_run_id'],
    )
    op.create_foreign_key(
        'fk_task_runs_dag_run_id',
        'task_runs', 'dag_runs',
        ['dag_run_id'], ['id'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_task_runs_dag_run_id', 'task_runs', type_='foreignkey')
    op.drop_index(op.f('ix_task_runs_dag_run_id'), table_name='task_runs')
    op.drop_column('task_runs', 'log_path')
    op.drop_column('task_runs', 'dag_run_id')

    op.drop_index(op.f('ix_dag_runs_execution_date'), table_name='dag_runs')
    op.drop_column('dag_runs', 'execution_date')
