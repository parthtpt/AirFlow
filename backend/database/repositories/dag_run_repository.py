from backend.database.models.dag_run import DagRun
from backend.database.session import SessionLocal


class DagRunRepository:

    def create(self, dag_uuid):

        with SessionLocal() as session:

            run = DagRun(
                dag_id=dag_uuid,
                state="queued",
            )

            session.add(run)

            session.commit()
            session.refresh(run)

            return run
