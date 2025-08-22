#!/bin/bash

# Google Chirp Transcription API Status Check Script

echo "🔍 Checking Google Chirp Transcription API Status..."
echo "=" * 50

# Check Redis
echo "📦 Checking Redis..."
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "❌ Redis is not running"
fi

# Check Celery worker
echo "🔧 Checking Celery worker..."
if pgrep -f "celery.*worker" > /dev/null; then
    echo "✅ Celery worker is running"
else
    echo "❌ Celery worker is not running"
fi

# Check FastAPI server
echo "🌐 Checking FastAPI server..."
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ FastAPI server is running"
    echo "   📖 API Documentation: http://localhost:8000/docs"
    echo "   🔄 ReDoc: http://localhost:8000/redoc"
else
    echo "❌ FastAPI server is not running"
fi

# Check Google credentials
echo "🔑 Checking Google credentials..."
if [ -f "credentials.json" ]; then
    echo "✅ Google credentials file found"
else
    echo "❌ Google credentials file not found"
fi

# Check uploads directory
echo "📁 Checking uploads directory..."
if [ -d "uploads_audios" ]; then
    echo "✅ Uploads directory exists"
else
    echo "❌ Uploads directory not found"
fi

# Check system dependencies
echo "🛠️  Checking system dependencies..."
if command -v sox > /dev/null 2>&1; then
    echo "✅ Sox is installed"
else
    echo "❌ Sox is not installed"
fi

if command -v ffmpeg > /dev/null 2>&1; then
    echo "✅ FFmpeg is installed"
else
    echo "❌ FFmpeg is not installed"
fi

# Test API endpoints
echo "🧪 Testing API endpoints..."
if curl -s http://localhost:8000/openapi.json > /dev/null 2>&1; then
    echo "✅ API endpoints are accessible"
    echo "   Available endpoints:"
    curl -s http://localhost:8000/openapi.json | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for path, methods in data['paths'].items():
        for method in methods.keys():
            print(f'     {method.upper()} {path}')
except:
    print('     Error parsing API spec')
" 2>/dev/null
else
    echo "❌ API endpoints are not accessible"
fi

echo ""
echo "🏁 Status check completed!" 