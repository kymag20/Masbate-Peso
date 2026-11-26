#!/bin/bash
# build_files.sh - Runs during Vercel build step to collect static files

echo "=== Installing Python dependencies ==="
python3 -m pip install -r requirements.txt

echo "=== Collecting static files ==="
python3 manage.py collectstatic --noinput --clear

echo "=== Build complete ==="
