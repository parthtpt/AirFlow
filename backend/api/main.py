"""AirFlow HTTP API + web dashboard.

- Web UI: /            (DAGs, runs, task states, logs)
- JSON:   /api/dags, /api/runs
- Probes: /health, /health/ready
- Auto docs: /docs
"""

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text

from backend.database.repositories.dag_repository import DAGRepository
from backend.database.repositories.dag_run_repository import DagRunRepository
from backend.database.repositories.task_repository import TaskRepository
from backend.database.repositories.task_run_repository import TaskRunRepository
from backend.database.session import SessionLocal

app = FastAPI(title="AirFlow API", version="0.2.0")

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
ADMINER_URL = os.getenv("ADMINER_URL", "http://localhost:8080")
LOG_FOLDER = Path(os.getenv("LOG_FOLDER", "backend/logs")).resolve()

dags = DAGRepository()
dag_runs = DagRunRepository()
tasks = TaskRepository()
task_runs = TaskRunRepository()


def render(request, template, **ctx):
    ctx.update({"request": request, "adminer_url": ADMINER_URL})
    return TEMPLATES.TemplateResponse(template, ctx)


# --- Web dashboard ---------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return render(
        request, "index.html",
        dags=dags.list_all(),
        runs=dag_runs.list_recent(limit=25),
    )


@app.get("/dags/{dag_id}", response_class=HTMLResponse)
def dag_detail(request: Request, dag_id: str):
    dag = dags.get_by_dag_id(dag_id)
    if dag is None:
        raise HTTPException(status_code=404, detail="DAG not found")
    return render(
        request, "dag.html",
        dag=dag,
        tasks=tasks.list_by_dag(dag.id),
        runs=dag_runs.list_by_dag(dag.id),
    )


@app.get("/runs/{run_id}", response_class=HTMLResponse)
def run_detail(request: Request, run_id: str):
    run = dag_runs.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return render(
        request, "run.html",
        run=run,
        tasks=task_runs.list_by_dag_run(run_id),
    )


@app.get("/runs/{run_id}/tasks/{task_id}/log", response_class=HTMLResponse)
def task_log(request: Request, run_id: str, task_id: str):
    rows = task_runs.list_by_dag_run(run_id)
    match = next((r for r in rows if r["task_id"] == task_id), None)
    content = "(no log)"
    if match and match["log_path"]:
        path = Path(match["log_path"]).resolve()
        # Prevent path traversal: only serve files under LOG_FOLDER.
        if str(path).startswith(str(LOG_FOLDER)) and path.exists():
            content = path.read_text(encoding="utf-8", errors="replace")
        else:
            content = "(log file not available)"
    return render(request, "log.html", run_id=run_id, task_id=task_id, content=content)


# --- JSON API --------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/ready")
def ready():
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as exc:  # noqa: BLE001
        return {"status": "not-ready", "detail": str(exc)}


@app.get("/api/dags")
def api_dags():
    return [
        {
            "id": str(d.id),
            "dag_id": d.dag_id,
            "schedule": d.schedule,
            "is_active": d.is_active,
        }
        for d in dags.list_all()
    ]


@app.get("/api/runs")
def api_runs(limit: int = 50):
    return dag_runs.list_recent(limit=limit)
