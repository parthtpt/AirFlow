"""RsyncOperator: sync files between local and a remote host.

    # push local -> prod
    RsyncOperator(task_id="upload", conn_id="prod",
                  direction="push", src="./build/", dest="/opt/app/")

    # pull prod -> local
    RsyncOperator(task_id="download", conn_id="prod",
                  direction="pull", src="/opt/app/output/", dest="./output/")

`src`/`dest` are paths on the *source*/*destination* side respectively.
"""

from backend.dag_engine.connections import get_connection

from .base import BaseOperator

PUSH = "push"
PULL = "pull"


class RsyncOperator(BaseOperator):

    def __init__(
        self,
        task_id,
        conn_id,
        src,
        dest,
        direction=PUSH,
        extra_args=None,
        retries=0,
        **kwargs,
    ):
        super().__init__(task_id=task_id, retries=retries, **kwargs)
        if direction not in (PUSH, PULL):
            raise ValueError(f"direction must be '{PUSH}' or '{PULL}'")
        self.conn_id = conn_id
        self.src = src
        self.dest = dest
        self.direction = direction
        self.extra_args = extra_args or []

    def execute(self, context):
        conn = get_connection(self.conn_id)

        # -a archive, -z compress, -h human, --progress for log visibility.
        cmd = ["rsync", "-azh", "--progress", *self.extra_args]

        if not conn.is_local:
            ssh_cmd = "ssh " + " ".join(conn.ssh_options())
            cmd += ["-e", ssh_cmd]
            remote = lambda path: f"{conn.target}:{path}"  # noqa: E731
        else:
            remote = lambda path: path  # noqa: E731

        if self.direction == PUSH:
            cmd += [self.src, remote(self.dest)]
        else:  # PULL
            cmd += [remote(self.src), self.dest]

        context.log(f"rsync {self.direction} via {self.conn_id} ({conn.target})")
        return self._run(cmd, context)
