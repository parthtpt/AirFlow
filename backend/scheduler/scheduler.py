"""Scheduler.

On each tick it:
  1. parses the DAG folder and syncs DAGs + their tasks into the database, and
  2. for every active DAG whose cron schedule is due, creates a queued DagRun.

Workers (backend.worker.worker) pick up queued runs and execute them.
"""

import os
import time
from datetime import datetime, timezone

from croniter import croniter

from backend.dag_engine.parser import DAGParser
from backend.database.repositories.dag_repository import DAGRepository
from backend.database.repositories.dag_run_repository import DagRunRepository
from backend.database.repositories.task_repository import TaskRepository


class Scheduler:

    def __init__(self, interval=None):
        self.parser = DAGParser(dag_folder=os.getenv("DAG_FOLDER", "backend/dags"))
        self.dags = DAGRepository()
        self.tasks = TaskRepository()
        self.dag_runs = DagRunRepository()
        self.interval = interval or int(os.getenv("SCHEDULER_INTERVAL", "10"))

    def sync_dags(self):
        parsed = self.parser.parse()

        for dag in parsed.values():
            self.dags.upsert(dag_id=dag.dag_id, schedule=dag.schedule)
            row = self.dags.get_by_dag_id(dag.dag_id)
            for task in dag.tasks.values():
                self.tasks.get_or_create(
                    row.id, task.task_id, retries=getattr(task, "retries", 0)
                )

        print(f"Synced {len(parsed)} DAG(s)", flush=True)
        return parsed

    def schedule_runs(self, parsed):
        now = datetime.now(timezone.utc)

        for dag in parsed.values():
            row = self.dags.get_by_dag_id(dag.dag_id)
            if row is None or not row.is_active:
                continue

            due_at = self._due_time(dag.schedule, row.id, now)
            if due_at is not None:
                self.dag_runs.create(
                    row.id, state="queued", execution_date=due_at
                )
                print(
                    f"Queued run for '{dag.dag_id}' @ {due_at.isoformat()}",
                    flush=True,
                )

    def _due_time(self, schedule, dag_uuid, now):
        """Return the execution_date to run for, or None if not due."""
        last = self.dag_runs.last_run_for_dag(dag_uuid)

        # Never run before: trigger an initial run immediately.
        if last is None:
            return now

        base = last.execution_date or last.created_at or now
        if base.tzinfo is None:
            base = base.replace(tzinfo=timezone.utc)

        next_time = croniter(schedule, base).get_next(datetime)
        return next_time if next_time <= now else None

    def run(self):
        while True:
            try:
                parsed = self.sync_dags()
                self.schedule_runs(parsed)
            except Exception as exc:  # noqa: BLE001 - keep the loop alive
                print(f"[scheduler] error: {exc}", flush=True)
            time.sleep(self.interval)


if __name__ == "__main__":
    Scheduler().run()
