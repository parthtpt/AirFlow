from sqlalchemy import select

from backend.database.models.task import Task
from backend.database.session import SessionLocal


class TaskRepository:

    def get_or_create(self, dag_uuid, task_id: str, retries: int = 0,
                      timeout_seconds: int = 3600):
        with SessionLocal() as session:
            stmt = select(Task).where(
                Task.dag_id == dag_uuid,
                Task.task_id == task_id,
            )
            task = session.scalar(stmt)

            if task is None:
                task = Task(
                    dag_id=dag_uuid,
                    task_id=task_id,
                    retries=retries,
                    timeout_seconds=timeout_seconds,
                )
                session.add(task)
                session.commit()
                session.refresh(task)
            else:
                task.retries = retries
                session.commit()
                session.refresh(task)

            return task

    def list_by_dag(self, dag_uuid):
        with SessionLocal() as session:
            stmt = select(Task).where(Task.dag_id == dag_uuid).order_by(Task.task_id)
            return list(session.scalars(stmt))
