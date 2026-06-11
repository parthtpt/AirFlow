from backend.dag_engine.core.decorators import dag
from backend.dag_engine.core.task import Task


@dag(
    dag_id="sample_dag",
    schedule="*/5 * * * *",
)
def workflow():

    fetch = Task("fetch")

    validate = Task("validate")

    fetch >> validate
