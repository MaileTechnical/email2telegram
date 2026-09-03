# Email to Telegram

This project forwards incoming email from designated Gmail accounts to specific topics in an Arizona Free Flight Telegram group.

The system currently supports two forwarding paths:

- **Rescue:** `<rescueAddress>@gmail.com` → Rescue topic
- **Retrieve:** `<retrieveAddress>@gmail.com` → Retrieve topic

Each path is independent at the Gmail/Pub/Sub/Cloud Function level while sharing the Telegram bot and Google Cloud project.

## Architecture at a glance

```text
Gmail account
    │
    │ Gmail watch
    ▼
Google Pub/Sub topic
    │
    │ notification
    ▼
Cloud Function: email-to-telegram-*
    │
    │ Gmail API
    │ Telegram Bot API
    ▼
Arizona Free Flight Telegram topic
```

Gmail watches have a finite lifetime, so each path also has a scheduled renewal function:

```text
Cloud Scheduler
    │
    │ daily at 06:00 America/Phoenix
    ▼
Cloud Function: renew-gmail-watch-*
    │
    ▼
Gmail API users.watch()
```

## Documentation

- [Overview](docs/Overview.md) — purpose, scope, and system inventory
- [Design](docs/Design.md) — architecture and implementation
- [Operations](docs/Operations.md) — deployment, verification, monitoring, and troubleshooting
- [Maintenance](docs/Maintenance.md) — changing the system and adding forwarding paths
- [Contributing](docs/Contributing.md) — development workflow and repository portability

## Quick operational checks

From the `email2telegram/` directory:

```bash
gcloud functions list   --project=email-to-telegram-455900   --regions=us-central1   --format="table(name.basename(),buildConfig.runtime,state)"
```

```bash
gcloud scheduler jobs list   --location=us-central1   --project=email-to-telegram-455900   --format="table(name.basename(),state,schedule,timeZone)"
```

The four production functions should normally be `python313` and `ACTIVE`, and both Scheduler jobs should be `ENABLED`.

## Repository layout

The deployable project is the `email2telegram/` directory in this repository. The detailed system documentation lives under `email2telegram/docs/`.

Secrets and OAuth credential files are deliberately not stored in the public repository.
