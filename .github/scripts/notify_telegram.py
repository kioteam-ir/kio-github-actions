"""Build HTML-formatted Telegram notifications for GitHub repository events."""

import html
import json
import os
from pathlib import Path
from typing import Any

CAP_MESSAGE = 500
CAP_TITLE = 300
CAP_SHORT = 100
CAP_URL = 500
OUTPUT_FILE = "tg-message.html"

Event = dict[str, Any]
Environment = dict[str, str]


def one_line(value: Any, cap: int) -> str:
    """Normalize whitespace and truncate a value to a maximum length."""
    if value is None:
        return ""

    text = " ".join(str(value).split())
    if len(text) > cap:
        return text[: cap - 1] + "…"

    return text


def escape_html(value: Any, cap: int = CAP_SHORT) -> str:
    """Normalize, truncate, and HTML-escape untrusted text."""
    return html.escape(one_line(value, cap), quote=False)


def code(value: Any, cap: int = CAP_SHORT) -> str:
    """Render escaped text inside a Telegram HTML code element."""
    return f"<code>{escape_html(value, cap)}</code>"


def repository_details(env: Environment) -> list[str]:
    """Return common repository and actor fields."""
    return [
        f"👤 By: {code(env.get('ACTOR', ''))}",
        f"📦 Repo: {code(env.get('REPOSITORY', ''))}",
    ]


def format_push(event: Event, env: Environment) -> str | None:
    """Format a push event, ignoring branch deletion events."""
    if event.get("deleted"):
        return None

    commit = event.get("head_commit") or {}
    lines = [
        f"🆕 <b>Push to</b> {code(env.get('REPOSITORY', ''))}",
        f"👤 By: {code(env.get('ACTOR', ''))}",
        f"🌿 Ref: {code(env.get('REF_NAME', ''))}",
    ]

    message = one_line(commit.get("message"), CAP_MESSAGE)
    if message:
        lines.append(f"💬 Message: {code(message, CAP_MESSAGE)}")

    if commit.get("url"):
        lines.append(f"🔗 {escape_html(commit['url'], CAP_URL)}")

    return "\n".join(lines)


def format_issue(event: Event, env: Environment) -> str:
    """Format an issue lifecycle event."""
    issue = event.get("issue") or {}
    action = str(event.get("action", ""))
    icon = {"opened": "🆕", "closed": "✅"}.get(action, "🔄")

    return "\n".join(
        [
            (
                f"<b>{icon} Issue #{issue.get('number', '?')} "
                f"{escape_html(action)}</b>"
            ),
            f"📌 Title: {code(issue.get('title'), CAP_TITLE)}",
            *repository_details(env),
            f"🔗 {escape_html(issue.get('html_url', ''), CAP_URL)}",
        ]
    )


def format_issue_comment(event: Event, env: Environment) -> str:
    """Format a comment created or edited on an issue."""
    issue = event.get("issue") or {}
    comment = event.get("comment") or {}

    return "\n".join(
        [
            f"💬 <b>Comment on Issue #{issue.get('number', '?')}</b>",
            *repository_details(env),
            f"🔗 {escape_html(comment.get('html_url', ''), CAP_URL)}",
        ]
    )


def format_pull_request(event: Event, env: Environment) -> str:
    """Format a pull request lifecycle event."""
    pull_request = event.get("pull_request") or {}
    action = str(event.get("action", ""))

    if action == "closed":
        label = (
            "🔀 PR merged"
            if pull_request.get("merged")
            else "❌ PR closed"
        )
    elif action == "opened":
        label = "🆕 PR"
    else:
        label = "🔄 PR"

    return "\n".join(
        [
            (
                f"<b>{label} #{pull_request.get('number', '?')} "
                f"{escape_html(action)}</b>"
            ),
            f"📌 Title: {code(pull_request.get('title'), CAP_TITLE)}",
            *repository_details(env),
            f"🔗 {escape_html(pull_request.get('html_url', ''), CAP_URL)}",
        ]
    )


def format_review_comment(event: Event, env: Environment) -> str:
    """Format a review comment created or edited on a pull request."""
    pull_request = event.get("pull_request") or {}
    comment = event.get("comment") or {}

    return "\n".join(
        [
            (
                "<b>💬 Review comment on PR "
                f"#{pull_request.get('number', '?')}</b>"
            ),
            *repository_details(env),
            f"🔗 {escape_html(comment.get('html_url', ''), CAP_URL)}",
        ]
    )


def format_release(event: Event, env: Environment) -> str:
    """Format a release creation or publication event."""
    release = event.get("release") or {}
    action = str(event.get("action", ""))
    status = "created" if action == "created" else "published"

    return "\n".join(
        [
            (
                f"🚀 <b>Release</b> {code(release.get('tag_name'))} "
                f"<b>{status}</b>"
            ),
            *repository_details(env),
            f"🔗 {escape_html(release.get('html_url', ''), CAP_URL)}",
        ]
    )


def format_dispatch(event: Event, env: Environment) -> str:
    """Format a manually triggered notification test."""
    return "\n".join(
        [
            "🧪 <b>Telegram notification test</b>",
            *repository_details(env),
            f"🌿 Ref: {code(env.get('REF_NAME', ''))}",
        ]
    )


BUILDERS = {
    "push": format_push,
    "issues": format_issue,
    "issue_comment": format_issue_comment,
    "pull_request": format_pull_request,
    "pull_request_review_comment": format_review_comment,
    "release": format_release,
    "workflow_dispatch": format_dispatch,
}


def main() -> None:
    """Build the notification and expose the send decision to GitHub Actions."""
    env: Environment = dict(os.environ)
    event_name = env["EVENT_NAME"]
    event_path = Path(env["EVENT_PATH"])
    workspace = Path(env["WORKSPACE"])

    with event_path.open(encoding="utf-8") as file:
        event: Event = json.load(file)

    builder = BUILDERS.get(event_name)
    message = builder(event, env) if builder else None

    output_path = Path(os.environ["GITHUB_OUTPUT"])
    with output_path.open("a", encoding="utf-8") as output:
        output.write(f"send={'true' if message else 'false'}\n")

    if not message:
        print(f"No notification generated for event: {event_name}")
        return

    message_path = workspace / OUTPUT_FILE
    message_path.write_text(message, encoding="utf-8")
    print(f"Notification generated for event: {event_name}")


if __name__ == "__main__":
    main()
