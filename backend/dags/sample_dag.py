"""Sample data pipeline.

Shows every operator type:
  - bash on prod        (SSHOperator + conn_id="prod")
  - python locally      (PythonOperator)
  - python on a remote  (SSHOperator + conn_id="remote")
  - rsync local -> prod  and  prod -> local  (RsyncOperator)

To run the remote / rsync steps, configure the "prod" and "remote" connections
via environment variables (see .env.example), e.g.:

    CONN_PROD_HOST=prod.example.com
    CONN_PROD_USER=deploy
    CONN_PROD_KEY_FILE=/keys/prod_id_rsa
    CONN_REMOTE_HOST=gpu-box.example.com
    CONN_REMOTE_USER=ml

Test the local parts immediately with:   python -m backend.cli run sample_dag
"""

from backend.dag_engine.core.decorators import dag
from backend.dag_engine.operators import (
    BashOperator,
    PythonOperator,
    RsyncOperator,
    SSHOperator,
)


def transform(context):
    """A plain Python step that runs locally on the worker."""
    context.log("Transforming data locally...")
    rows = [{"id": i, "value": i * i} for i in range(5)]
    context.log(f"Produced {len(rows)} rows")
    return rows


@dag(dag_id="sample_dag", schedule="*/5 * * * *")
def pipeline():

    # 1. Prepare a local working directory (local bash).
    prepare = BashOperator(
        task_id="prepare_local",
        bash_command="mkdir -p /tmp/airflow_demo && echo 'input data' "
        "> /tmp/airflow_demo/input.txt && ls -l /tmp/airflow_demo",
    )

    # 2. Transform the data with local Python.
    transform_step = PythonOperator(
        task_id="transform_local",
        python_callable=transform,
    )

    # 3. Ship the prepared files up to prod (local -> prod).
    push = RsyncOperator(
        task_id="push_to_prod",
        conn_id="prod",
        direction="push",
        src="/tmp/airflow_demo/",
        dest="/opt/app/incoming/",
    )

    # 4. Run a bash script on prod.
    run_on_prod = SSHOperator(
        task_id="run_bash_on_prod",
        conn_id="prod",
        command="bash /opt/app/scripts/process.sh /opt/app/incoming",
    )

    # 5. Run a Python script on a remote box.
    #    `pool` caps how many tasks across all DAGs hit this resource at once.
    #    Create the "remote_pool" pool in the dashboard (Pools page) to enforce it.
    run_remote_py = SSHOperator(
        task_id="run_python_on_remote",
        conn_id="remote",
        command="python3 /opt/jobs/aggregate.py --input /opt/app/incoming",
        retries=2,
        pool="remote_pool",
    )

    # 6. Pull the results back down to local (prod -> local).
    pull = RsyncOperator(
        task_id="pull_from_prod",
        conn_id="prod",
        direction="pull",
        src="/opt/app/results/",
        dest="/tmp/airflow_demo/results/",
    )

    prepare >> transform_step >> push >> run_on_prod >> run_remote_py >> pull
