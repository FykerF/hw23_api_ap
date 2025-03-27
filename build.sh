#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Do NOT run migrations
# We're intentionally skipping "alembic upgrade head"
echo "Skipping database migrations as requested"
