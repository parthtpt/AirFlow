"""A tiny, fully-local DAG - runs with no remote configuration.

    python -m backend.cli run hello_local
"""

from backend.dag_engine.core.decorators import dag
from backend.dag_engine.operators import BashOperator, PythonOperator


def say_hi(context):
    context.log("Hello from a Python task!")
    return "ok"


@dag(dag_id="hello_local", schedule="*/10 * * * *")
def pipeline():
    greet = BashOperator(
        task_id="greet",
        bash_command="echo 'Hello from bash' && date",
    )
    finish = PythonOperator(
        task_id="finish",
        python_callable=say_hi,
    )
    greet >> finish
