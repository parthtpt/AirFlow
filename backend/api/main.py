"""AirFlow HTTP API.

Minimal FastAPI surface for now: liveness/readiness probes plus a read-only
DAG listing. Endpoints can grow alongside the rest of the app.
"""

from fastapi import FastAPI
from sqlalchemy import text

from backend.database.repositories.dag_repository import DAGRepository
from backend.database.session import SessionLocal

app = FastAPI(title="AirFlow API", version="0.1.0")

dag_repo = DAGRepository()


@app.get("/health")
def health():
    """Liveness probe: the process is up."""
    return {"status": "ok"}


@app.get("/health/ready")
def ready():
    """Readiness probe: the database is reachable."""
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as exc:  # noqa: BLE001 - report any DB failure as not-ready
        return {"status": "not-ready", "detail": str(exc)}


@app.get("/dags")
def list_dags():
    """List all registered DAGs."""
    dags = dag_repo.list_all()
    return [
        {
            "id": str(dag.id),
            "dag_id": dag.dag_id,
            "schedule": dag.schedule,
            "is_active": dag.is_active,
        }
        for dag in dags
    ]
