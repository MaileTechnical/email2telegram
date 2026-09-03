# Maintenance

## 1. General principles

Keep route-specific configuration out of Python code.

When modifying the system, preserve the separation between:

- Gmail account and OAuth token;
- Pub/Sub notification topic;
- forwarding Cloud Function;
- Telegram destination topic;
- watch-renewal function;
- Scheduler job.

Changes should be made to the smallest set of components necessary.

## 2. Source files

### `main.py`

Implements the common email-to-Telegram forwarding behavior.

It should generally not contain route-specific constants.

### `.env.<routeName>.yaml`

Define route-specific deployment configuration.

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

Add a new forwarding path using the pattern of the existing routes.

### Step 1: Define the route

Choose:

- Gmail account, creating a new one if necessary.
- Pub/Sub topic;
- Telegram topic;
- Secret Manager secret containing the Gmail OAuth token;
- forwarding function name;
- renewal function name;
- Scheduler job name.

Use the existing naming conventions.

### Step 2: Create the Gmail OAuth token

If the Gmail account has not yet been used, send a few emails to and from it to
establish some normal usage, as this step involves requesting API authorization to
the Gmail account.  Sometimes, Google views such a request on a newly created account
as suspicious and denies the request.
Ensure all emails sent to the new account are received in the inbox.
Mark any that fall into the spam folder as not spam.

Run the OAuth-token utility.
This utility presents a Google login dialog, so you will need to provide the Gmail
address and password for the Gmail account.
It will then supply a token that must be kept secure.
Do not email it, paste it into a chat or otherwise let it escape your machine.
Store this token in the Google Secret Manager using the secret name (which must 
be unique to the route) in the environment file for the new route.

### Step 3: Create the Pub/Sub topic

Create a topic dedicated to the new Gmail account.

Grant Gmail the required permission to publish to the topic.

AI TODO: add command(s)

### Step 4: Add route configuration

Create a new environment file following the existing pattern, for example:

```text
.env.newroute.yaml
```
Copy the contents of one of the existing environment files into the new file.
Update each value in the file for the new route.

### Step 5: Extend the Makefile

Add the new route to all case statements.

Add explicit convenience targets analogous to:

```text
deploy-newroute
deploy-watch-newroute
schedule-watch-newroute
delete-schedule-watch-newroute
```

Also extend the aggregate targets if appropriate.

### Step 6: Deploy the forwarding function

AI TODO: add command(s)
Deploy the new route and verify that the function is `ACTIVE`.

### Step 7: Deploy the renewal function

AI TODO: add command(s)
Deploy its renewal function and verify that it is `ACTIVE`.

### Step 8: Create the Scheduler job

AI TODO: add command(s)
Run the corresponding `schedule-watch-*` target.

Verify the job's URI, OIDC configuration, schedule, and enabled state.

### Step 9: Test the watch renewal

AI TODO: add command(s)
Run the Scheduler job manually and inspect the renewal function logs.

### Step 10: Test forwarding

Send a real test message to the new Gmail account and verify delivery to the new Telegram topic
while confirming it does not arrive in any other topic.

### Step 11: Update Inventory

Add the identifiers for the new route to the Operational Inventory in this document.

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
2. update `GMAIL_PUBSUB_TOPIC`;
3. deploy the forwarding function;
4. deploy the renewal function if necessary;
5. explicitly renew the Gmail watch;
6. verify the new topic receives notifications;
7. test forwarding.

## 7. Secret maintenance

Secrets are maintained in Google Cloud Secret Manager.

Never:

- commit secret values;
- put OAuth tokens in `.env.*.yaml`;
- put Telegram bot tokens in source;
- paste secret values into issue reports or documentation.

If a secret is rotated, update Secret Manager and then test the affected route.

## 8. Repository portability

The application must not depend on the GitHub repository's owner or URL.

The runtime deployment uses the local source tree and explicit Google Cloud resource names. It does not fetch source from GitHub.

Prefer:

- repository-relative paths;
- relative documentation links;
- configuration variables for deployment-specific values.

Avoid:

- hard-coded GitHub repository URLs in code;
- absolute developer filesystem paths;
- references to a particular GitHub owner in scripts;
- GitHub-specific URLs where a relative repository path is sufficient.

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
