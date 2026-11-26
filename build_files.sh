#!/bin/bash
# build_files.sh - Runs during Vercel build step to collect static files

echo "=== Installing Python dependencies ==="
pip install -r requirements.txt

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput --clear

echo "=== Running database migrations ==="
python manage.py migrate --noinput

echo "=== Build complete ==="
