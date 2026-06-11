import backend.dag_engine.core.context as ctx

from .dag import DAG


def dag(
    dag_id: str,
    schedule: str,
):
    def wrapper(func):

        workflow = DAG(
            dag_id=dag_id,
            schedule=schedule,
        )

        ctx.CURRENT_DAG = workflow

        func()

        ctx.CURRENT_DAG = None

        return workflow

    return wrapper
