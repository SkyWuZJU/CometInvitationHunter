#!/bin/bash

# Load development environment
export $(cat config/development.env | grep -v '^#' | xargs)

echo "Starting Comet Invitation Hunter in development mode..."

# Start backend in background
echo "Starting backend server..."
source venv/bin/activate
cd backend
uvicorn main:app --reload --port $BACKEND_PORT &
BACKEND_PID=$!
cd ..

# Start frontend in background
echo "Starting frontend server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "Backend running on port $BACKEND_PORT (PID: $BACKEND_PID)"
echo "Frontend running on port $FRONTEND_PORT (PID: $FRONTEND_PID)"
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait