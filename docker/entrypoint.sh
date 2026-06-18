#!/usr/bin/env bash
# Container entrypoint shared by all AirFlow services.
#
# Optionally waits for Postgres to accept connections (WAIT_FOR_DB=1), then
# exec's whatever command the container was given (set per-service in compose).
set -euo pipefail

wait_for_db() {
  echo "[entrypoint] waiting for database..."
  python - <<'PY'
import os
import sys
import time

import psycopg2

url = os.environ.get("DATABASE_URL")
if not url:
    print("[entrypoint] DATABASE_URL not set; skipping DB wait")
    sys.exit(0)

deadline = 60  # seconds
for attempt in range(deadline):
    try:
        psycopg2.connect(url).close()
        print("[entrypoint] database is ready")
        sys.exit(0)
    except psycopg2.OperationalError:
        time.sleep(1)

print(f"[entrypoint] database not reachable after {deadline}s", file=sys.stderr)
sys.exit(1)
PY
}

if [[ "${WAIT_FOR_DB:-0}" == "1" ]]; then
  wait_for_db
fi

echo "[entrypoint] starting: $*"
exec "$@"
