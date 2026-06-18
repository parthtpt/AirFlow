"""AirFlow command line.

    python -m backend.cli list                 # list DAGs found in DAG_FOLDER
    python -m backend.cli run <dag_id>         # run a DAG now, in-process (no DB)
    python -m backend.cli trigger <dag_id>     # enqueue a run for a worker (uses DB)

`run` is the quickest way to test a DAG you just wrote - it executes locally and
prints task output, no database required. `trigger` queues a run that the worker
picks up and records, so it shows in the dashboard.
"""

import argparse
import os
import sys

from backend.dag_engine.executor import DagRunner
from backend.dag_engine.parser import DAGParser


def _parse():
    folder = os.getenv("DAG_FOLDER", "backend/dags")
    return DAGParser(dag_folder=folder).parse()


def cmd_list(_args):
    dags = _parse()
    if not dags:
        print("No DAGs found.")
        return
    for dag in dags.values():
        print(f"{dag.dag_id}  (schedule={dag.schedule}, tasks={len(dag.tasks)})")


def cmd_run(args):
    dags = _parse()
    dag = dags.get(args.dag_id)
    if dag is None:
        print(f"DAG '{args.dag_id}' not found.", file=sys.stderr)
        sys.exit(1)
    result = DagRunner().run(dag)
    sys.exit(0 if result["state"] == "success" else 1)


def cmd_trigger(args):
    # Imported lazily so `list`/`run` work without database deps configured.
    from backend.database.repositories.dag_repository import DAGRepository
    from backend.database.repositories.dag_run_repository import DagRunRepository

    dag = DAGRepository().get_by_dag_id(args.dag_id)
    if dag is None:
        print(
            f"DAG '{args.dag_id}' is not in the database yet. "
            "Start the scheduler so it gets synced, then retry.",
            file=sys.stderr,
        )
        sys.exit(1)
    run = DagRunRepository().create(dag.id, state="queued")
    print(f"Queued run {run.id} for '{args.dag_id}'. A worker will execute it.")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="airflow", description="AirFlow CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="list DAGs").set_defaults(func=cmd_list)

    p_run = sub.add_parser("run", help="run a DAG now, in-process")
    p_run.add_argument("dag_id")
    p_run.set_defaults(func=cmd_run)

    p_trig = sub.add_parser("trigger", help="enqueue a run for a worker")
    p_trig.add_argument("dag_id")
    p_trig.set_defaults(func=cmd_trigger)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
