"""BaseOperator: a Task that knows how to execute itself."""

import subprocess

from backend.dag_engine.core.task import Task


class OperatorError(Exception):
    """Raised when an operator's command exits non-zero."""


class BaseOperator(Task):
    """A task with an execute() method.

    Subclasses implement execute(context). `context` is supplied by the executor
    and exposes a `.log(line)` method plus run metadata (dag_id, run_id, ...).
    Operators should raise on failure; the executor handles retries.
    """

    def __init__(self, task_id, retries=0, pool="default_pool", **kwargs):
        super().__init__(task_id=task_id, retries=retries)
        self.pool = pool
        self.kwargs = kwargs

    def execute(self, context):  # pragma: no cover - abstract
        raise NotImplementedError(
            f"{type(self).__name__} must implement execute(context)"
        )

    # -- shared helpers -----------------------------------------------------

    def _run(self, cmd, context, cwd=None, env=None):
        """Run a subprocess, streaming combined output into the task log.

        `cmd` is a list of args (no shell). Raises OperatorError on non-zero exit.
        Returns the full captured output as a string.
        """
        context.log(f"$ {' '.join(cmd)}")

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=cwd,
            env=env,
        )

        output_lines = []
        for line in proc.stdout:
            line = line.rstrip("\n")
            output_lines.append(line)
            context.log(line)

        returncode = proc.wait()

        if returncode != 0:
            raise OperatorError(
                f"Command exited with code {returncode}: {' '.join(cmd)}"
            )

        return "\n".join(output_lines)
