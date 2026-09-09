#!/usr/bin/env bash

# Pune Dam Water Storage Analytics Dashboard & DBMS Launcher Script
PORT="${1:-8000}"

if [ "$1" == "--inspect" ]; then
    python3 database/db_manager.py --inspect
    exit 0
fi

echo "=========================================================="
echo "💧  Pune Dam Water Storage Analytics Dashboard  💧"
echo "=========================================================="
echo "Starting local HTTP server on port ${PORT}..."
echo "Serving web assets from 'web/' directory..."
echo "Open your browser at: http://localhost:${PORT}"
echo "Press Ctrl+C to stop the server."
echo "=========================================================="

if command -v python3 &>/dev/null; then
    python3 -m http.server "${PORT}" --directory web
elif command -v python &>/dev/null; then
    python -m http.server "${PORT}" --directory web
else
    echo "❌ Error: Python 3 is required to run the local server."
    exit 1
fi

