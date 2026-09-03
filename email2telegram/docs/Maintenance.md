# Maintenance

## 1. General principles

Keep route-specific configuration out of Python code.

When modifying the system, preserve the separation between:

* Gmail account and OAuth token;
* Pub/Sub notification topic;
* forwarding Cloud Function;
* Telegram destination topic;
* watch-renewal function;
* Scheduler job.

Changes should be made to the smallest set of components necessary.

## 2. Source files

### `main.py`

Implements the common email-to-Telegram forwarding behavior.

It should generally not contain route-specific constants.

### `.env.<routeName>.yaml`

Defines route-specific deployment configuration.

Do not put credentials or OAuth token contents in these files.

### `renew_watch/renew_watch.py`

Implements Gmail watch renewal.

### `renew_watch/main.py`

Provides the renewal function's deployment entry point support.

### `Makefile`

Defines the deployment and operational commands and contains the mapping between logical routes and Google Cloud resources.

Because it controls production deployment, changes to the Makefile should be tested explicitly.

### `utils/genOauthToken.py`

Supports generation of Gmail OAuth token material.

Credential files used by this process are not committed.

## 3. Adding a new forwarding path

A forwarding path consists of:

* one Gmail account;
* one Gmail OAuth token stored in Secret Manager;
* one Pub/Sub topic receiving Gmail notifications;
* one forwarding Cloud Function;
* one Telegram group/topic destination;
* one watch-renewal Cloud Function;
* one Cloud Scheduler job.

Add the new path using the pattern of the existing routes.

### Step 1: Define the route

Choose:

* Gmail account, creating a new one if necessary;
* Pub/Sub topic;
* Telegram group and topic;
* Secret Manager secret containing the Gmail OAuth token;
* forwarding function name;
* renewal function name;
* Scheduler job name.

Use the existing naming conventions.

For example, for a hypothetical route named `newroute`:

```text
Gmail account:             designated Gmail account
Pub/Sub topic:             gmail-notifications-newroute
Telegram topic:            <new Telegram topic ID>
OAuth secret:              gmail_token_newroute
Forwarding function:       email-to-telegram-newroute
Renewal function:          renew-gmail-watch-newroute
Scheduler job:             renew-gmail-watch-newroute-job
Environment file:          .env.newroute.yaml
```

The actual Gmail address does not need to appear in the repository documentation.

### Step 2: Create the Gmail OAuth token

If the Gmail account has not yet been used, send a few emails to and from it to establish some normal usage. This step involves requesting API authorization to the Gmail account, and Google may sometimes treat authorization from a newly created account as suspicious.

Ensure all emails sent to the new account are received in the inbox. Mark any that fall into the Spam folder as not spam.

From the repository root, run the OAuth-token utility:

```bash
python3 utils/genOauthToken.py
```

Follow the utility's prompts to authorize the Gmail account.

The utility produces OAuth token material that must be kept secure. Do not email it, paste it into a chat, commit it to Git, or otherwise allow it to escape the machine on which it was generated.

Create a Secret Manager secret for the route:

```bash
gcloud secrets create gmail_token_newroute \
  --replication-policy=automatic \
  --project=email-to-telegram-455900
```

Add the OAuth token as the first secret version. If the utility produced the token in a file, use:

```bash
gcloud secrets versions add gmail_token_newroute \
  --data-file=<token-file> \
  --project=email-to-telegram-455900
```

If the token is instead available through standard input, the equivalent form is:

```bash
cat <token-file> | gcloud secrets versions add gmail_token_newroute \
  --data-file=- \
  --project=email-to-telegram-455900
```

Do not put the token itself in the environment file.

The Cloud Functions must also have permission to access the secret. Follow the same Secret Manager IAM configuration used by the existing routes. The required role is `roles/secretmanager.secretAccessor`.

### Step 3: Create the Pub/Sub topic

Create a topic dedicated to the new Gmail account:

```bash
gcloud pubsub topics create gmail-notifications-newroute \
  --project=email-to-telegram-455900
```

Grant the Gmail API service account permission to publish to the topic.

For the Gmail push-notification service account, grant the Pub/Sub Publisher role on the topic:

```bash
gcloud pubsub topics add-iam-policy-binding gmail-notifications-newroute \
  --member="serviceAccount:gmail-api-push@system.gserviceaccount.com" \
  --role="roles/pubsub.publisher" \
  --project=email-to-telegram-455900
```

This permission is required before the Gmail `users.watch()` call can successfully use the topic.

### Step 4: Add route configuration

Create a new environment file following the existing pattern:

```text
.env.newroute.yaml
```

Copy the contents of an existing environment file:

```bash
cp .env.rescue.yaml .env.newroute.yaml
```

Edit the new file and change every route-specific value.

The file should contain values corresponding to:

```text
TELEGRAM_CHAT_ID
TELEGRAM_TOPIC_ID
GCP_PROJECT
GMAIL_TOKEN_SECRET
TELEGRAM_BOT_TOKEN_SECRET
GMAIL_PUBSUB_TOPIC
```

The file contains secret *names*, not secret values.

### Step 5: Extend the Makefile

The current Makefile uses `SOLUTION` case statements to map the logical route to its Google Cloud resources.

Add the new route to all applicable case statements in:

```text
deploy
deploy-watch
schedule-watch
delete-schedule-watch
logs
logs-watch
```

For example, the forwarding deployment case must contain an entry analogous to:

```make
newroute) \
    FUNCTION_NAME=email-to-telegram-newroute; \
    ENV_FILE=.env.newroute.yaml; \
    TRIGGER_TOPIC=gmail-notifications-newroute; \
    ;;
```

The renewal deployment case must map `newroute` to:

```text
renew-gmail-watch-newroute
.env.newroute.yaml
```

The Scheduler case must map it to:

```text
renew-gmail-watch-newroute-job
renew-gmail-watch-newroute
```

The logging cases must map it to the appropriate forwarding and renewal functions.

Add explicit convenience targets analogous to the existing routes:

```make
deploy-newroute:
  $(MAKE) deploy SOLUTION=newroute

deploy-watch-newroute:
  $(MAKE) deploy-watch SOLUTION=newroute

schedule-watch-newroute:
  $(MAKE) schedule-watch SOLUTION=newroute

delete-schedule-watch-newroute:
  $(MAKE) delete-schedule-watch SOLUTION=newroute
```

Also extend the aggregate targets if appropriate.

After editing the Makefile, inspect the change carefully:

```bash
git diff
```

The Makefile is part of the production deployment mechanism, so test the new route explicitly before relying on an aggregate target.

### Step 6: Deploy the forwarding function

From the repository root:

```bash
make deploy-newroute
```

This is equivalent to:

```bash
make deploy SOLUTION=newroute
```

Verify that the new function is active:

```bash
gcloud functions list \
  --project=email-to-telegram-455900 \
  --regions=us-central1 \
  --format="table(name.basename(),buildConfig.runtime,state)"
```

### Step 7: Deploy the renewal function

Deploy the renewal function:

```bash
make deploy-watch-newroute
```

This is equivalent to:

```bash
make deploy-watch SOLUTION=newroute
```

Verify that the renewal function is `ACTIVE`.

### Step 8: Create the Scheduler job

Create or update the Scheduler job:

```bash
make schedule-watch-newroute
```

This is equivalent to:

```bash
make schedule-watch SOLUTION=newroute
```

The Makefile configures the job with:

* the renewal function URL;
* HTTP GET;
* the configured OIDC service account;
* the function URL as the OIDC audience;
* the daily schedule;
* the configured time zone;
* the configured retry and backoff settings.

Verify the resulting job:

```bash
gcloud scheduler jobs describe renew-gmail-watch-newroute-job \
  --location=us-central1 \
  --project=email-to-telegram-455900
```

Confirm that the job is enabled and that its URI, OIDC configuration, schedule, and time zone are correct.

### Step 9: Establish and test the Gmail watch

Run the Scheduler job manually:

```bash
gcloud scheduler jobs run renew-gmail-watch-newroute-job \
  --location=us-central1 \
  --project=email-to-telegram-455900
```

Then inspect the renewal function logs:

```bash
make logs-watch SOLUTION=newroute
```

The logs should show successful startup and execution without an exception.

A successful Scheduler invocation alone does not prove that Gmail accepted the watch. The renewal function must complete its Gmail `users.watch()` call successfully.

### Step 10: Test forwarding

Send a real test message to the new Gmail account.

Verify:

1. the message arrives in the Gmail inbox;
2. the Gmail notification reaches the new Pub/Sub topic;
3. the forwarding function processes the message;
4. the message appears in the intended Telegram topic;
5. the message does not appear in another Telegram topic;
6. the Gmail message is marked read after successful forwarding.

This is an end-to-end test of the new route.

### Step 11: Update the operational inventory

Add the new route's production resource names to the Operational Inventory in this document.

Do not add the Gmail address or any secret values.

## 4. Changing a Telegram destination

To change a route's destination topic:

1. If it is not already a member of the destination Telegram group, add the bot to that group.
2. Update the route's `TELEGRAM_CHAT_ID` and `TELEGRAM_TOPIC_ID`.
3. Review the change carefully.
4. Deploy that forwarding function.
5. Send a real test email.
6. Verify the new destination.

No Gmail or Scheduler change is required for a Telegram-only destination change.

## 5. Changing a Gmail account

Changing the Gmail account is more involved because the OAuth token and Gmail watch belong to the account.

Plan to:

1. generate/store the new Gmail OAuth token;
2. update `GMAIL_TOKEN_SECRET`;
3. establish the new Gmail watch;
4. verify the Pub/Sub topic;
5. deploy the forwarding function;
6. renew the new watch;
7. perform a real end-to-end test.

Do not assume that changing an environment variable automatically changes an existing Gmail watch.

## 6. Changing a Pub/Sub topic

A Pub/Sub topic is part of the Gmail watch configuration.

If the topic changes:

1. create/configure the new topic;
2. grant Gmail permission to publish to the new topic;
3. update `GMAIL_PUBSUB_TOPIC`;
4. deploy the forwarding function;
5. deploy the renewal function if necessary;
6. explicitly renew the Gmail watch;
7. verify the new topic receives notifications;
8. test forwarding.

The old topic can be removed only after confirming that the new watch and forwarding path are working.

## 7. Secret maintenance

Secrets are maintained in Google Cloud Secret Manager.

Never:

* commit secret values;
* put OAuth tokens in `.env.*.yaml`;
* put Telegram bot tokens in source;
* paste secret values into issue reports or documentation.

If a secret is rotated, update Secret Manager and then test the affected route.

Secret Manager supports multiple secret versions, so rotating a secret does not require putting the new value into source-controlled configuration.

## 8. Repository portability

The application must not depend on the GitHub repository's owner or URL.

The runtime deployment uses the local source tree and explicit Google Cloud resource names. It does not fetch source from GitHub.

Prefer:

* repository-relative paths;
* relative documentation links;
* configuration variables for deployment-specific values.

Avoid:

* hard-coded GitHub repository URLs in code;
* absolute developer filesystem paths;
* references to a particular GitHub owner in scripts;
* GitHub-specific URLs where a relative repository path is sufficient.

## 9. Runtime upgrades

When Google Cloud announces retirement of the current Python runtime:

1. Check the supported runtime options.
2. Select a mature supported runtime with an adequate support lifetime.
3. Change the runtime declarations in the Makefile.
4. Inspect the diff.
5. Commit and push.
6. Deploy all functions.
7. Verify all report the new runtime.
8. Exercise all forwarding routes.
9. Exercise all renewal Scheduler jobs.
10. Verify Scheduler configuration remains unchanged.

Keep runtime upgrades isolated from unrelated application changes.

## 10. Operational inventory

The authoritative production names currently used by the Makefile are:

```text
Project:
    email-to-telegram-455900

Region:
    us-central1

Forwarding:
    email-to-telegram-rescue
    email-to-telegram-retrieve

Renewal:
    renew-gmail-watch-rescue
    renew-gmail-watch-retrieve

Pub/Sub:
    gmail-notifications-rescue
    gmail-notifications-retrieve

Scheduler:
    renew-gmail-watch-rescue-job
    renew-gmail-watch-retrieve-job

Secrets:
    gmail_token_azffrescue
    gmail_token_azffretrieve
    telegram_bot_token

Scheduler service account:
    506739284793-compute@developer.gserviceaccount.com
```

Treat these names as deployment-specific configuration, not as identifiers that should be copied into application logic unnecessarily.
