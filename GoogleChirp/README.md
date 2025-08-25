# Google Chirp Transcription API

A FastAPI-based application that provides audio transcription services using Google Cloud Speech-to-Text API with support for both English and Georgian languages.

## Features

- **Multi-language Support**: Transcribe audio in English and Georgian
- **Translation Support**: Translate Georgian transcripts to English
- **Asynchronous Processing**: Uses Celery for background task processing
- **Google Cloud Integration**: Leverages Google Cloud Speech-to-Text and Translate APIs
- **Audio Preprocessing**: Supports various audio formats with automatic conversion
- **Large File Support**: Handles files up to 100MB with efficient chunked uploads
- **RESTful API**: Clean REST endpoints for easy integration

## Prerequisites

- Python 3.8+
- Redis server
- Google Cloud account with Speech-to-Text and Translate APIs enabled
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
   # Install ffmpeg for pydub audio processing
   sudo apt-get install ffmpeg
   
   # Install Redis
   sudo apt-get install redis-server redis-tools
   ```

4. **Set up Google Cloud credentials**
   - Download your Google service account key JSON file
   - Place it in the project root as `healthorbit-ai.json`
   - Ensure the service account has access to:
     - Speech-to-Text API
     - Translate API
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

2. **Enable APIs** in your Google Cloud project:
   - Speech-to-Text API
   - Translate API
   - Cloud Storage API

3. **Set up recognizers**:
   - English: `projects/healthorbit-24052/locations/us-central1/recognizers/_`
   - Georgian: `projects/healthorbit-ai-446710/locations/global/recognizers/_`

## Running the Application

### Option 1: Using the startup script (Recommended)
```bash
python run.py
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

3. **Access the application**:
   - Web Interface: http://localhost:8000/georgian-transcription
   - API Documentation: http://localhost:8000/docs

## API Endpoints

### 1. English Transcription
- **POST** `/transcribe/`
- **Description**: Transcribe audio files in English
- **File Size Limit**: 100MB

### 2. Georgian Transcription
- **POST** `/transcribe-georgian/`
- **Description**: Transcribe audio files in Georgian
- **File Size Limit**: 100MB

### 3. Translation
- **POST** `/translate/`
- **Description**: Translate Georgian text to English
- **Request Body**:
  ```json
  {
    "text": "გამარჯობა",
    "source_language": "ka",
    "target_language": "en"
  }
  ```

### 4. Get Results
- **GET** `/result/{task_id}`
- **Description**: Get transcription results for a task

### 5. Web Interface
- **GET** `/georgian-transcription`
- **Description**: Web interface for audio transcription

## Usage Examples

### Using the Web Interface

1. Open http://localhost:8000/georgian-transcription
2. Upload an audio file (MP3, WAV, M4A, etc.)
3. Select language (English or Georgian)
4. Click "Start Transcription"
5. Wait for processing to complete
6. For Georgian transcriptions, click "Translate to English" if needed

### Using the API

```bash
# Transcribe Georgian audio
curl -X POST "http://localhost:8000/transcribe-georgian/" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio_file.mp3"

# Get results
curl "http://localhost:8000/result/{task_id}"

# Translate text
curl -X POST "http://localhost:8000/translate/" \
  -H "Content-Type: application/json" \
  -d '{"text": "გამარჯობა", "source_language": "ka", "target_language": "en"}'
```

## File Size Limits

- **Maximum file size**: 100MB
- **Supported formats**: MP3, WAV, M4A, FLAC, OGG
- **Processing**: Chunked upload for efficient handling

## Troubleshooting

### Common Issues

1. **Redis Connection Error**
   ```bash
   sudo systemctl start redis-server
   ```

2. **Google Cloud Credentials**
   - Ensure `healthorbit-ai.json` is in the project root
   - Verify API permissions in Google Cloud Console

3. **File Upload Errors**
   - Check file size (max 100MB)
   - Verify file format is supported
   - Ensure uploads_audios/ directory exists

4. **Translation Errors**
   - Verify Translate API is enabled
   - Check service account permissions

## Project Structure

```
GoogleChirp/
├── app.py                 # Main FastAPI application
├── run.py                 # Startup script
├── requirements.txt       # Python dependencies
├── healthorbit-ai.json   # Google Cloud credentials
├── uploads_audios/       # Upload directory
├── templates/            # HTML templates
│   └── index.html        # Web interface
└── README.md            # This file
```

## License

This project is licensed under the MIT License. 