# Contributing

## 1. Development model

Development follows an issue-driven GitHub workflow.

The main branch should contain reviewed, tested changes suitable for deployment.

Work should normally be associated with a GitHub issue before implementation begins.

## 2. Start with an issue

Create or identify the issue describing the desired change.

The issue should explain:

- what needs to change;
- why the change is needed;
- relevant constraints;
- how the result will be tested.

Keep the issue focused enough that a branch and pull request can correspond to a coherent change.

## 3. Work in a personal fork

Development is performed in a personal fork rather than directly on the main repository.

Create a branch whose name identifies the issue:

```text
issue/<issue number>-description
```

For example:

```text
issue/42-improve_scheduler_diagnostics
```

Keep the branch focused on the issue.

## 4. Implement and test

Make the smallest reasonable change.

For this project, testing should consider both the Python code and the Google Cloud deployment configuration.

Depending on the change, useful checks include:

- inspecting `git diff`;
- deploying the affected function;
- checking that the function becomes `ACTIVE`;
- checking the deployed runtime;
- sending a real test email;
- running a Scheduler renewal job;
- inspecting function logs;
- checking Scheduler configuration.

Do not expose secrets (OAuth and bot tokens) in source, logs, commits, issues, or pull requests.

## 5. Commit

Commit the completed change with a concise message describing what changed.

## 6. Pull request

Push the issue branch to the personal fork and create a pull request against the main repository.

The pull request should identify the issue and summarize:

- the implementation;
- important design decisions;
- tests performed;
- any remaining limitations or follow-up work.

## 7. Review and merge

After review and successful testing, merge the pull request into `main`.

Do not treat a successful merge as proof that the production deployment has been updated. Deployment is a separate operation.

## 8. Deployment after merge

From the local checkout of the main branch, deploy the affected production components using the Makefile.

For forwarding changes:

```bash
make deploy-<routeName>
```

or:

```bash
make deploy-all
```

For renewal changes:

```bash
make deploy-watch-<routeName>
```

or:

```bash
make deploy-watch-all
```

Perform the appropriate production verification after deployment.

## 9. Repository ownership and portability

Code, deployment scripts, and documentation should not depend on the repository's current owner or URL.

In particular:

- do not hard-code the GitHub repository URL in application code;
- do not use absolute local paths;
- prefer repository-relative documentation links;
- do not make Google Cloud deployment depend on GitHub checkout URLs.

A repository transfer should require only GitHub-side administration and updating local Git remotes.

## 10. What is not stored in Git

The public repository intentionally does not contain:

- Gmail OAuth token contents;
- Google OAuth credential files;
- Telegram bot credentials;
- other secret credential material.

A contributor who needs to modify authentication or deployment must have appropriate access
to the relevant Google Cloud resources without placing those credentials into the repository.

## 11. Keeping documentation current

When a change alters:

- architecture;
- Google Cloud resources;
- deployment commands;
- configuration variables;
- troubleshooting procedures;
- supported routes;
- development workflow;

update the relevant documentation in the same issue/branch.

The documentation should describe the current system, not the historical implementation that was replaced.
