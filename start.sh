#!/bin/bash
set -e

until psql "${DATABASE_URL}" -c '\q' 2>/dev/null; do
  echo "Waiting for database..."
  sleep 1
done

psql "${DATABASE_URL}" -f /app/schema.sql

exec uvicorn main:app --host 0.0.0.0 --port 8000
