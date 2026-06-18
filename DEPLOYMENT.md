# AirFlow — Deployment

This document covers running AirFlow with Docker Compose. AirFlow is composed of
Postgres, Redis, and three application services (API, scheduler, worker) that all
run from a single image.

## Architecture

```
                 ┌─────────────┐
                 │  postgres   │◄────────────┐
                 └─────────────┘             │
                 ┌─────────────┐             │
                 │    redis    │◄──────┐     │
                 └─────────────┘       │     │
   migrate (one-shot: alembic upgrade head) ─┘
        │ (must complete before app services start)
        ▼
 ┌──────────┐   ┌────────────┐   ┌──────────┐
 │   api    │   │ scheduler  │   │  worker  │
 │ :8000    │   │            │   │          │
 └──────────┘   └────────────┘   └──────────┘
```

- **postgres** — metadata database (DAGs, runs, tasks, workers).
- **redis** — queue/cache backend.
- **migrate** — one-shot job that runs `alembic upgrade head`, then exits. App
  services wait for it via `service_completed_successfully` so migrations never
  run concurrently.
- **api** — FastAPI app + web dashboard (`backend.api.main:app`) served by uvicorn.
- **scheduler** — parses DAGs, syncs DAGs/tasks, and queues runs on their cron schedule.
- **worker** — claims queued runs and executes their tasks (bash/python/ssh/rsync).
- **adminer** — web UI for browsing the Postgres database directly.

## Where to see everything (UIs)

Once the stack is up:

| What                         | URL                          |
| ---------------------------- | ---------------------------- |
| Dashboard (DAGs/runs/logs)   | http://localhost:8000        |
| API docs (OpenAPI/Swagger)   | http://localhost:8000/docs   |
| Database UI (Adminer)        | http://localhost:8080        |
| JSON API                     | http://localhost:8000/api/dags, `/api/runs` |

The dashboard's top nav links to the API docs and the database UI, so everything
is reachable from one place. Adminer login: system **PostgreSQL**, server
**postgres**, plus the user/password/db from your `.env`.

The dashboard (Airflow-style) includes:
- **DAG graph** — upstream → downstream, colored by the latest run's task states.
- **Grid** — a runs × tasks matrix of state cells (click a column to open a run).
- **Run detail** — per-task timing: queued / started / finished, **wait** time and
  **duration**, plus a state-colored graph and log links.
- **Pools** — create concurrency pools (name + slots); tasks set `pool="name"` on
  their operator, and at most `slots` of them run at once across all DAGs. The
  page shows live used / available slots.
- **Trigger** buttons and a **Code** view per DAG.

## Writing pipelines

You only write DAG files in `backend/dags/`. See **AUTHORING.md** for the full
guide and `backend/dags/sample_dag.py` for a worked example (local bash, local +
remote python, and rsync push/pull). Quick local test of a DAG:

```bash
python -m backend.cli list
python -m backend.cli run hello_local
```

## Prerequisites

- Docker Engine 24+ and the Docker Compose v2 plugin (`docker compose`).

## Configuration

All configuration is via environment variables. Copy the template and edit it:

```bash
cp .env.example .env
```

Set a strong `POSTGRES_PASSWORD` and update `DATABASE_URL` to match. Inside
Compose, services reach Postgres at host `postgres` and Redis at `redis` (the
service names) — not `localhost`.

| Variable            | Purpose                                              |
| ------------------- | ---------------------------------------------------- |
| `POSTGRES_USER`     | Postgres role                                        |
| `POSTGRES_PASSWORD` | Postgres password — **set a strong value**           |
| `POSTGRES_DB`       | Database name                                         |
| `POSTGRES_PORT`     | Host port mapped to Postgres (default 5432)          |
| `DATABASE_URL`      | SQLAlchemy/alembic URL (use `postgres` host in Compose) |
| `REDIS_HOST`        | Redis host (`redis` in Compose)                      |
| `REDIS_PORT`        | Redis port                                           |
| `DAG_FOLDER`        | Where DAG files live                                 |
| `LOG_FOLDER`        | Log output directory                                 |
| `API_PORT`          | Host port for the API                                |
| `API_WORKERS`       | uvicorn worker processes                             |
| `WAIT_FOR_DB`       | `1` = entrypoint waits for Postgres before starting  |

## Run

```bash
docker compose up -d --build
```

This builds the image, starts Postgres and Redis, runs migrations, then starts
the API, scheduler, and worker.

Check it:

```bash
docker compose ps
curl http://localhost:8000/health          # liveness
curl http://localhost:8000/health/ready    # readiness (checks the DB)
curl http://localhost:8000/api/dags        # list registered DAGs (JSON)
```

Logs and lifecycle:

```bash
docker compose logs -f scheduler
docker compose restart worker
docker compose down            # stop (keeps volumes/data)
docker compose down -v         # stop and delete data volumes
```

## Migrations

Migrations run automatically via the `migrate` service on every `up`. To run them
manually against a running stack:

```bash
docker compose run --rm migrate alembic upgrade head
```

To create a new migration during development:

```bash
docker compose run --rm migrate alembic revision --autogenerate -m "describe change"
```

## CI/CD

`.github/workflows/ci.yml` runs on every push and pull request:

1. **lint** — Ruff, error-level rules only (syntax / undefined names).
2. **test** — spins up Postgres, applies all migrations, runs the parser/validator
   smoke tests and an API import check.
3. **docker-build** — builds the production image to verify the Dockerfile.

## Production notes

This Compose stack is suitable for a single host. Before exposing it publicly:

- Move secrets out of `.env` into your platform's secret manager.
- Put the API behind a TLS-terminating reverse proxy (nginx/Caddy/Traefik).
- Don't publish the Postgres/Redis host ports unless you need external access.
- Add backups for the `pgdata` volume.
- For multi-host / cluster deployment, port these services to Kubernetes (each
  service maps to a Deployment; `migrate` becomes an init Job).
