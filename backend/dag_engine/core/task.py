import backend.dag_engine.core.context as ctx


class Task:

    def __init__(
        self,
        task_id,
        retries=0,
    ):
        self.task_id = task_id
        self.retries = retries

        self.upstream = []
        self.downstream = []

        if ctx.CURRENT_DAG:
            ctx.CURRENT_DAG.add_task(self)

    def __rshift__(self, other):

        self.downstream.append(other)
        other.upstream.append(self)

        return other
