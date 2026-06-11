from .context import DAG_REGISTRY


class DAG:

    def __init__(
        self,
        dag_id: str,
        schedule: str,
    ):
        self.dag_id = dag_id
        self.schedule = schedule
        self.tasks = {}

        DAG_REGISTRY[dag_id] = self

    def add_task(self, task):
        self.tasks[task.task_id] = task
