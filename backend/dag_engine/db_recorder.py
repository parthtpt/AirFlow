"""DB-backed recorder: persists run/task state to Postgres as a DAG executes.

Plugs into DagRunner via the recorder interface (see executor.NullRecorder).
"""

from backend.database.repositories.dag_repository import DAGRepository
from backend.database.repositories.dag_run_repository import DagRunRepository
from backend.database.repositories.task_repository import TaskRepository
from backend.database.repositories.task_run_repository import TaskRunRepository


class DBRecorder:

    def __init__(self):
        self.dags = DAGRepository()
        self.dag_runs = DagRunRepository()
        self.tasks = TaskRepository()
        self.task_runs = TaskRunRepository()
        self._dag_uuid = None

    def run_started(self, dag_id, run_id, execution_date):
        dag = self.dags.get_by_dag_id(dag_id)
        if dag is None:
            raise ValueError(
                f"DAG '{dag_id}' is not registered in the database. "
                "Run the scheduler (or sync) first."
            )
        self._dag_uuid = dag.id
        self.dag_runs.upsert_running(run_id, dag.id, execution_date)

    def task_state(self, run_id, task_id, state, log_path=None):
        task = self.tasks.get_or_create(self._dag_uuid, task_id)
        self.task_runs.upsert(run_id, task.id, state, log_path)

    def run_finished(self, run_id, state):
        self.dag_runs.set_state(run_id, state)
