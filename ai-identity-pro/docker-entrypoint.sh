#!/bin/bash
# Docker entrypoint for AI Identity Pro
# Starts both backend API and frontend

set -e

echo "Starting AI Identity Pro..."

# Start backend in background
cd /app/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Start frontend in background  
cd /app/frontend
npm start &
FRONTEND_PID=$!

# Handle shutdown
shutdown() {
    echo "Shutting down..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit 0
}

trap shutdown SIGTERM SIGINT

# Keep container running
wait
