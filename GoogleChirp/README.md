# Google Chirp Transcription API

A FastAPI-based application that provides audio transcription services using Google Cloud Speech-to-Text API with support for both English and Georgian languages.

## Features

- **Multi-language Support**: Transcribe audio in English and Georgian
- **Asynchronous Processing**: Uses Celery for background task processing
- **Google Cloud Integration**: Leverages Google Cloud Speech-to-Text API
- **Audio Preprocessing**: Supports various audio formats with automatic conversion
- **RESTful API**: Clean REST endpoints for easy integration

## Prerequisites

- Python 3.8+
- Redis server
- Google Cloud account with Speech-to-Text API enabled
- Google Cloud Storage buckets configured
- Google service account credentials

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd GoogleChirp
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install system dependencies**
   ```bash
   # Install sox for audio processing
   sudo apt-get install sox
   
   # Install ffmpeg for pydub
   sudo apt-get install ffmpeg
   
   # Install Redis
   sudo apt-get install redis-server redis-tools
   ```

4. **Set up Google Cloud credentials**
   - Download your Google service account key JSON file
   - Place it in the project root as `credentials.json`
   - Ensure the service account has access to:
     - Speech-to-Text API
     - Cloud Storage (for both `healthorbit_bucket` and `ho_georgian` buckets)

5. **Start Redis server**
   ```bash
   sudo systemctl start redis-server
   sudo systemctl enable redis-server
   ```

## Configuration

### Google Cloud Setup

1. **Create Google Cloud Storage buckets**:
   - `healthorbit_bucket` (for English transcriptions)
   - `ho_georgian` (for Georgian transcriptions)

2. **Enable Speech-to-Text API** in your Google Cloud project

3. **Set up recognizers**:
   - English: `projects/healthorbit-24052/locations/us-central1/recognizers/_`
   - Georgian: `projects/healthorbit-ai-446710/locations/global/recognizers/_`

## Running the Application

### Option 1: Using the startup script (Recommended)
```bash
./start.sh
```

### Option 2: Manual setup

1. **Start the Celery worker** (in a separate terminal):
   ```bash
   celery -A app worker --loglevel=info
   ```

2. **Start the FastAPI server** (in another terminal):
   ```bash
   uvicorn app:fastapi_app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Access the API documentation**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

### 1. English Transcription
- **POST** `/transcribe/`
- **Description**: Transcribe audio files in English
- **Request**: Multipart form with audio file
- **Response**: Task ID for tracking

### 2. Georgian Transcription
- **POST** `/transcribe-georgian/`
- **Description**: Transcribe audio files in Georgian (with English fallback)
- **Request**: Multipart form with audio file
- **Response**: Task ID for tracking

### 3. Get Results
- **GET** `/result/{task_id}`
- **Description**: Retrieve transcription results
- **Response**: Transcription data or status

## Usage Examples

### Using curl

**English Transcription:**
```bash
curl -X POST "http://localhost:8000/transcribe/" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_audio_file.mp3"
```

**Georgian Transcription:**
```bash
curl -X POST "http://localhost:8000/transcribe-georgian/" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_georgian_audio.mp3"
```

**Get Results:**
```bash
curl -X GET "http://localhost:8000/result/{task_id}"
```

### Using Python

```python
import requests

# Upload audio for English transcription
with open('audio_file.mp3', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/transcribe/',
        files={'file': f}
    )
    task_id = response.json()['task_id']

# Check results
result = requests.get(f'http://localhost:8000/result/{task_id}')
print(result.json())
```

## Response Format

```json
{
  "status": "success",
  "result": {
    "transcription": [
      {
        "start_time": "0.0s",
        "end_time": "2.5s",
        "language_code": "en-US",
        "confidence": 0.95,
        "transcript": "Hello, this is a test transcription."
      }
    ]
  }
}
```

## Supported Audio Formats

- MP3
- M4A
- WAV
- FLAC
- OGG
- And other formats supported by pydub

## Error Handling

The API returns appropriate HTTP status codes:
- `200`: Success
- `400`: Bad request
- `500`: Internal server error

## Monitoring

- Check Celery worker logs for task processing status
- Monitor Redis for task queue status
- Use Google Cloud Console to monitor API usage

## Troubleshooting

1. **Redis Connection Issues**:
   - Ensure Redis server is running: `sudo systemctl status redis-server`
   - Check Redis connection: `redis-cli ping`

2. **Google Cloud Authentication**:
   - Verify `credentials.json` is in the correct location
   - Check service account permissions

3. **Audio Processing Issues**:
   - Ensure sox and ffmpeg are installed
   - Check audio file format compatibility

4. **Memory Issues**:
   - Large audio files may require more memory
   - Consider chunking very large files

## Status Check

Use the status check script to verify all services are running:
```bash
./status_check.sh
```

## License

[Add your license information here] 