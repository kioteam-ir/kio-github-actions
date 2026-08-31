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
2. Put `TELEGRAM_TO` and `TELEGRAM_TOKEN` on the caller repo, or as org secrets.

This repo is public so public callers such as `kio-website` can use it. Do not put secrets in YAML.

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

## Release

1. Merge to `main`.
2. Tag a release (`v1.0.1`) and move the floating major tag (`v1`) to the same commit.
3. Callers stay on `@v1` until a breaking change needs `@v2`.
