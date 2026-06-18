from backend.database.repositories.dag_repository import DAGRepository
from backend.database.repositories.dag_run_repository import DagRunRepository

dag_repo = DAGRepository()
run_repo = DagRunRepository()

dag = dag_repo.get_by_dag_id("sample_dag")

print("dag:", dag.id)

run = run_repo.create(dag.id)

print("run:", run.id)
