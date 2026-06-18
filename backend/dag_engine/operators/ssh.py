"""SSHOperator: run a command on a remote host over SSH.

Works for any remote command - a bash one-liner, a shell script, or a remote
Python script:

    # run a bash script on prod
    SSHOperator(task_id="deploy", conn_id="prod",
                command="bash /opt/app/deploy.sh")

    # run a python script on a remote box
    SSHOperator(task_id="train", conn_id="remote",
                command="python3 /opt/jobs/train.py --epochs 5")

The connection (host/user/key) is resolved from env vars - see connections.py.
"""

from backend.dag_engine.connections import get_connection

from .base import BaseOperator


class SSHOperator(BaseOperator):

    def __init__(self, task_id, conn_id, command, retries=0, **kwargs):
        super().__init__(task_id=task_id, retries=retries, **kwargs)
        self.conn_id = conn_id
        self.command = command

    def execute(self, context):
        conn = get_connection(self.conn_id)

        if conn.is_local:
            # "local" connection => just run it here.
            return self._run(["bash", "-lc", self.command], context)

        cmd = ["ssh", *conn.ssh_options(), conn.target, self.command]
        context.log(f"Running on {self.conn_id} ({conn.target})")
        return self._run(cmd, context)
