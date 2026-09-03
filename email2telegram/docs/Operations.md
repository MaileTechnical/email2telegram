# Operations

## 1. Normal operation

Normally, no manual action is required.

Gmail watches are renewed daily by Cloud Scheduler. Incoming email causes Gmail Pub/Sub notifications, which invoke the appropriate forwarding function.

Forwarding functions are configured to retry failed event deliveries. This means a transient failure should normally result in another delivery attempt without waiting for another incoming email.

Because event delivery is at-least-once, duplicate event delivery and consequently duplicate Telegram messages are possible. This is an accepted tradeoff in favor of avoiding lost messages.

## 2. Check production status

### Functions

```bash
gcloud functions list \
  --project=email-to-telegram-455900 \
  --regions=us-central1 \
  --format="table(name.basename(),buildConfig.runtime,state)"
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
gcloud scheduler jobs list \
  --location=us-central1 \
  --project=email-to-telegram-455900 \
  --format="table(name.basename(),state,schedule,timeZone)"
```

Expected:

```text
renew-gmail-watch-rescue-job    ENABLED  0 6 * * *  America/Phoenix
renew-gmail-watch-retrieve-job  ENABLED  0 6 * * *  America/Phoenix
```

## 3. Test forwarding

The most useful functional test is a real email.

### Rescue

Send an email to the designated Gmail account for the Rescue route.

Verify that it appears in the Rescue Telegram topic.

### Retrieve

Send an email to the designated Gmail account for the Retrieve route.

Verify that it appears in the Retrieve Telegram topic.

These tests exercise the complete forwarding path: Gmail, the watch, Pub/Sub, the Cloud Function, Gmail message retrieval, Secret Manager, Telegram authentication, and Telegram delivery.

## 4. Test watch renewal

A Scheduler job can be run immediately.

### Rescue

```bash
gcloud scheduler jobs run renew-gmail-watch-rescue-job \
  --location=us-central1 \
  --project=email-to-telegram-455900
```

### Retrieve

```bash
gcloud scheduler jobs run renew-gmail-watch-retrieve-job \
  --location=us-central1 \
  --project=email-to-telegram-455900
```

These commands exercise the production Scheduler → OIDC → renewal-function path.

A successful Scheduler invocation only establishes that Scheduler accepted the request. Check the renewal function logs to determine whether the Gmail `users.watch()` operation itself succeeded.

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
gcloud functions logs read email-to-telegram-rescue \
  --region=us-central1 \
  --project=email-to-telegram-455900
```

```bash
gcloud functions logs read email-to-telegram-retrieve \
  --region=us-central1 \
  --project=email-to-telegram-455900
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
gcloud functions logs read renew-gmail-watch-rescue \
  --region=us-central1 \
  --project=email-to-telegram-455900
```

```bash
gcloud functions logs read renew-gmail-watch-retrieve \
  --region=us-central1 \
  --project=email-to-telegram-455900
```

Use `--limit=N` when only recent entries are needed.

## 6. Troubleshooting a missing forwarded message

Work from the outside in.

### Step 1: Verify Gmail

Confirm that the email actually arrived in the expected Gmail inbox.

Check the Gmail Spam folder, and if the message is there, mark it as not spam.

### Step 2: Verify the Gmail watch

If a forwarding path stops receiving messages, suspect the watch or Pub/Sub path.

Run the corresponding renewal Scheduler job manually and inspect its logs.

### Step 3: Check the forwarding function logs

Look for:

* Secret Manager failures;
* Gmail API authentication errors;
* Gmail API message retrieval errors;
* Telegram HTTP errors;
* Python exceptions.

A function exception should normally cause the event delivery to be retried. If the message remains unread, the retry should provide another opportunity to process it.

### Step 4: Check Telegram

Verify that:

* the bot is still a member of the group;
* the bot still has permission to post;
* the configured chat ID is correct;
* the configured topic ID is correct;
* the bot token is valid.

### Step 5: Allow for retry

A failed forwarding invocation does not necessarily mean that the message has been lost.

The event-trigger retry mechanism should attempt delivery again. If the failure is transient, the message should eventually be forwarded without requiring another incoming Gmail message.

If repeated attempts fail, inspect the forwarding function logs to determine the underlying problem.

## 7. Duplicate Telegram messages

A duplicate Telegram message can occur even when retries are functioning correctly.

For example:

```text
Forwarding function
       │
       ▼
Telegram accepts message
       │
       ▼
Function does not successfully complete
       │
       ▼
Event is retried
       │
       ▼
Same Gmail message is still unread
       │
       ▼
Telegram receives it again
```

This can happen if the Telegram request succeeds but the function experiences a timeout or other failure before it can complete normally.

Duplicates are therefore not, by themselves, evidence that the retry mechanism is malfunctioning.

For this application, a duplicate is preferable to a lost message.

## 8. Troubleshooting a renewal failure

First verify the Scheduler job.

For Rescue:

```bash
gcloud scheduler jobs describe renew-gmail-watch-rescue-job \
  --location=us-central1 \
  --project=email-to-telegram-455900
```

For Retrieve:

```bash
gcloud scheduler jobs describe renew-gmail-watch-retrieve-job \
  --location=us-central1 \
  --project=email-to-telegram-455900
```

Confirm:

* job is enabled;
* URI points to the correct renewal function;
* OIDC service account is configured;
* OIDC audience matches the function URL.

Then inspect the renewal function logs.

A successful manual Scheduler invocation only establishes that Scheduler accepted the request. The function logs should be checked to determine whether the Gmail `users.watch()` operation itself succeeded.

## 9. Deploying code

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

These deployments enable retries on the forwarding functions.

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

## 10. Scheduler configuration

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

Scheduler retry settings are independent of the event-trigger retry settings used by the forwarding functions.

## 11. Python runtime upgrades

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

## 12. Recovery from a failed deployment

If a deployment fails:

1. Do not immediately modify unrelated configuration.
2. Inspect the deployment/build output.
3. Check the function state and runtime.
4. Review recent function logs.
5. Compare the working Git revision with the failed change.
6. If necessary, redeploy the last known-good revision from the local Git checkout.

Because Google Cloud resources and secrets are outside Git, restoring source code alone is not sufficient to recreate the complete production system.

## 13. Recreating the production system

The Git repository contains the application source and the configuration needed to deploy it, but it does not contain all of the state required for a functioning production installation.

A complete recreation requires both the repository and the external services/resources described below.

### 13.1 Information stored in Git

The repository contains:

* forwarding function source;
* renewal function source;
* Python dependency declarations;
* route environment files;
* Makefile deployment and operational commands;
* OAuth-token generation utility;
* documentation.

The route environment files contain secret *names* and other configuration, but not secret values.

### 13.2 External resources that must exist

A functioning installation also requires:

**Google Cloud**

* the Google Cloud project;
* required APIs enabled;
* Pub/Sub topics;
* Secret Manager secrets and their values;
* Secret Manager IAM permissions;
* forwarding Cloud Functions;
* renewal Cloud Functions;
* Cloud Scheduler jobs;
* the Scheduler service account and required IAM permissions;
* permission for Gmail to publish to each Gmail notification topic.

**Gmail**

* the Gmail accounts used by the forwarding routes;
* OAuth authorization for each account;
* the corresponding OAuth token material;
* an active Gmail watch for each route.

**Telegram**

* the Telegram bot;
* the bot token;
* the destination Telegram group;
* the destination topics;
* bot membership and permission to post.

### 13.3 Recreating Google Cloud resources

The Cloud Functions, Pub/Sub topics, Scheduler jobs, and Secret Manager metadata are infrastructure that can be recreated from the documented configuration.

The current production resource names are listed in the Operational Inventory in `Maintenance.md`.

The normal order for recreating a route is:

1. create or identify the Gmail account;
2. authorize Gmail and create its OAuth token;
3. create the corresponding Secret Manager secret and store the token;
4. grant the forwarding and renewal functions access to the secret;
5. create the Pub/Sub topic;
6. grant Gmail permission to publish to the topic;
7. create the route's `.env.<routeName>.yaml` file;
8. add the route to the Makefile;
9. create or configure the Telegram destination;
10. deploy the forwarding function;
11. deploy the renewal function;
12. create the Scheduler job;
13. run the Scheduler job manually to establish the Gmail watch;
14. perform a real end-to-end forwarding test.

The exact resource names are not intrinsically important to the application; what matters is that the environment file, Makefile, Gmail watch, Pub/Sub topic, functions, and Scheduler job all agree.

### 13.4 What cannot be recovered from Git alone

Git does not contain:

* Gmail passwords;
* Gmail OAuth token contents;
* Telegram bot token;
* Google Cloud Secret Manager secret values;
* Telegram group/topic state;
* Gmail account state.

Those items must therefore either be preserved separately or recreated through their respective services.

In particular, do not assume that restoring the repository and redeploying the functions will restore Gmail watches. A Gmail watch is external state and must be established by calling the renewal function.

### 13.5 Recovery principle

The repository should be sufficient to explain **how to rebuild the software and infrastructure**, while secrets and externally owned service state must be recovered or recreated separately.

This distinction is intentional: sensitive credentials and service-owned state are not stored in Git merely to make disaster recovery easier.
