"""Worker.

Polls the database for queued DagRuns and executes them with the DagRunner,
persisting per-task state via the DBRecorder. Run as many workers as you like;
each claims runs by flipping their state to "running".
"""

import os
import time

from backend.dag_engine.db_recorder import DBRecorder
from backend.dag_engine.executor import DagRunner
from backend.dag_engine.parser import DAGParser
from backend.database.repositories.dag_repository import DAGRepository
from backend.database.repositories.dag_run_repository import DagRunRepository


class Worker:

    def __init__(self, poll_interval=None):
        self.parser = DAGParser(dag_folder=os.getenv("DAG_FOLDER", "backend/dags"))
        self.dags = DAGRepository()
        self.dag_runs = DagRunRepository()
        self.poll_interval = poll_interval or int(
            os.getenv("WORKER_POLL_INTERVAL", "5")
        )

    def process_once(self):
        queued = self.dag_runs.list_queued()
        if not queued:
            return 0

        parsed = self.parser.parse()

        for run in queued:
            # Claim the run so other workers skip it.
            self.dag_runs.set_state(run.id, "running")

            dag_row = self.dags.get_by_id(run.dag_id)
            dag_obj = parsed.get(dag_row.dag_id) if dag_row else None

            if dag_obj is None:
                print(
                    f"[worker] no DAG definition for run {run.id}; failing",
                    flush=True,
                )
                self.dag_runs.set_state(run.id, "failed")
                continue

            print(f"[worker] executing run {run.id} ({dag_row.dag_id})", flush=True)
            DagRunner(recorder=DBRecorder()).run(
                dag_obj,
                run_id=str(run.id),
                execution_date=run.execution_date,
            )

        return len(queued)

    def run(self):
        print("Worker started", flush=True)
        while True:
            try:
                self.process_once()
            except Exception as exc:  # noqa: BLE001 - keep the loop alive
                print(f"[worker] error: {exc}", flush=True)
            time.sleep(self.poll_interval)


if __name__ == "__main__":
    Worker().run()
