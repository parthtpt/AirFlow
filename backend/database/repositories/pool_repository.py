from sqlalchemy import func, select

from backend.database.models.pool import Pool
from backend.database.models.task import Task
from backend.database.models.task_run import TaskRun
from backend.database.session import SessionLocal


class PoolRepository:

    def ensure_default(self, slots=16):
        with SessionLocal() as session:
            existing = session.scalar(select(Pool).where(Pool.name == "default_pool"))
            if existing is None:
                session.add(Pool(
                    name="default_pool",
                    slots=slots,
                    description="Default pool for tasks with no explicit pool",
                ))
                session.commit()

    def get_by_name(self, name):
        with SessionLocal() as session:
            return session.scalar(select(Pool).where(Pool.name == name))

    def create(self, name, slots, description=None):
        with SessionLocal() as session:
            pool = session.scalar(select(Pool).where(Pool.name == name))
            if pool is None:
                pool = Pool(name=name, slots=slots, description=description)
                session.add(pool)
            else:
                pool.slots = slots
                pool.description = description
            session.commit()
            session.refresh(pool)
            return pool

    def running_count(self, pool_name):
        """Number of task_runs currently running in a pool."""
        with SessionLocal() as session:
            stmt = (
                select(func.count(TaskRun.id))
                .join(Task, Task.id == TaskRun.task_id)
                .where(Task.pool == pool_name, TaskRun.state == "running")
            )
            return session.scalar(stmt) or 0

    def list_with_usage(self):
        """Return pools with used/available slot counts."""
        with SessionLocal() as session:
            pools = list(session.scalars(select(Pool).order_by(Pool.name)))

            # running task_runs grouped by pool
            usage_stmt = (
                select(Task.pool, func.count(TaskRun.id))
                .join(Task, Task.id == TaskRun.task_id)
                .where(TaskRun.state == "running")
                .group_by(Task.pool)
            )
            used = {row[0]: row[1] for row in session.execute(usage_stmt).all()}

            result = []
            for p in pools:
                u = used.get(p.name, 0)
                result.append({
                    "name": p.name,
                    "slots": p.slots,
                    "description": p.description,
                    "used": u,
                    "available": max(p.slots - u, 0),
                })
            return result
