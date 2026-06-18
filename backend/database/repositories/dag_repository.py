import uuid

from sqlalchemy import select

from backend.database.models.dag import DAG
from backend.database.session import SessionLocal


class DAGRepository:

    def get_by_dag_id(self, dag_id: str):

        with SessionLocal() as session:

            stmt = select(DAG).where(
                DAG.dag_id == dag_id
            )

            return session.scalar(stmt)

    def get_by_id(self, dag_uuid):

        if not isinstance(dag_uuid, uuid.UUID):
            dag_uuid = uuid.UUID(str(dag_uuid))

        with SessionLocal() as session:
            return session.get(DAG, dag_uuid)

    def list_all(self):

        with SessionLocal() as session:

            stmt = select(DAG).order_by(DAG.dag_id)

            return list(session.scalars(stmt))

    def upsert(
        self,
        dag_id: str,
        schedule: str,
    ):

        with SessionLocal() as session:

            stmt = select(DAG).where(
                DAG.dag_id == dag_id
            )

            dag = session.scalar(stmt)

            if dag is None:

                dag = DAG(
                    dag_id=dag_id,
                    schedule=schedule,
                )

                session.add(dag)

                print(
                    f"Created DAG: {dag_id}"
                )

            else:

                dag.schedule = schedule

                print(
                    f"Updated DAG: {dag_id}"
                )

            session.commit()
