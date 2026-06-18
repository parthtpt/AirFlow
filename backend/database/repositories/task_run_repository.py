import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from backend.database.models.task import Task
from backend.database.models.task_run import TaskRun
from backend.database.session import SessionLocal

TERMINAL = {"success", "failed", "skipped"}


def _as_uuid(value):
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


def _now():
    return datetime.now(timezone.utc)


class TaskRunRepository:

    def upsert(self, dag_run_id, task_uuid, state: str, log_path=None):
        """Create or update the TaskRun for (dag_run, task), stamping timing."""
        dag_run_id = _as_uuid(dag_run_id)
        now = _now()
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
                    queued_at=now,
                )
                session.add(run)
            else:
                run.state = state
                if log_path:
                    run.log_path = log_path

            if state == "running" and run.started_at is None:
                run.started_at = now
            if state in TERMINAL and run.finished_at is None:
                run.finished_at = now

            session.commit()
            session.refresh(run)
            return run

    def list_by_dag_run(self, dag_run_id):
        """Return per-task rows for a run, including pool and timing."""
        dag_run_id = _as_uuid(dag_run_id)
        with SessionLocal() as session:
            stmt = (
                select(
                    Task.task_id,
                    Task.pool,
                    TaskRun.state,
                    TaskRun.log_path,
                    TaskRun.queued_at,
                    TaskRun.started_at,
                    TaskRun.finished_at,
                )
                .join(Task, Task.id == TaskRun.task_id)
                .where(TaskRun.dag_run_id == dag_run_id)
                .order_by(Task.task_id)
            )
            rows = []
            for r in session.execute(stmt).all():
                started, finished, queued = r[5], r[6], r[4]
                duration = (
                    (finished - started).total_seconds()
                    if started and finished else None
                )
                wait = (
                    (started - queued).total_seconds()
                    if started and queued else None
                )
                rows.append({
                    "task_id": r[0],
                    "pool": r[1],
                    "state": r[2],
                    "log_path": r[3],
                    "queued_at": queued,
                    "started_at": started,
                    "finished_at": finished,
                    "duration": duration,
                    "wait": wait,
                })
            return rows

    def states_for_run(self, dag_run_id):
        """Return {task_id: state} for a run (used by the grid view)."""
        return {r["task_id"]: r["state"] for r in self.list_by_dag_run(dag_run_id)}
