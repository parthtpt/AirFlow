import uuid

from sqlalchemy import select

from backend.database.models.dag import DAG
from backend.database.models.dag_run import DagRun
from backend.database.session import SessionLocal


def _as_uuid(value):
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


class DagRunRepository:

    def create(self, dag_uuid, state="queued", execution_date=None):
        with SessionLocal() as session:
            run = DagRun(
                dag_id=dag_uuid,
                state=state,
                execution_date=execution_date,
            )
            session.add(run)
            session.commit()
            session.refresh(run)
            return run

    def upsert_running(self, run_id, dag_uuid, execution_date=None):
        """Mark an existing run as running, or create it if it doesn't exist."""
        run_id = _as_uuid(run_id)
        with SessionLocal() as session:
            run = session.get(DagRun, run_id)
            if run is None:
                run = DagRun(
                    id=run_id,
                    dag_id=dag_uuid,
                    state="running",
                    execution_date=execution_date,
                )
                session.add(run)
            else:
                run.state = "running"
            session.commit()

    def set_state(self, run_id, state):
        run_id = _as_uuid(run_id)
        with SessionLocal() as session:
            run = session.get(DagRun, run_id)
            if run:
                run.state = state
                session.commit()

    def get(self, run_id):
        run_id = _as_uuid(run_id)
        with SessionLocal() as session:
            return session.get(DagRun, run_id)

    def list_queued(self):
        with SessionLocal() as session:
            stmt = select(DagRun).where(DagRun.state == "queued").order_by(
                DagRun.created_at
            )
            return list(session.scalars(stmt))

    def list_recent(self, limit=50):
        """Return recent runs joined with their dag name, newest first."""
        with SessionLocal() as session:
            stmt = (
                select(
                    DagRun.id,
                    DAG.dag_id,
                    DagRun.state,
                    DagRun.execution_date,
                    DagRun.created_at,
                )
                .join(DAG, DAG.id == DagRun.dag_id)
                .order_by(DagRun.created_at.desc())
                .limit(limit)
            )
            return [
                {
                    "id": str(row[0]),
                    "dag_id": row[1],
                    "state": row[2],
                    "execution_date": row[3],
                    "created_at": row[4],
                }
                for row in session.execute(stmt).all()
            ]

    def list_by_dag(self, dag_uuid, limit=50):
        with SessionLocal() as session:
            stmt = (
                select(
                    DagRun.id,
                    DagRun.state,
                    DagRun.execution_date,
                    DagRun.created_at,
                )
                .where(DagRun.dag_id == dag_uuid)
                .order_by(DagRun.created_at.desc())
                .limit(limit)
            )
            return [
                {
                    "id": str(row[0]),
                    "state": row[1],
                    "execution_date": row[2],
                    "created_at": row[3],
                }
                for row in session.execute(stmt).all()
            ]

    def last_run_for_dag(self, dag_uuid):
        with SessionLocal() as session:
            stmt = (
                select(DagRun)
                .where(DagRun.dag_id == dag_uuid)
                .order_by(DagRun.created_at.desc())
                .limit(1)
            )
            return session.scalar(stmt)
