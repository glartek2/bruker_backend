#!/bin/sh

MAX_RETRIES=20
RETRY_INTERVAL=2
COUNT=0

echo "⏳ Waiting for Postgres at $DB_HOST:$DB_PORT (user $DB_USER)..."

while ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
  COUNT=$((COUNT+1))
  echo "---"
  echo "🔁 [$COUNT/$MAX_RETRIES] Still waiting for DB..."
  if [ $COUNT -ge $MAX_RETRIES ]; then
    echo "❌ Could not connect to Postgres. Exiting."
    exit 1
  fi
  sleep $RETRY_INTERVAL
done

echo "✅ Database is ready!"

echo "➡️ Applying migrations..."
poetry run python manage.py migrate

echo "🚀 Starting Django server..."
poetry run python manage.py runserver 0.0.0.0:8000
