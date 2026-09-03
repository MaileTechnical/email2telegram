# System Design

## 1. Architecture

There are two nearly identical forwarding paths. Route-specific configuration keeps the paths isolated while allowing them to share implementation.

```text
                           ┌─────────────────────┐
                           │ Gmail: rescue       │
                           └──────────┬──────────┘
                                      │ watch
                                      ▼
                           ┌─────────────────────┐
                           │ Pub/Sub: rescue     │
                           └──────────┬──────────┘
                                      │
                                      ▼
                           ┌─────────────────────┐
                           │ email-to-telegram-  │
                           │ rescue              │
                           └──────────┬──────────┘
                                      │
                                      ▼
                           ┌─────────────────────┐
                           │ Telegram: Rescue    │
                           └─────────────────────┘


                           ┌─────────────────────┐
                           │ Gmail: retrieve     │
                           └──────────┬──────────┘
                                      │ watch
                                      ▼
                           ┌─────────────────────┐
                           │ Pub/Sub: retrieve   │
                           └──────────┬──────────┘
                                      │
                                      ▼
                           ┌─────────────────────┐
                           │ email-to-telegram-  │
                           │ retrieve            │
                           └──────────┬──────────┘
                                      │
                                      ▼
                           ┌─────────────────────┐
                           │ Telegram: Retrieve  │
                           └─────────────────────┘
```

Watch renewal is independent of message forwarding:

```text
Cloud Scheduler
      │
      │ 06:00 daily
      ▼
renew-gmail-watch-rescue ──► Gmail users.watch()
renew-gmail-watch-retrieve ─► Gmail users.watch()
```

## 2. Forwarding function

The entry point is `handle_request(event, context)` in `main.py`.

### Authentication

The function obtains the configured Gmail OAuth token from Secret Manager. The secret name comes from `GMAIL_TOKEN_SECRET`.

The token is converted into Google OAuth credentials with the Gmail `modify` scope.

The Telegram bot token is also retrieved from Secret Manager using `TELEGRAM_BOT_TOKEN_SECRET`.

### Message discovery

The function calls Gmail:

```text
users.messages.list(
    userId="me",
    labelIds=["INBOX", "UNREAD"],
    maxResults=5
)
```

The Pub/Sub event is therefore treated as a signal to inspect the inbox; the notification payload itself is not used as the email message.

### Message extraction

Each message is retrieved with `format="full"`.

The implementation extracts:

- `Subject`
- `From`
- the first available `text/plain` body part

If no subject or sender header exists, fallback values are used.

HTML-only multipart content is not converted to plain text.

### Telegram delivery

The message is formatted as:

```text
*From:* sender
*Subject:* subject

body
```

Only the first 1,000 characters of the body are forwarded.

The configured `TELEGRAM_CHAT_ID` and `TELEGRAM_TOPIC_ID` determine the destination.

Telegram Markdown parsing is enabled.

A successful HTTP response is required before the Gmail message is marked read.

### Error handling

The forwarding entry point catches exceptions only to print the traceback, then re-raises the exception. This allows the platform to record the invocation as failed.

The forwarding triggers are configured to retry failed event deliveries.

This provides **at-least-once delivery** rather than at-most-once delivery. Eventarc can deliver an event more than once, so the forwarding function can receive duplicate events.

The retry behavior is intentional. A transient failure is more serious for this application than an occasional duplicate Telegram message. Without retries, a failed invocation could leave an unread Gmail message waiting indefinitely until some later Gmail notification happens to cause another invocation. With retries enabled, a failed invocation is automatically attempted again.

### Duplicate delivery

The forwarding operation cannot provide exactly-once delivery because Gmail and Telegram are independent external systems.

The important sequence is:

```text
send message to Telegram
        │
        ├── Telegram accepts message
        │
        └── function fails before completing successfully
                │
                ▼
             retry
                │
                ▼
        same Gmail message may be
        sent to Telegram again
```

This can happen, for example, if Telegram accepts the request but the response is lost or times out.

The implementation reduces duplicate exposure by marking the Gmail message read only after successful Telegram delivery. A retry therefore normally encounters only messages that remain unread.

Nevertheless, duplicate Telegram delivery is possible and is an accepted limitation.

Google recommends that retryable event handlers be idempotent because Eventarc provides at-least-once delivery. In this application, complete idempotency across Gmail and Telegram is not practical without adding persistent delivery state or an idempotency facility from the destination service. The system instead favors eventual delivery over strict duplicate avoidance.

### Retry policy

Retries are enabled on the forwarding functions through the `--retry` option in the Makefile.

The renewal functions do not use this event-trigger retry policy. Their HTTP invocations are retried independently by Cloud Scheduler according to the Scheduler configuration.

## 3. Gmail watch renewal

The renewal implementation is in `renew_watch/renew_watch.py`, with `app()` as the HTTP entry point.

For its route, it:

1. Reads `GCP_PROJECT`, `GMAIL_TOKEN_SECRET`, and `GMAIL_PUBSUB_TOPIC`.
2. Retrieves the Gmail OAuth token from Secret Manager.
3. Refreshes the OAuth credentials when possible.
4. Calls Gmail `users.watch()`.
5. Requests notifications for the Inbox and specifies the route's Pub/Sub topic.
6. Returns a JSON response containing success status and the Gmail watch response.

Exceptions are converted into an HTTP 500 response containing an error message.

## 4. Scheduler

Each renewal function has a corresponding Cloud Scheduler job.

The Makefile configures:

- schedule: `0 6 * * *`
- time zone: `America/Phoenix`
- HTTP method: `GET`
- OIDC service account: `506739284793-compute@developer.gserviceaccount.com`
- OIDC audience: the Cloud Function URL
- attempt deadline: `180s`
- maximum retry attempts: `3`
- minimum backoff: `5s`
- maximum backoff: `3600s`
- maximum doublings: `16`

The Scheduler jobs are independent of the forwarding functions.

## 5. Configuration

Each route has an environment file, `.env.<routeName>.yaml`, containing values specific to that route such as,
the Gmail token secret, Telegram topic, and Pub/Sub topic.

The environment files do not contain the actual secret values.

## 6. Secrets

Secret Manager contains:

- one Gmail OAuth token per forwarding path;
- one shared Telegram bot token.

OAuth token generation is supported by `utils/genOauthToken.py`. Credential material used to generate or maintain the tokens is not part of the public repository.

## 7. Deployment model

The Makefile is the operational interface to deployment.

Forwarding functions are deployed from the project root with `--source=.` and retries enabled.

Renewal functions are deployed from `renew_watch/` with `--source=renew_watch`.

All four production functions currently use Python 3.13.

## 8. Design rationale

### Separate routes

Separate functions, Pub/Sub topics, and Gmail tokens prevent a configuration mistake in one route from directly changing the destination of another.

### Shared Telegram bot

The Telegram bot is authorized to post to any topic within a Telegram group to which the
bot has been added as a member.  It provides no other capabilities in this system.

### Scheduled watch renewal

Renewal is intentionally independent of forwarding.
A failure of a renewal invocation should be diagnosable without changing the forwarding implementation.

### Configuration in environment files

Route-specific deployment settings are kept outside the Python implementation.
This makes adding another route mostly a deployment/configuration task which should require no code changes.

### Retry versus duplicate delivery

The system favors **at-least-once delivery** over at-most-once delivery.

A missed rescue or retrieve message can have operational consequences, whereas a duplicate Telegram message is primarily an inconvenience. Enabling retries therefore provides the more appropriate reliability tradeoff for this application.

The tradeoff is accepted because the forwarding path crosses two independent systems—Gmail and Telegram—and cannot atomically mark a Gmail message as processed at the same time that it sends the Telegram message.

### Repository portability

Nothing in the runtime design depends on the GitHub repository owner or repository URL.
Google Cloud deployment is based on the local source directory and explicit Google Cloud resource names.
