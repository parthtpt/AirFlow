"""BashOperator: run a bash command/script on the local machine."""

from .base import BaseOperator


class BashOperator(BaseOperator):
    """Run a bash command locally.

        BashOperator(
            task_id="prepare",
            bash_command="mkdir -p /tmp/data && echo ready > /tmp/data/flag",
        )

    For a script file, just call it: bash_command="bash ./scripts/build.sh".
    """

    def __init__(self, task_id, bash_command, cwd=None, retries=0, **kwargs):
        super().__init__(task_id=task_id, retries=retries, **kwargs)
        self.bash_command = bash_command
        self.cwd = cwd

    def execute(self, context):
        return self._run(
            ["bash", "-lc", self.bash_command],
            context,
            cwd=self.cwd,
        )
