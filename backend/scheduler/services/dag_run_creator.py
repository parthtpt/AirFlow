from backend.database.repositories.dag_run_repository import DagRunRepository
from backend.database.repositories.dag_repository import DAGRepository


class DagRunCreator:

    def __init__(self):

        self.dag_repo = DAGRepository()
        self.run_repo = DagRunRepository()

    def create_run(self, dag_id: str):

        dag = self.dag_repo.get_by_dag_id(
            dag_id
        )

        if dag is None:
            return

        run = self.run_repo.create(
            dag.id
        )

        print(
            f"Created DagRun {run.id}"
        )

        return run
