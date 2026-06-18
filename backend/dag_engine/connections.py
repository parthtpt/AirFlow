"""Connection registry.

Connections describe *where* and *how* to reach a remote host for SSH / rsync
operators. They are resolved from environment variables so you never hard-code
hosts or credentials in a DAG:

    CONN_<ID>_HOST       (required)  e.g. prod.example.com
    CONN_<ID>_USER       (optional)  ssh user, default: current user
    CONN_<ID>_PORT       (optional)  ssh port,  default: 22
    CONN_<ID>_KEY_FILE   (optional)  path to a private key inside the container

Example, for a connection referenced as conn_id="prod":

    CONN_PROD_HOST=prod.example.com
    CONN_PROD_USER=deploy
    CONN_PROD_KEY_FILE=/keys/prod_id_rsa

The special conn_id "local" means "run on this machine" (no SSH).
"""

import os
from dataclasses import dataclass

LOCAL = "local"


class ConnectionNotConfigured(Exception):
    pass


@dataclass
class Connection:
    conn_id: str
    host: str
    user: str | None = None
    port: int = 22
    key_file: str | None = None

    @property
    def is_local(self) -> bool:
        return self.conn_id == LOCAL

    @property
    def target(self) -> str:
        """user@host or just host."""
        return f"{self.user}@{self.host}" if self.user else self.host

    def ssh_options(self) -> list[str]:
        opts = ["-p", str(self.port)]
        if self.key_file:
            opts += ["-i", self.key_file]
        # Non-interactive, fail fast rather than hang on host-key prompts.
        opts += ["-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=accept-new"]
        return opts


def get_connection(conn_id: str) -> Connection:
    """Resolve a connection by id from environment variables."""
    if conn_id == LOCAL:
        return Connection(conn_id=LOCAL, host="localhost")

    prefix = f"CONN_{conn_id.upper()}_"
    host = os.getenv(prefix + "HOST")
    if not host:
        raise ConnectionNotConfigured(
            f"Connection '{conn_id}' is not configured. "
            f"Set {prefix}HOST (and optionally {prefix}USER / {prefix}PORT / "
            f"{prefix}KEY_FILE) in your environment / .env file."
        )

    return Connection(
        conn_id=conn_id,
        host=host,
        user=os.getenv(prefix + "USER"),
        port=int(os.getenv(prefix + "PORT", "22")),
        key_file=os.getenv(prefix + "KEY_FILE"),
    )
