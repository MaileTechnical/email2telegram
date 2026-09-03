import os
import google.auth
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scopes required for your app
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

# Authenticate the user
def authenticate():
    creds = None
    if os.path.exists('token.json'):
        creds, _ = google.auth.load_credentials_from_file('token.json')

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

    return creds

# Re-authenticate Gmail with new token
creds = authenticate()
service = build('gmail', 'v1', credentials=creds)
print("Successfully authenticated with Gmail.")

