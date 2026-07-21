#!/usr/bin/env bash
# build.sh — Render build script
# Runs on every deploy: installs deps and applies DB migrations

set -e  # Exit immediately on error

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Running Alembic database migrations..."
alembic upgrade head

echo "==> Build complete!"
