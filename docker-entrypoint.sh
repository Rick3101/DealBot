#!/bin/bash
# Docker entrypoint script for production deployment
# Uses Render's $PORT environment variable

set -e

# Get port from environment or default to 5000
PORT=${PORT:-5000}

echo "Starting application on port $PORT..."

# Start gunicorn with eventlet worker for WebSocket support
exec gunicorn \
    --worker-class eventlet \
    -w 1 \
    --bind "0.0.0.0:$PORT" \
    wsgi:app \
    --timeout 120 \
    --log-level info \
    --access-logfile - \
    --error-logfile -
