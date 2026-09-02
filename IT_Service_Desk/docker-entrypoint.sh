#!/bin/sh
set -e

echo "Waiting for MySQL..."

python - <<'PY'
import os
import time

from sqlalchemy import text
from app import app
from config.database import db

for attempt in range(30):
    try:
        with app.app_context():
            db.session.execute(text("SELECT 1"))
            db.create_all()
        print("MySQL is ready and database tables are available.")
        break
    except Exception as exc:
        print(f"MySQL not ready (attempt {attempt + 1}/30): {exc}")
        time.sleep(2)
else:
    raise SystemExit("Could not connect to MySQL after 30 attempts.")
PY

exec "$@"
