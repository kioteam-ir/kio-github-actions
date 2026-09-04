# kio-github-actions

Reusable GitHub Actions workflows and composite actions for [`kioteam-ir`](https://github.com/kioteam-ir).

Pin callers to a tag (`@v1`), not `main`.

## Layout

| Path | Kind | Use when |
|---|---|---|
| `.github/workflows/*.yml` | reusable workflow (`workflow_call`) | The shared unit is a whole **job** (runner, secrets, several steps) |
| `actions/*/action.yml` | composite action | The shared unit is a **step** inside a job the caller owns |

A reusable workflow that lives in this repo must reference composite actions with the full path `kioteam-ir/kio-github-actions/actions/<name>@<tag>`. Relative `./` paths resolve against the **caller** repo, not this one.

## Setup (once per org)

1. Repo → Settings → Actions → General → Access: **Accessible from repositories in the `kioteam-ir` organization**.
2. Put `TELEGRAM_TO` (supergroup chat id) and `TELEGRAM_TOKEN` on the caller repo, or as org secrets. `telegram-notify` sends to forum topic `8643` unless `message_thread_id` is overridden.

This repo is public so public callers such as `kio-website` can use it. Do not put secrets in YAML.

This repo also calls `notify-events.yml@v1` from `.github/workflows/notify.yml` so its own pushes, issues, PRs, and releases notify Telegram. Set `TELEGRAM_TO` and `TELEGRAM_TOKEN` as repository secrets (same names as the product repos).

## Reusable workflow: notify events

Caller keeps the `on:` triggers. This repo owns the Telegram job.

```yaml
name: Notify Repo Events

on:
  push:
  issues:
    types: [opened, closed, reopened]
  issue_comment:
    types: [created]
  pull_request:
    types: [opened, closed, reopened]
  pull_request_review_comment:
    types: [created]
  release:
    types: [published]

jobs:
  notify:
    uses: kioteam-ir/kio-github-actions/.github/workflows/notify-events.yml@v1
    secrets:
      TELEGRAM_TO: ${{ secrets.TELEGRAM_TO }}
      TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
```

Optional input `runner` defaults to `ubuntu-latest`. Self-hosted callers pass `with: { runner: self-hosted }`.

## Reusable workflow: notify CI result

Caller keeps `on.workflow_run` (which workflows to watch). This repo owns success/failure Telegram jobs.

```yaml
name: Notify CI Result

on:
  workflow_run:
    workflows: [CI, Deploy]
    types: [completed]

jobs:
  notify:
    uses: kioteam-ir/kio-github-actions/.github/workflows/notify-ci.yml@v1
    secrets:
      TELEGRAM_TO: ${{ secrets.TELEGRAM_TO }}
      TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
```

## Composite action: telegram-notify

```yaml
jobs:
  example:
    runs-on: ubuntu-latest
    steps:
      - uses: kioteam-ir/kio-github-actions/actions/telegram-notify@v1
        with:
          token: ${{ secrets.TELEGRAM_TOKEN }}
          to: ${{ secrets.TELEGRAM_TO }}
          message: hello from ${{ github.repository }}
```

## Reusable CI workflows

Use GitHub-hosted runners through reusable workflows:

### Python Poetry

```yaml
name: CI

on:
  push:
  pull_request:

jobs:
  python:
    uses: kioteam-ir/kio-github-actions/.github/workflows/python-poetry-ci.yml@v1
```

### Full-stack

```yaml
jobs:
  fullstack:
    uses: kioteam-ir/kio-github-actions/.github/workflows/fullstack-ci.yml@v1
```

The full-stack workflow expects `backend/requirements.txt` and
`frontend/package-lock.json`. Override the workflow inputs when a project
uses different directories or commands.

## Release

1. Merge to `main`.
2. Tag a release (`v1.0.1`) and move the floating major tag (`v1`) to the same commit.
3. Callers stay on `@v1` until a breaking change needs `@v2`.
