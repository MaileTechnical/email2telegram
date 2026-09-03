# System Overview

## 1. Purpose

Email to Telegram is an unattended notification bridge for Arizona Free Flight operations.

It watches designated Gmail inboxes and forwards newly received email to corresponding topics in a Telegram group. The primary use is operational communication for pilots who may send email through satellite communicators when they are outside cellular coverage.

The system is deliberately small. It does not attempt to become a general-purpose email gateway, Telegram client, or message archive.

## 2. Current forwarding paths

| Path | Gmail account | Pub/Sub topic | Telegram topic |
|---|---|---|---|
| Rescue | `rescueAddress` | `gmail-notifications-rescue` | `4309` |
| Retrieve | `retrieveAddress` | `gmail-notifications-retrieve` | `13792` |

Both paths use the same Telegram group and bot, but separate Gmail OAuth tokens, Pub/Sub topics, Cloud Functions, and Telegram topics.

## 3. External services

The system depends on:

- **Gmail / Gmail API** — receives mail and provides the watch and message APIs.
- **Google Cloud Pub/Sub** — carries Gmail watch notifications.
- **Google Cloud Functions (2nd gen / Cloud Run functions)** — runs the forwarding and watch-renewal Python code.
- **Google Cloud Scheduler** — invokes the renewal functions daily.
- **Google Cloud Secret Manager** — stores Gmail OAuth tokens and the Telegram bot token.
- **Telegram Bot API** — delivers forwarded messages to the selected group topic.

The production Google Cloud project is `email-to-telegram-455900`, in region `us-central1`.

## 4. Normal operation

Normal operation requires no manual intervention.

For each Gmail account:

1. Gmail receives an email.
2. Gmail's watch publishes a notification to that account's Pub/Sub topic.
3. The corresponding forwarding Cloud Function runs.
4. The function queries Gmail for unread messages in the Inbox.
5. It retrieves each message, extracts sender, subject, and plain-text body, and sends it to the configured Telegram topic.
6. After successful Telegram delivery, the Gmail message is marked read.

Because Gmail watches expire, a separate renewal function calls Gmail `users.watch()` daily.

## 5. Operational characteristics and limitations

The current forwarding implementation:

- processes up to five unread Inbox messages per function invocation;
- forwards the first available `text/plain` body part;
- truncates the forwarded body to 1,000 characters;
- uses Telegram Markdown formatting;
- marks a message read only after the Telegram request succeeds;
- re-raises forwarding exceptions so the Cloud Function invocation is reported as failed.

The forwarding function is event-driven; it does not poll Gmail on a timer.

The renewal functions are HTTP-triggered and are not configured for unauthenticated access. Cloud Scheduler invokes them using OIDC authentication.

## 6. Production inventory

### Forwarding functions

- `email-to-telegram-rescue`
- `email-to-telegram-retrieve`

### Renewal functions

- `renew-gmail-watch-rescue`
- `renew-gmail-watch-retrieve`

### Pub/Sub topics

- `gmail-notifications-rescue`
- `gmail-notifications-retrieve`

### Scheduler jobs

- `renew-gmail-watch-rescue-job`
- `renew-gmail-watch-retrieve-job`

Both run at `06:00` in `America/Phoenix`.

### Secrets

- `gmail_token_azffrescue`
- `gmail_token_azffretrieve`
- `telegram_bot_token`

The secret values themselves must never be committed to Git.
