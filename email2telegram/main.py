import base64
import os
import json

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.cloud import secretmanager
import requests


# Environment variables
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
TELEGRAM_TOPIC_ID = int(os.environ.get("TELEGRAM_TOPIC_ID", "0"))
GCP_PROJECT = os.environ.get("GCP_PROJECT")


def get_secret(secret_name):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{GCP_PROJECT}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


def authenticate_gmail():
    token_data = get_secret(os.environ["GMAIL_TOKEN_SECRET"])
    creds = Credentials.from_authorized_user_info(
        json.loads(token_data),
        SCOPES
    )
    return build('gmail', 'v1', credentials=creds)


def get_unread_message_ids(service, max_results=5):
    response = service.users().messages().list(
        userId='me',
        labelIds=['INBOX', 'UNREAD'],
        maxResults=max_results
    ).execute()
    messages = response.get('messages', [])
    return [msg['id'] for msg in messages]


def get_email_message(service, message_id):
    msg = service.users().messages().get(
        userId='me',
        id=message_id,
        format='full'
    ).execute()

    headers = {
        h['name']: h['value']
        for h in msg['payload']['headers']
    }

    subject = headers.get('Subject', '(No Subject)')
    from_email = headers.get('From', '(Unknown Sender)')

    body = ''
    parts = msg['payload'].get('parts', [])

    if parts:
        for part in parts:
            if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                body = base64.urlsafe_b64decode(
                    part['body']['data']
                ).decode('utf-8', errors='ignore')
                break
    else:
        if 'data' in msg['payload']['body']:
            body = base64.urlsafe_b64decode(
                msg['payload']['body']['data']
            ).decode('utf-8', errors='ignore')

    return {
        'id': msg['id'],
        'from': from_email,
        'subject': subject,
        'body': body
    }


def mark_as_read(service, message_id):
    service.users().messages().modify(
        userId='me',
        id=message_id,
        body={'removeLabelIds': ['UNREAD']}
    ).execute()


def send_to_telegram(subject, sender, body):
    text = f"*From:* {sender}\n*Subject:* {subject}\n\n{body[:1000]}"

    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'message_thread_id': TELEGRAM_TOPIC_ID,
        'text': text,
        'parse_mode': 'Markdown'
    }

    telegram_bot_token = get_secret(
        os.environ["TELEGRAM_BOT_TOKEN_SECRET"]
    )

    url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"

    response = requests.post(
        url,
        json=payload,
        timeout=10
    )
    response.raise_for_status()


def handle_request(event, context):
    try:
        service = authenticate_gmail()
        message_ids = get_unread_message_ids(service)

        for message_id in message_ids:
            msg = get_email_message(service, message_id)

            send_to_telegram(
                msg['subject'],
                msg['from'],
                msg['body']
            )

            mark_as_read(service, message_id)

    except Exception:
        import traceback
        traceback.print_exc()
        raise
