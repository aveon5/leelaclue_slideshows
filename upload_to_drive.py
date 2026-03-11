import os
import argparse
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def authenticate_google_drive():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

def get_or_create_folder(service, folder_name, parent_id=None):
    """Finds a folder by name or creates it if it doesn't exist."""
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
        
    results = service.files().list(q=query, spaces='drive', fields='nextPageToken, files(id, name)').execute()
    items = results.get('files', [])
    
    if items:
        # Return the first found folder ID
        return items[0]['id']
    else:
        # Create the folder
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            folder_metadata['parents'] = [parent_id]
            
        folder = service.files().create(body=folder_metadata, fields='id').execute()
        print(f"    [+] Created new folder '{folder_name}' on Drive.")
        return folder.get('id')
        
def file_exists_in_folder(service, file_name, parent_id):
    """Checks if a file already exists in the given Google Drive folder."""
    query = f"name='{file_name}' and '{parent_id}' in parents and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    items = results.get('files', [])
    return len(items) > 0

def upload_file(service, file_path, parent_id):
    """Uploads a single file to the specified Google Drive folder."""
    file_name = file_path.name
    
    if file_exists_in_folder(service, file_name, parent_id):
        print(f"      [Skip] '{file_name}' already exists in Drive folder.")
        return
        
    file_metadata = {
        'name': file_name,
        'parents': [parent_id]
    }
    media = MediaFileUpload(str(file_path), mimetype='image/jpeg', resumable=True)
    
    print(f"      Uploading: {file_name}...")
    service.files().create(body=file_metadata, media_body=media, fields='id').execute()

def main():
    parser = argparse.ArgumentParser(description="Upload generated _Text.jpg slides to Google Drive.")
    parser.add_argument("--input_dir", type=str, default="scenario_assets_text", help="Local directory containing the scenario folders.")
    parser.add_argument("--drive_root_folder_id", type=str, required=True, help="The ID of the Root Google Drive folder where scenarios should be uploaded.")
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"Error: Local directory '{input_dir}' not found.")
        return
        
    # Check for credentials before attempting auth
    if not os.path.exists('credentials.json') and not os.path.exists('token.json'):
         print("Error: 'credentials.json' not found. Please download your OAuth 2.0 Client credentials from the Google Cloud Console and place them in this folder.")
         return
         
    print("Authenticating with Google Drive...")
    service = authenticate_google_drive()
    print("Authentication successful.")
    
    # Iterate through scenario folders
    scenario_folders = sorted([f for f in input_dir.iterdir() if f.is_dir() and f.name.startswith("scenario_")])
    if not scenario_folders:
        print(f"No scenario folders found in '{input_dir}'.")
        return
        
    print(f"Found {len(scenario_folders)} scenarios. Beginning upload...")
    
    for local_folder in scenario_folders:
        print(f"\n--> Processing {local_folder.name}")
        
        # Find all _Text images in the local folder
        text_images = sorted(list(local_folder.glob("*_Text.jpg")))
        
        if not text_images:
            print(f"    No _Text.jpg files found in {local_folder.name}. Skipping.")
            continue
            
        print(f"    Found {len(text_images)} text images.")
        
        # Get or create the scenario folder on Google Drive
        drive_scenario_folder_id = get_or_create_folder(service, local_folder.name, args.drive_root_folder_id)
        
        # Upload each image
        for img_path in text_images:
            upload_file(service, img_path, drive_scenario_folder_id)
            
    print("\nUpload complete!")

if __name__ == "__main__":
    main()
