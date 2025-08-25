#!/usr/bin/env python3
"""
Simple startup script for Audio Transcription Service
"""

import uvicorn
import os

if __name__ == "__main__":
    # Ensure uploads directory exists
    os.makedirs("uploads_audios", exist_ok=True)
    
    print("🚀 Starting Audio Transcription Service...")
    print("📁 Upload directory: uploads_audios/")
    print("🌐 Server will be available at: http://localhost:8000")
    print("📊 File size limit: 100MB")
    print("=" * 50)
    
    # Start the server
    uvicorn.run(
        "app:fastapi_app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
