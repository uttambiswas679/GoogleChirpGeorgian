#!/bin/bash

# Google Chirp Transcription API Startup Script

echo "🚀 Starting Google Chirp Transcription API..."

# Check if Redis is running
if ! pgrep -x "redis-server" > /dev/null; then
    echo "📦 Starting Redis server..."
    redis-server --daemonize yes
    sleep 2
else
    echo "✅ Redis server is already running"
fi

# Create uploads directory if it doesn't exist
mkdir -p uploads_audios

# Check if Google credentials file exists
if [ ! -f "credentials.json" ]; then
    echo "❌ Error: credentials.json not found!"
    echo "Please place your Google Cloud service account key file in the project root."
    exit 1
fi

# Start Celery worker in background
echo "🔧 Starting Celery worker..."
celery -A app worker --loglevel=info &
CELERY_PID=$!

# Wait a moment for Celery to start
sleep 3

# Start FastAPI server
echo "🌐 Starting FastAPI server..."
echo "📖 API Documentation will be available at: http://localhost:8000/docs"
echo "🔄 ReDoc will be available at: http://localhost:8000/redoc"

uvicorn app:fastapi_app --host 0.0.0.0 --port 8000 --reload

# Cleanup function
cleanup() {
    echo "🛑 Shutting down services..."
    kill $CELERY_PID 2>/dev/null
    pkill -f "celery.*worker" 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for background processes
wait 