# Operations

## 1. Normal operation

Normally, no manual action is required.

Gmail watches are renewed daily by Cloud Scheduler. Incoming email causes Gmail Pub/Sub notifications, which invoke the appropriate forwarding function.

## 2. Check production status

### Functions

```bash
gcloud functions list   --project=email-to-telegram-455900   --regions=us-central1   --format="table(name.basename(),buildConfig.runtime,state)"
```

Expected:

```text
email-to-telegram-rescue    python313  ACTIVE
email-to-telegram-retrieve  python313  ACTIVE
renew-gmail-watch-rescue    python313  ACTIVE
renew-gmail-watch-retrieve  python313  ACTIVE
```

### Scheduler

```bash
gcloud scheduler jobs list   --location=us-central1   --project=email-to-telegram-455900   --format="table(name.basename(),state,schedule,timeZone)"
```

Expected:

```text
renew-gmail-watch-rescue-job    ENABLED  0 6 * * *  America/Phoenix
renew-gmail-watch-retrieve-job  ENABLED  0 6 * * *  America/Phoenix
```

## 3. Test forwarding

The most useful functional test is a real email.

### Rescue

Send an email to:

```text
rescueAddress
```

Verify that it appears in the Rescue Telegram topic.

### Retrieve

Send an email to:

```text
retrieveAddress
```

Verify that it appears in the Retrieve Telegram topic.

These tests exercise the complete forwarding path: Gmail, the watch, Pub/Sub, the Cloud Function, Gmail message retrieval, Secret Manager, Telegram authentication, and Telegram delivery.

## 4. Test watch renewal

A Scheduler job can be run immediately:

```bash
gcloud scheduler jobs run renew-gmail-watch-rescue-job   --location=us-central1   --project=email-to-telegram-455900
```

and:

```bash
gcloud scheduler jobs run renew-gmail-watch-retrieve-job   --location=us-central1   --project=email-to-telegram-455900
```

This exercises the production Scheduler → OIDC → renewal-function path.

## 5. View logs

### Forwarding

```bash
make logs SOLUTION=rescue
```

```bash
make logs SOLUTION=retrieve
```

Equivalent direct commands:

```bash
gcloud functions logs read email-to-telegram-rescue   --region=us-central1   --project=email-to-telegram-455900
```

```bash
gcloud functions logs read email-to-telegram-retrieve   --region=us-central1   --project=email-to-telegram-455900
```

### Watch renewal

```bash
make logs-watch SOLUTION=rescue
```

```bash
make logs-watch SOLUTION=retrieve
```

Equivalent direct commands:

```bash
gcloud functions logs read renew-gmail-watch-rescue   --region=us-central1   --project=email-to-telegram-455900
```

```bash
gcloud functions logs read renew-gmail-watch-retrieve   --region=us-central1   --project=email-to-telegram-455900
```

Use `--limit=N` when only recent entries are needed.

## 6. Troubleshooting a missing forwarded message

Work from the outside in.

### Step 1: Verify Gmail

Confirm that the email actually arrived in the expected Gmail inbox.
Check the Gmail Spam folder, and if the message is there, mark it as not spam.

### Step 2: Verify the Gmail watch

If both forwarding paths stop receiving messages, suspect the watch or Pub/Sub path.

Run the corresponding renewal Scheduler job manually and inspect its logs.

### Step 3: Check the forwarding function logs

Look for:

- Secret Manager failures
- Gmail API authentication errors
- Gmail API message retrieval errors
- Telegram HTTP errors
- Python exceptions

### Step 4: Check Telegram

Verify that:

- the bot is still a member of the group;
- the bot still has permission to post;
- the configured chat ID is correct;
- the configured topic ID is correct;
- the bot token is valid.

## 7. Troubleshooting a renewal failure

First verify the Scheduler job:

```bash
gcloud scheduler jobs describe renew-gmail-watch-rescue-job   --location=us-central1   --project=email-to-telegram-455900
```

or the retrieve equivalent.

Confirm:

- job is enabled;
- URI points to the correct renewal function;
- OIDC service account is configured;
- OIDC audience matches the function URL.

Then inspect the renewal function logs.

A successful manual Scheduler invocation only establishes that Scheduler accepted the request. The function logs should be checked to determine whether the Gmail `users.watch()` operation itself succeeded.

## 8. Deploying code

After a source change has been committed and pushed, deploy the affected function.

### Forwarding

```bash
make deploy-rescue
make deploy-retrieve
```

or both:

```bash
make deploy-all
```

### Watch renewal

```bash
make deploy-watch-rescue
make deploy-watch-retrieve
```

or both:

```bash
make deploy-watch-all
```

The `deploy-all` target means both forwarding functions; it does not include the renewal functions.

## 9. Scheduler configuration

Scheduler configuration is normally established with:

```bash
make schedule-watch-rescue
make schedule-watch-retrieve
```

or:

```bash
make schedule-watch-all
```

These targets create the job if it does not exist or update it if it does.

Do not recreate Scheduler jobs merely because application code was redeployed. Redeployment does not change the Scheduler configuration.

## 10. Python runtime upgrades

The current production runtime is Python 3.13.

For a future runtime upgrade:

1. Change the `--runtime` setting in the Makefile.
2. Inspect the resulting Git diff.
3. Commit and push the change.
4. Deploy the affected functions.
5. Verify the reported runtime and `ACTIVE` state.
6. Perform real forwarding tests.
7. Exercise both renewal Scheduler jobs.
8. Verify the Scheduler jobs remain enabled and correctly configured.

A runtime upgrade should be treated as a deployment change, not merely as a local Python installation change.

## 11. Recovery from a failed deployment

If a deployment fails:

1. Do not immediately modify unrelated configuration.
2. Inspect the deployment/build output.
3. Check the function state and runtime.
4. Review recent function logs.
5. Compare the working Git revision with the failed change.
6. If necessary, redeploy the last known-good revision from the local Git checkout.

Because Google Cloud resources and secrets are outside Git, restoring source code alone
is not sufficient to recreate the complete production system.

