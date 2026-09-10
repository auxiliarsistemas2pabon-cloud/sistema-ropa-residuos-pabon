#!/bin/sh
set -e

echo "Esperando a la base de datos..."
python - <<'PY'
import os, time, sys
import psycopg
dsn = "host={h} port={p} dbname={d} user={u} password={pw}".format(
    h=os.environ.get("POSTGRES_HOST", "db"),
    p=os.environ.get("POSTGRES_PORT", "5432"),
    d=os.environ.get("POSTGRES_DB", "clinica_pabon"),
    u=os.environ.get("POSTGRES_USER", "clinica_pabon"),
    pw=os.environ.get("POSTGRES_PASSWORD", ""),
)
for _ in range(30):
    try:
        psycopg.connect(dsn).close()
        sys.exit(0)
    except Exception:
        time.sleep(2)
sys.exit("La base de datos no respondió a tiempo.")
PY

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Recolectando estáticos..."
python manage.py collectstatic --noinput

exec "$@"
