"""DAG executor.

Runs the tasks of a single DAG in dependency order, with per-task retries and
log files. Persistence is optional and injected via a `recorder` so the executor
can run completely standalone (e.g. from the CLI) without a database.
"""

import os
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path

from backend.dag_engine.operators.base import BaseOperator

# Task / run states (kept as plain strings; mirror database.models.enums).
QUEUED = "queued"
RUNNING = "running"
SUCCESS = "success"
FAILED = "failed"
SKIPPED = "skipped"


class ExecutionContext:
    """Passed to each operator's execute(); carries metadata + a log sink."""

    def __init__(self, dag_id, run_id, execution_date, task_id, log_path):
        self.dag_id = dag_id
        self.run_id = run_id
        self.execution_date = execution_date
        self.task_id = task_id
        self.log_path = log_path
        self._fh = open(log_path, "a", encoding="utf-8")

    def log(self, line):
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        msg = f"[{stamp}] {line}"
        print(f"({self.task_id}) {line}", flush=True)
        self._fh.write(msg + "\n")
        self._fh.flush()

    def close(self):
        self._fh.close()


class NullRecorder:
    """No-op persistence. Override to record runs/tasks to a database."""

    def run_started(self, dag_id, run_id, execution_date):
        pass

    def task_state(self, run_id, task_id, state, log_path=None):
        pass

    def run_finished(self, run_id, state):
        pass


def topological_order(dag):
    """Return tasks in dependency order (Kahn's algorithm). Raises on a cycle."""
    tasks = dag.tasks
    indegree = {tid: 0 for tid in tasks}
    for task in tasks.values():
        for child in task.downstream:
            indegree[child.task_id] += 1

    queue = sorted(tid for tid, d in indegree.items() if d == 0)
    order = []
    while queue:
        tid = queue.pop(0)
        order.append(tid)
        for child in tasks[tid].downstream:
            indegree[child.task_id] -= 1
            if indegree[child.task_id] == 0:
                queue.append(child.task_id)
        queue.sort()

    if len(order) != len(tasks):
        raise ValueError(f"DAG '{dag.dag_id}' contains a cycle")
    return order


class DagRunner:
    def __init__(self, recorder=None, log_folder=None):
        self.recorder = recorder or NullRecorder()
        self.log_folder = Path(
            log_folder or os.getenv("LOG_FOLDER", "backend/logs")
        )

    def run(self, dag, run_id=None, execution_date=None):
        run_id = run_id or str(uuid.uuid4())
        execution_date = execution_date or datetime.now(timezone.utc)

        run_dir = self.log_folder / dag.dag_id / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        print(f"== Run {run_id} of DAG '{dag.dag_id}' ==", flush=True)
        self.recorder.run_started(dag.dag_id, run_id, execution_date)

        order = topological_order(dag)
        states = {}

        for task_id in order:
            task = dag.tasks[task_id]

            # Skip if any upstream did not succeed.
            failed_parents = [
                p.task_id
                for p in task.upstream
                if states.get(p.task_id) != SUCCESS
            ]
            if failed_parents:
                states[task_id] = SKIPPED
                print(
                    f"-- SKIP {task_id} (upstream not successful: "
                    f"{', '.join(failed_parents)})",
                    flush=True,
                )
                self.recorder.task_state(run_id, task_id, SKIPPED)
                continue

            log_path = str(run_dir / f"{task_id}.log")
            state = self._run_task(task, run_id, dag.dag_id, execution_date, log_path)
            states[task_id] = state
            self.recorder.task_state(run_id, task_id, state, log_path)

        run_state = SUCCESS if all(s == SUCCESS for s in states.values()) else FAILED
        print(f"== Run {run_id} finished: {run_state} ==", flush=True)
        self.recorder.run_finished(run_id, run_state)

        return {"run_id": run_id, "state": run_state, "task_states": states}

    def _run_task(self, task, run_id, dag_id, execution_date, log_path):
        attempts = getattr(task, "retries", 0) + 1

        for attempt in range(1, attempts + 1):
            ctx = ExecutionContext(dag_id, run_id, execution_date, task.task_id, log_path)
            try:
                ctx.log(f"-- RUN {task.task_id} (attempt {attempt}/{attempts})")
                if isinstance(task, BaseOperator):
                    task.execute(ctx)
                else:
                    # A bare Task with no operator behaviour is a no-op marker.
                    ctx.log("No operator behaviour; treating as no-op.")
                ctx.log(f"-- SUCCESS {task.task_id}")
                ctx.close()
                print(f"-- SUCCESS {task.task_id}", flush=True)
                return SUCCESS
            except Exception as exc:  # noqa: BLE001 - record any task failure
                ctx.log(f"-- ERROR {task.task_id}: {exc}")
                ctx.log(traceback.format_exc())
                ctx.close()
                if attempt >= attempts:
                    print(f"-- FAILED {task.task_id}: {exc}", flush=True)
                    return FAILED
                print(f"-- retry {task.task_id} after failure: {exc}", flush=True)

        return FAILED
