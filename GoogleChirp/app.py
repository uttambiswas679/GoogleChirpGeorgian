import os
import subprocess
import json
import datetime
import random
import string
import re
from fastapi import FastAPI, File, UploadFile, Request
from pydub import AudioSegment
from google.api_core.client_options import ClientOptions
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech
from google.cloud import speech
from google.cloud import storage
from google.cloud import translate
from google.protobuf.json_format import MessageToJson
from celery import Celery
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


MAX_AUDIO_LENGTH_SECS = 8 * 60 * 60

os.environ['GOOGLE_APPLICATION_CREDENTIALS']= 'healthorbit-ai.json'

# Celery setup
celery_app = Celery("tasks", broker="redis://localhost:6379/0", backend="redis://localhost:6379/1", broker_connection_retry_on_startup=True)

# FastAPI app with increased file upload limits
fastapi_app = FastAPI(
    title="Audio Transcription Service",
    description="Upload audio files for transcription in multiple languages",
    version="1.0.0"
)

# Pydantic model for translation request
class TranslationRequest(BaseModel):
    text: str
    source_language: str = "ka"
    target_language: str = "en"

# Simple root route for testing
@fastapi_app.get("/")
async def root():
    return {
        "message": "Audio Transcription Service",
        "endpoints": {
            "transcribe_english": "/transcribe/",
            "transcribe_georgian": "/transcribe-georgian/",
            "get_result": "/result/{task_id}",
            "translate": "/translate/",
            "docs": "/docs"
        }
    }

fastapi_app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@fastapi_app.get("/georgian-transcription", response_class=HTMLResponse)
async def render_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Translation endpoint
@fastapi_app.post("/translate/")
async def translate_text(request: TranslationRequest):
    try:
        # Try Google Cloud Translate API first
        try:
            translate_client = translate.TranslationServiceClient()
            parent = f"projects/healthorbit-ai/locations/global"
            
            response = translate_client.translate_text(
                request={
                    "parent": parent,
                    "contents": [request.text],
                    "mime_type": "text/plain",
                    "source_language_code": request.source_language,
                    "target_language_code": request.target_language,
                }
            )
            
            translation = response.translations[0].translated_text
            return {"translation": translation, "method": "google_translate"}
            
        except Exception as e:
            print(f"Google Translate API failed: {e}")
            # Fallback: return original text with a note
            return {
                "translation": f"[Translation service unavailable] {request.text}",
                "method": "fallback",
                "error": "Translation service temporarily unavailable"
            }
            
    except Exception as e:
        return {"error": f"Translation failed: {str(e)}"}


# Celery task for transcription
@celery_app.task(bind=True, time_limit=3600, soft_time_limit=3300)  # 1 hour max, 55 min soft limit
def process_transcription(self, audio_path, language_config="english"):
    try:
        # Check if input file exists
        if not os.path.exists(audio_path):
            return {"error": f"Input audio file not found: {audio_path}"}
        
        # Preprocess audio locally
        processed_audio_path = preprocess_audio_local(audio_path)
        
        if not processed_audio_path or not os.path.exists(processed_audio_path):
            return {"error": "Audio processing failed"}
        
        # Get transcription using standard Speech API
        transcription_result = run_batch_recognize(processed_audio_path, language_config)
        
        # Clean up processed file
        if os.path.exists(processed_audio_path):
            os.remove(processed_audio_path)
            print(f"Cleaned up processed file: {processed_audio_path}")
        
        return transcription_result
    
    except Exception as e:
        print(f"Error in process_transcription: {e}")
        return {"error": str(e)}

# Celery task for Georgian transcription
@celery_app.task(bind=True, time_limit=3600, soft_time_limit=3300)  # 1 hour max, 55 min soft limit
def process_georgian_transcription(self, audio_path):
    try:
        print(f"Processing Georgian transcription for: {audio_path}")
        
        # Check if input file exists
        if not os.path.exists(audio_path):
            return {"error": f"Input audio file not found: {audio_path}"}
        
        # Preprocess audio locally
        processed_audio_path = preprocess_audio_local(audio_path)
        
        if not processed_audio_path or not os.path.exists(processed_audio_path):
            return {"error": "Audio processing failed"}
        
        # Get transcription using standard Speech API
        transcription_result = run_batch_recognize(processed_audio_path, "georgian")
        
        # Clean up processed file
        if os.path.exists(processed_audio_path):
            os.remove(processed_audio_path)
            print(f"Cleaned up processed file: {processed_audio_path}")
        
        return transcription_result
    
    except Exception as e:
        print(f"Error in process_georgian_transcription: {e}")
        return {"error": str(e)}

#------------------------------------------------------------------------------------------------------
# FastAPI endpoint
@fastapi_app.post("/transcribe/")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        # Validate file size (max 100MB)
        MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB in bytes
        
        # Read file in chunks to handle large files efficiently
        generatefilename = generate_unique_filename()
        audio_path = f"uploads_audios/{generatefilename + file.filename}"
        
        with open(audio_path, "wb") as f:
            total_size = 0
            chunk_size = 1024 * 1024  # 1MB chunks
            
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                    
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE:
                    # Clean up partial file
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
                    return {"error": f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"}
                
                f.write(chunk)
        
        task = process_transcription.delay(audio_path, "english")
        return {"task_id": task.id, "message": "Transcription in progress. Use /result/{task_id} to fetch the result."}
    except Exception as e:
        return {"error": str(e)}

# FastAPI endpoint for Georgian transcription
@fastapi_app.post("/transcribe-georgian/")
async def transcribe_georgian_audio(file: UploadFile = File(...)):
    try:
        # Validate file size (max 100MB)
        MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB in bytes
        
        # Read file in chunks to handle large files efficiently
        generatefilename = generate_unique_filename()
        audio_path = f"uploads_audios/{generatefilename + file.filename}"
        
        with open(audio_path, "wb") as f:
            total_size = 0
            chunk_size = 1024 * 1024  # 1MB chunks
            
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                    
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE:
                    # Clean up partial file
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
                    return {"error": f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"}
                
                f.write(chunk)
        
        task = process_georgian_transcription.delay(audio_path)
        return {"task_id": task.id, "message": "Georgian transcription in progress. Use /result/{task_id} to fetch the result."}
    except Exception as e:
        return {"error": str(e)}

#------------------------------------------------------------------------------------------------------
# Endpoint to get transcription result
@fastapi_app.get("/result/{task_id}")
async def get_result(task_id: str):
    result = celery_app.AsyncResult(task_id)
    if result.state == "PENDING":
        return {"status": "pending", "message": "Task is still in progress."}
    elif result.state == "SUCCESS":
        return {"status": "success", "result": result.result}
    else:
        return {"status": "failure", "message": result.info}      
#------------------------------------------------------------------------------------------------------

# General Functions
#------------------------------------------------------------------------------------------------------
# Function to generate a newfilename
def generate_unique_filename():
    prefix="HOAudio_"
    # Get current time in microseconds
    microseconds = datetime.datetime.now().microsecond
    # Generate a random string of 8 characters
    random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    # Combine prefix, microseconds, and random string
    filename = f"{prefix}{microseconds}{random_string}"
    return filename
#------------------------------------------------------------------------------------------------------
# Function to extract data from url without prefix 
def extract_uri(response_str):
  lines = response_str.splitlines()
  for line in lines:
    if "uri:" in line:
      uri = line.split(": ")[1].strip() 
      # Remove the bucket prefix
      uri = uri.replace("gs://ho_georgian/", "") 
      return uri
  return None
#------------------------------------------------------------------------------------------------------
#Funtion to Extracts the first occurrence of a URI from the given result string.
def get_first_uri(result_string):
  match = re.search(r'uri:\s*"(.*?)"', result_string)
  if match:
    return match.group(1)
  else:
    return None
  
def remove_gs_bucket_prefix(path):
  if path.startswith("gs://healthorbit_bucket/"):
    return path[len("gs://healthorbit_bucket/"):]
  else:
    return path

def remove_gs_bucket_prefix_georgian(path):
  if path.startswith("gs://ho_georgian/"):
    return path[len("gs://ho_georgian/"):]
  else:
    return path
  
def remove_local_pathsuffix(path):
  if path.startswith("uploads_audios/"):
    return path[len("uploads_audios/"):]
  else:
    return path  
#------------------------------------------------------------------------------------------------------

# Function to preprocess audio locally
def preprocess_audio_local(audio_path, target_sample_rate=16000):
    try:
        # Check if input file exists
        if not os.path.exists(audio_path):
            print(f"Error: Input audio file does not exist: {audio_path}")
            return None
            
        # Create a temporary file for the processed audio
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            processed_audio_path = tmp_file.name
        
        # Load audio with pydub
        audio = AudioSegment.from_file(audio_path)

        # Convert to mono and set the sample rate
        audio = audio.set_channels(1).set_frame_rate(target_sample_rate)

        # Export to the temporary WAV file
        audio.export(processed_audio_path, format="wav")
        
        # Verify the processed file was created
        if not os.path.exists(processed_audio_path):
            print(f"Error: Processed audio file was not created: {processed_audio_path}")
            return None
        
        print(f"Audio successfully processed locally and saved at: {processed_audio_path}")
        
        # Remove the original file
        try:
            os.remove(audio_path)
            print(f"Deleted the original audio file: {audio_path}")
        except OSError as e:
            print(f"Warning: Could not delete original audio file: {e}")

        return processed_audio_path
        
    except Exception as e:
        print(f"Error during local audio processing: {e}")
        return None

#------------------------------------------------------------------------------------------------------

# Function to preprocess large audio files
def preprocess_audio(audio_path, destination_blob_name, target_sample_rate=16000):
    try:
        # Check if input file exists
        if not os.path.exists(audio_path):
            print(f"Error: Input audio file does not exist: {audio_path}")
            return None
            
        # Load audio with pydub
        audio = AudioSegment.from_file(audio_path)

        # Convert to mono and set the sample rate
        audio = audio.set_channels(1).set_frame_rate(target_sample_rate)

        # Export to a temporary WAV file
        processed_audio_path = destination_blob_name
        audio.export(processed_audio_path, format="wav")
        
        # Verify the processed file was created
        if not os.path.exists(processed_audio_path):
            print(f"Error: Processed audio file was not created: {processed_audio_path}")
            return None
        
        print(f"Audio successfully processed with pydub and saved at: {processed_audio_path}")
        
        # Remove the original file
        try:
            os.remove(audio_path)
            print(f"Deleted the original audio file: {audio_path}")
        except OSError as e:
            print(f"Warning: Could not delete original audio file: {e}")

        return processed_audio_path
        
    except Exception as e:
        print(f"Error during audio processing with pydub: {e}")
        return None

# Function to preprocess large audio files using sox
def preprocess_audio_with_sox(audio_path, destination_blob_name, target_sample_rate=16000):
    # Check if input file exists
    if not os.path.exists(audio_path):
        print(f"Error: Input audio file does not exist: {audio_path}")
        return None
    
    # For MP3 files, use pydub instead of sox since sox doesn't handle MP3 well
    file_extension = os.path.splitext(audio_path)[1].lower()
    if file_extension in ['.mp3', '.m4a']:
        print(f"Using pydub for {file_extension} file processing...")
        return preprocess_audio(audio_path, destination_blob_name, target_sample_rate)
    
    # Construct the sox command for other formats
    processed_audio_path = destination_blob_name
    sox_command = [
        "sox",
        audio_path,              # Input file
        processed_audio_path,    # Output file
        "rate", str(target_sample_rate),  # Set sample rate
        "channels", "1"          # Convert to mono
    ]

    try:
        # Run the sox command
        subprocess.run(sox_command, check=True)
        print(f"Audio successfully processed with sox and saved at: {processed_audio_path}")

        # Remove the original file if processing was successful
        if os.path.exists(processed_audio_path):
            os.remove(audio_path)
            print(f"Deleted the original audio file: {audio_path}")
        else:
            print(f"Warning: Processed file was not created: {processed_audio_path}")
            return None

    except subprocess.CalledProcessError as e:
        print(f"Error during audio processing with sox: {e}")
        # Fallback to pydub if sox fails
        print("Falling back to pydub processing...")
        return preprocess_audio(audio_path, destination_blob_name, target_sample_rate)
    except OSError as e:
        print(f"Error deleting the original audio file: {e}")

    return processed_audio_path

#------------------------------------------------------------------------------------------------------
# Function to upload audio to Google Cloud Storage
def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    return f"gs://{bucket_name}/{destination_blob_name}"
#------------------------------------------------------------------------------------------------------
# Function to Get audio from Google Cloud Storage
#------------------------------------------------------------------------------------------------------
def get_file_from_bucket(bucket_name, file_path):
    try:
        # Create a client to interact with Google Cloud Storage
        storage_client = storage.Client()

        # Get the bucket object
        bucket = storage_client.get_bucket(bucket_name)

        # Get the blob object representing the file
        blob = bucket.blob(file_path)

        # Download the file contents as a string
        file_contents = blob.download_as_text()

        # Parse the JSON data
        json_data = json.loads(file_contents)

        return json_data

    except Exception as e:
        print(f"Error retrieving file from bucket: {e}")
        return None
#------------------------------------------------------------------------------------------------------  

#Main Function to Generate transcript
def run_batch_recognize(audio_path, language_config="english"):
    try:
        # Create Speech client
        client = speech.SpeechClient()
        
        # Configure recognition based on language
        if language_config == "georgian" or language_config == "ho_georgian":
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="ka-GE",  # Georgian language code
                alternative_language_codes=["en-US", "ru-RU"],  # Fallback languages
                enable_word_time_offsets=True,
                enable_word_confidence=True,
                enable_automatic_punctuation=True,
            )
        else:
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="en-US",
                enable_word_time_offsets=True,
                enable_word_confidence=True,
                enable_automatic_punctuation=True,
            )
        
        # Read the audio file
        with open(audio_path, "rb") as audio_file:
            content = audio_file.read()
        
        # Check file size to determine if we need GCS upload
        file_size = len(content)
        # Rough estimate: 1 minute of 16kHz mono audio is about 1.9MB
        one_minute_size = 16000 * 2 * 60  # 16kHz * 2 bytes * 60 seconds
        
        if file_size > one_minute_size:
            # Upload to GCS for longer audio
            print(f"Audio file is {file_size} bytes, uploading to GCS for processing")
            
            # Generate a unique filename for GCS
            import uuid
            gcs_filename = f"temp_audio_{uuid.uuid4()}.wav"
            bucket_name = "ho_georgian"
            
            # Upload to GCS
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(gcs_filename)
            blob.upload_from_filename(audio_path)
            
            # Create GCS URI
            gcs_uri = f"gs://{bucket_name}/{gcs_filename}"
            
            # Use long running recognition with GCS URI
            audio = speech.RecognitionAudio(uri=gcs_uri)
            operation = client.long_running_recognize(config=config, audio=audio)
            
            # Calculate timeout based on audio length (roughly 2x audio duration + 60 seconds buffer)
            # For safety, cap at 30 minutes maximum
            audio_duration_estimate = file_size / (16000 * 2)  # Rough estimate in seconds
            timeout_seconds = min(audio_duration_estimate * 2 + 60, 1800)  # Max 30 minutes
            
            print(f"Audio estimated duration: {audio_duration_estimate:.1f}s, using timeout: {timeout_seconds}s")
            response = operation.result(timeout=timeout_seconds)
            
            # Clean up GCS file
            try:
                blob.delete()
                print(f"Cleaned up GCS file: {gcs_filename}")
            except Exception as e:
                print(f"Warning: Could not clean up GCS file: {e}")
                
        else:
            # Use inline audio for shorter files
            print(f"Audio file is {file_size} bytes, using inline processing")
            audio = speech.RecognitionAudio(content=content)
            response = client.recognize(config=config, audio=audio)
        
        # Process results
        output_data = []
        for result in response.results:
            for alternative in result.alternatives:
                entry = {
                    "start_time": f"{alternative.words[0].start_time.total_seconds()}s" if alternative.words else "0.0s",
                    "end_time": f"{alternative.words[-1].end_time.total_seconds()}s" if alternative.words else "0.0s",
                    "language_code": language_config,
                    "confidence": alternative.confidence,
                    "transcript": alternative.transcript,
                }
                output_data.append(entry)
        
        if not output_data:
            return {"error": "No transcription results found"}
        
        return {"transcription": output_data}
        
    except Exception as e:
        print(f"Error in run_batch_recognize: {e}")
        error_message = str(e)
        
        # Handle specific timeout errors
        if "timeout" in error_message.lower() or "deadline" in error_message.lower():
            return {"error": "Transcription timed out. Please try with a shorter audio file or contact support."}
        elif "permission" in error_message.lower():
            return {"error": "Permission denied. Please check your Google Cloud credentials."}
        else:
            return {"error": f"Transcription failed: {error_message}"}