"""AirFlow HTTP API + web dashboard.

- Web UI:  /  (DAGs)  ·  /dags/{id}  (graph, grid, tasks, runs, code)
           /runs/{id} (graph + timing)  ·  /pools (concurrency pools)
- JSON:    /api/dags, /api/runs, /api/pools
- Probes:  /health, /health/ready   ·   Auto docs: /docs
"""

import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text

from backend.api.graph import build_mermaid, get_source, get_structure
from backend.database.repositories.dag_repository import DAGRepository
from backend.database.repositories.dag_run_repository import DagRunRepository
from backend.database.repositories.pool_repository import PoolRepository
from backend.database.repositories.task_repository import TaskRepository
from backend.database.repositories.task_run_repository import TaskRunRepository
from backend.database.session import SessionLocal

app = FastAPI(title="AirFlow API", version="0.3.0")

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
ADMINER_URL = os.getenv("ADMINER_URL", "http://localhost:8080")
LOG_FOLDER = Path(os.getenv("LOG_FOLDER", "backend/logs")).resolve()

dags = DAGRepository()
dag_runs = DagRunRepository()
tasks = TaskRepository()
task_runs = TaskRunRepository()
pools = PoolRepository()


# --- template filters ------------------------------------------------------

def _fmt_dt(value):
    if not value:
        return "-"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


def _fmt_dur(seconds):
    if seconds is None:
        return "-"
    seconds = float(seconds)
    if seconds < 1:
        return f"{seconds*1000:.0f} ms"
    if seconds < 60:
        return f"{seconds:.1f}s"
    m, s = divmod(int(seconds), 60)
    if m < 60:
        return f"{m}m {s}s"
    h, m = divmod(m, 60)
    return f"{h}h {m}m"


TEMPLATES.env.filters["dt"] = _fmt_dt
TEMPLATES.env.filters["dur"] = _fmt_dur


def render(request, template, **ctx):
    ctx.update({"adminer_url": ADMINER_URL})
    return TEMPLATES.TemplateResponse(request, template, ctx)


def _structure_or_fallback(dag_id, task_rows):
    structure = get_structure(dag_id)
    if structure is None:
        structure = {"tasks": [t.task_id for t in task_rows], "edges": []}
    return structure


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

    task_rows = tasks.list_by_dag(dag.id)
    runs = dag_runs.list_by_dag(dag.id, limit=50)
    structure = _structure_or_fallback(dag_id, task_rows)

    # color the graph by the latest run
    last = dag_runs.last_run_for_dag(dag.id)
    latest_states = task_runs.states_for_run(last.id) if last else {}

    # grid: oldest -> newest, last 14 runs
    grid_runs = list(reversed(runs[:14]))
    grid_states = {r["id"]: task_runs.states_for_run(r["id"]) for r in grid_runs}

    return render(
        request, "dag.html",
        dag=dag,
        tasks=task_rows,
        runs=runs,
        mermaid=build_mermaid(structure, latest_states),
        grid_tasks=structure["tasks"],
        grid_runs=grid_runs,
        grid_states=grid_states,
        source=get_source(dag_id),
    )


@app.post("/dags/{dag_id}/trigger")
def trigger_dag(dag_id: str):
    dag = dags.get_by_dag_id(dag_id)
    if dag is None:
        raise HTTPException(status_code=404, detail="DAG not found")
    dag_runs.create(dag.id, state="queued",
                    execution_date=datetime.now(timezone.utc))
    return RedirectResponse(url=f"/dags/{dag_id}", status_code=303)


@app.get("/runs/{run_id}", response_class=HTMLResponse)
def run_detail(request: Request, run_id: str):
    run = dag_runs.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    dag_row = dags.get_by_id(run.dag_id)
    dag_id = dag_row.dag_id if dag_row else "?"
    task_rows = task_runs.list_by_dag_run(run_id)
    states = {r["task_id"]: r["state"] for r in task_rows}
    structure = _structure_or_fallback(dag_id, [])

    duration = None
    if run.started_at and run.finished_at:
        duration = (run.finished_at - run.started_at).total_seconds()

    return render(
        request, "run.html",
        run=run,
        dag_id=dag_id,
        tasks=task_rows,
        mermaid=build_mermaid(structure, states),
        duration=duration,
    )


@app.get("/runs/{run_id}/tasks/{task_id}/log", response_class=HTMLResponse)
def task_log(request: Request, run_id: str, task_id: str):
    rows = task_runs.list_by_dag_run(run_id)
    match = next((r for r in rows if r["task_id"] == task_id), None)
    content = "(no log)"
    if match and match["log_path"]:
        path = Path(match["log_path"]).resolve()
        if str(path).startswith(str(LOG_FOLDER)) and path.exists():
            content = path.read_text(encoding="utf-8", errors="replace")
        else:
            content = "(log file not available)"
    return render(request, "log.html", run_id=run_id, task_id=task_id, content=content)


@app.get("/pools", response_class=HTMLResponse)
def pools_page(request: Request):
    return render(request, "pools.html", pools=pools.list_with_usage())


@app.post("/pools")
def create_pool(name: str = Form(...), slots: int = Form(...),
                description: str = Form("")):
    pools.create(name=name.strip(), slots=int(slots),
                 description=(description.strip() or None))
    return RedirectResponse(url="/pools", status_code=303)


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
        {"id": str(d.id), "dag_id": d.dag_id, "schedule": d.schedule,
         "is_active": d.is_active}
        for d in dags.list_all()
    ]


@app.get("/api/runs")
def api_runs(limit: int = 50):
    return dag_runs.list_recent(limit=limit)


@app.get("/api/pools")
def api_pools():
    return pools.list_with_usage()
