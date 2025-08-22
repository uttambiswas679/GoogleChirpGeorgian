from google.oauth2 import service_account
from googleapiclient import discovery

def check_permissions(project_id, bucket_name, creds_path="creds.json"):
    credentials = service_account.Credentials.from_service_account_file(creds_path)

    # Build service clients
    storage_service = discovery.build('storage', 'v1', credentials=credentials)
    crm_service = discovery.build('cloudresourcemanager', 'v1', credentials=credentials)

    # Required permissions
    required_permissions = {
        "storage": [
            "storage.objects.get",
            "storage.objects.create",
            "storage.objects.delete",
            "storage.objects.list"   # 👈 also needed for listing files
        ],
        "speech": [
            "speech.recognizers.recognize"
        ]
    }

    print("🔍 Checking GCS bucket permissions...")
    storage_resp = storage_service.buckets().testIamPermissions(
        bucket=bucket_name,
        permissions=required_permissions["storage"]
    ).execute()

    print("GCS Permissions granted:", storage_resp.get("permissions", []))

    print("\n🔍 Checking Speech-to-Text permissions...")
    speech_resp = crm_service.projects().testIamPermissions(
        resource=project_id,
        body={"permissions": required_permissions["speech"]}
    ).execute()

    print("Speech Permissions granted:", speech_resp.get("permissions", []))

    # Final check
    missing_storage = set(required_permissions["storage"]) - set(storage_resp.get("permissions", []))
    missing_speech = set(required_permissions["speech"]) - set(speech_resp.get("permissions", []))

    if not missing_storage and not missing_speech:
        print("\n✅ You have all required permissions.")
    else:
        print("\n❌ Missing permissions:")
        if missing_storage:
            print("   Storage:", list(missing_storage))
        if missing_speech:
            print("   Speech:", list(missing_speech))

    return storage_service


def list_bucket_files(storage_service, bucket_name):
    """Fetch all files from a GCS bucket"""
    print(f"\n📂 Listing files in bucket: {bucket_name}")
    request = storage_service.objects().list(bucket=bucket_name)
    all_files = []

    while request is not None:
        response = request.execute()
        items = response.get("items", [])
        for obj in items:
            all_files.append(obj["name"])
            print(" -", obj["name"])
        request = storage_service.objects().list_next(previous_request=request, previous_response=response)

    if not all_files:
        print("⚠️ No files found in the bucket.")
    return all_files


if __name__ == "__main__":
    PROJECT_ID = "healthorbit-ai-446710"   # Replace with your GCP project ID
    BUCKET_NAME = "ho_georgian"            # Replace with your bucket
    CREDS_PATH = "healthorbit-ai.json"     # Path to your creds.json

    storage_service = check_permissions(PROJECT_ID, BUCKET_NAME, CREDS_PATH)
    list_bucket_files(storage_service, BUCKET_NAME)
