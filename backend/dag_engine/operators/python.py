"""PythonOperator: run Python locally - either a callable or a script file."""

import inspect
import sys

from .base import BaseOperator


class PythonOperator(BaseOperator):
    """Run Python on the local machine.

    Either pass a callable:

        def transform(**context):
            ...
        PythonOperator(task_id="transform", python_callable=transform)

    or a script file (run with the current interpreter):

        PythonOperator(task_id="ingest", python_script="scripts/ingest.py",
                       script_args=["--date", "today"])
    """

    def __init__(
        self,
        task_id,
        python_callable=None,
        op_args=None,
        op_kwargs=None,
        python_script=None,
        script_args=None,
        retries=0,
        **kwargs,
    ):
        super().__init__(task_id=task_id, retries=retries, **kwargs)
        if not python_callable and not python_script:
            raise ValueError(
                "PythonOperator needs either python_callable or python_script"
            )
        self.python_callable = python_callable
        self.op_args = op_args or []
        self.op_kwargs = op_kwargs or {}
        self.python_script = python_script
        self.script_args = script_args or []

    def execute(self, context):
        if self.python_callable:
            context.log(f"Calling {self.python_callable.__name__}()")
            call_kwargs = dict(self.op_kwargs)
            # Only pass `context` if the callable can accept it.
            sig = inspect.signature(self.python_callable)
            accepts_context = "context" in sig.parameters or any(
                p.kind == inspect.Parameter.VAR_KEYWORD
                for p in sig.parameters.values()
            )
            if accepts_context:
                call_kwargs["context"] = context
            result = self.python_callable(*self.op_args, **call_kwargs)
            context.log(f"Returned: {result!r}")
            return result

        cmd = [sys.executable, self.python_script, *self.script_args]
        return self._run(cmd, context)
