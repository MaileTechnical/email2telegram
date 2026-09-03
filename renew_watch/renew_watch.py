import os
import json

from flask import Request, jsonify
from google.cloud import secretmanager
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def get_secret(project_id, secret_name):
    client = secretmanager.SecretManagerServiceClient()
    secret_path = (
        f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    )
    response = client.access_secret_version(
        request={"name": secret_path}
    )
    return response.payload.data.decode("UTF-8")


def app(request: Request):
    project_id = os.environ["GCP_PROJECT"]
    secret_name = os.environ["GMAIL_TOKEN_SECRET"]
    pubsub_topic = os.environ["GMAIL_PUBSUB_TOPIC"]

    try:
        token_data = json.loads(
            get_secret(project_id, secret_name)
        )

        creds = Credentials.from_authorized_user_info(token_data)

        if not creds.valid and creds.expired and creds.refresh_token:
            creds.refresh(GoogleRequest())

        service = build("gmail", "v1", credentials=creds)

        result = service.users().watch(
            userId="me",
            body={
                "labelIds": ["INBOX"],
                "topicName": (
                    f"projects/{project_id}/topics/{pubsub_topic}"
                ),
            },
        ).execute()

        return jsonify(
            {
                "success": True,
                "gmail_token_secret": secret_name,
                "pubsub_topic": pubsub_topic,
                "watch_response": result,
            }
        )

    except Exception as e:
        return jsonify(
            {
                "success": False,
                "gmail_token_secret": secret_name,
                "pubsub_topic": pubsub_topic,
                "error": str(e),
            }
        ), 500
