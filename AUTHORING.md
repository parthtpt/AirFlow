# Writing DAGs

This is the only file type you need to touch to build a pipeline. Drop a `.py`
file in `backend/dags/`, define a DAG with tasks, and the platform schedules,
runs, logs, and displays it for you.

## The shape of a DAG

```python
from backend.dag_engine.core.decorators import dag
from backend.dag_engine.operators import (
    BashOperator, PythonOperator, SSHOperator, RsyncOperator,
)

@dag(dag_id="my_pipeline", schedule="0 * * * *")   # cron schedule
def pipeline():
    a = BashOperator(task_id="step_a", bash_command="echo hi")
    b = PythonOperator(task_id="step_b", python_callable=my_func)
    a >> b        # a runs before b
```

- `dag_id` is unique. `schedule` is standard cron (`*/5 * * * *`, `0 2 * * *`, ...).
- `>>` sets dependencies: `a >> b >> c`, or fan-out `a >> [b, c]` by repeating
  (`a >> b`, `a >> c`).
- A task only runs if **all** its upstream tasks succeeded; otherwise it's skipped.

## Operators

| Operator         | What it does                                  | Key args |
| ---------------- | --------------------------------------------- | -------- |
| `BashOperator`   | Run a bash command/script **locally**          | `bash_command`, `cwd` |
| `PythonOperator` | Run a Python callable or `.py` script locally  | `python_callable` / `python_script`, `op_args`, `op_kwargs`, `script_args` |
| `SSHOperator`    | Run any command on a **remote host** over SSH  | `conn_id`, `command` |
| `RsyncOperator`  | Sync files between local and remote            | `conn_id`, `src`, `dest`, `direction` (`push`/`pull`) |

All operators accept `retries=<n>` (default 0).

### Examples

```python
# bash locally
BashOperator(task_id="prep", bash_command="mkdir -p /tmp/out && ./scripts/x.sh")

# python locally - a callable...
def transform(context):     # `context` is optional; gives you context.log(...)
    context.log("working")
    return 42
PythonOperator(task_id="transform", python_callable=transform)

# ...or a script file
PythonOperator(task_id="ingest", python_script="scripts/ingest.py",
               script_args=["--date", "2026-06-19"])

# run a bash script on prod, or a python script on a remote box
SSHOperator(task_id="deploy", conn_id="prod",   command="bash /opt/app/deploy.sh")
SSHOperator(task_id="train",  conn_id="remote", command="python3 /opt/jobs/train.py")

# move files: local -> prod, and prod -> local
RsyncOperator(task_id="up",   conn_id="prod", direction="push",
              src="./build/", dest="/opt/app/")
RsyncOperator(task_id="down", conn_id="prod", direction="pull",
              src="/opt/app/results/", dest="./results/")
```

## Connections (for SSH / rsync)

Don't hard-code hosts. Define connections as environment variables in `.env`:

```
CONN_PROD_HOST=prod.example.com
CONN_PROD_USER=deploy
CONN_PROD_KEY_FILE=/keys/prod_id_rsa     # put the key in ./keys/ (mounted read-only)
```

Then reference them by id: `conn_id="prod"`. The id `"local"` means "run here".

## Running & seeing your DAG

```bash
python -m backend.cli list                 # list DAGs
python -m backend.cli run my_pipeline      # run now, in-process, prints output
python -m backend.cli trigger my_pipeline  # queue a run for a worker (shows in UI)
```

When the stack is up (`docker compose up -d`), the scheduler runs DAGs on their
cron schedule automatically and everything appears in the dashboard at
<http://localhost:8000>. See `DEPLOYMENT.md` for the full list of UIs.
