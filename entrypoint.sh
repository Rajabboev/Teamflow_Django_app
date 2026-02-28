#!/bin/sh
set -eu

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-teamflow.settings.production}"

wait_for_postgres() {
python - <<'PY'
import os
import sys
import time

import psycopg2

host = os.environ.get("DB_HOST", "localhost")
port = int(os.environ.get("DB_PORT", "5432"))
name = os.environ.get("DB_NAME", "")
user = os.environ.get("DB_USER", "")
password = os.environ.get("DB_PASSWORD", "")

if not name:
    print("DB_NAME not set; skipping PostgreSQL wait.")
    sys.exit(0)

max_attempts = int(os.environ.get("DB_WAIT_MAX_ATTEMPTS", "60"))
delay = float(os.environ.get("DB_WAIT_DELAY_SECONDS", "1"))

for attempt in range(1, max_attempts + 1):
    try:
        conn = psycopg2.connect(
            dbname=name,
            user=user,
            password=password,
            host=host,
            port=port,
        )
        conn.close()
        print("PostgreSQL is ready.")
        sys.exit(0)
    except Exception as e:
        print(f"Waiting for PostgreSQL ({attempt}/{max_attempts})... {e}")
        time.sleep(delay)

print("PostgreSQL not ready in time.", file=sys.stderr)
sys.exit(1)
PY
}

wait_for_postgres

python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear

if [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
python - <<'PY'
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.environ.get("DJANGO_SETTINGS_MODULE", "teamflow.settings.production"))
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
password = os.environ["DJANGO_SUPERUSER_PASSWORD"]

user, created = User.objects.get_or_create(username=username, defaults={"email": email})
if created:
    user.is_staff = True
    user.is_superuser = True
    user.set_password(password)
    user.save()
    print(f"Created superuser '{username}'.")
else:
    # Keep idempotent but ensure password matches env if provided
    user.is_staff = True
    user.is_superuser = True
    if not user.email and email:
        user.email = email
    user.set_password(password)
    user.save()
    print(f"Updated superuser '{username}'.")
PY
fi

exec "$@"

