#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
until nc -z postgres 5432; do
  sleep 0.5
done
echo "PostgreSQL is up and running!"

# Wait for Redis to be ready
echo "Waiting for Redis..."
until nc -z redis 6379; do
  sleep 0.5
done
echo "Redis is up and running!"

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting application..."
if [ "$DEBUG" = "true" ]; then
  # Development mode with auto-reload
  uvicorn main:app --host 0.0.0.0 --port 8000 --reload
else
  # Production mode
  uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
fi