#!/usr/bin/env bash

# Pune Dam Water Storage Analytics Dashboard Runner Script
PORT="${1:-8000}"

echo "=========================================================="
echo "💧  Pune Dam Water Storage Analytics Dashboard  💧"
echo "=========================================================="
echo "Starting local HTTP server on port ${PORT}..."
echo "Open your browser at: http://localhost:${PORT}"
echo "Press Ctrl+C to stop the server."
echo "=========================================================="

# Check if python3 is available
if command -v python3 &>/dev/null; then
    python3 -m http.server "${PORT}"
elif command -v python &>/dev/null; then
    python -m http.server "${PORT}"
else
    echo "❌ Error: Python 3 is required to run the local server."
    exit 1
fi
