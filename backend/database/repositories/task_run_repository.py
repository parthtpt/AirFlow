import uuid

from sqlalchemy import select

from backend.database.models.task import Task
from backend.database.models.task_run import TaskRun
from backend.database.session import SessionLocal


def _as_uuid(value):
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


class TaskRunRepository:

    def upsert(self, dag_run_id, task_uuid, state: str, log_path=None):
        """Create or update the TaskRun for (dag_run, task)."""
        dag_run_id = _as_uuid(dag_run_id)
        with SessionLocal() as session:
            stmt = select(TaskRun).where(
                TaskRun.dag_run_id == dag_run_id,
                TaskRun.task_id == task_uuid,
            )
            run = session.scalar(stmt)

            if run is None:
                run = TaskRun(
                    dag_run_id=dag_run_id,
                    task_id=task_uuid,
                    state=state,
                    log_path=log_path,
                )
                session.add(run)
            else:
                run.state = state
                if log_path:
                    run.log_path = log_path

            session.commit()
            session.refresh(run)
            return run

    def list_by_dag_run(self, dag_run_id):
        """Return [(task_name, state, log_path), ...] for a run."""
        dag_run_id = _as_uuid(dag_run_id)
        with SessionLocal() as session:
            stmt = (
                select(Task.task_id, TaskRun.state, TaskRun.log_path)
                .join(Task, Task.id == TaskRun.task_id)
                .where(TaskRun.dag_run_id == dag_run_id)
                .order_by(Task.task_id)
            )
            return [
                {"task_id": row[0], "state": row[1], "log_path": row[2]}
                for row in session.execute(stmt).all()
            ]
