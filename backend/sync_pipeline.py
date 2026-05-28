"""Notion, GitHub, and Slack sync pipeline.

Current behavior:
- Create Notion DB reads backend/meeting_summary.json.
- The new database ID replaces DATABASE_ID in .env.
- GitHub tracking and Slack reports use the active DATABASE_ID.
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
ENV_PATH = ROOT_DIR / ".env"
SUMMARY_PATH = BASE_DIR / "meeting_summary.json"
USER_MAPPING_PATH = BASE_DIR / "user_mapping.json"
STATE_PATH = BASE_DIR / ".sync_state.json"

load_dotenv(ENV_PATH, override=True)

NOTION_VERSION = "2022-06-28"
TASK_STATUS_TODO = "To Do"
TASK_STATUS_DONE = "Done"
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "for",
    "in",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "using",
    "task",
    "done",
    "update",
    "fix",
    "add",
    "create",
    "created",
    "complete",
    "completed",
}


def env(name: str, default: str | None = None) -> str | None:
    """Read an environment variable and normalize quotes/spaces."""
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value.strip().strip('"').strip("'")


def required_env(name: str) -> str:
    """Read a required environment variable."""
    value = env(name)
    if not value:
        raise RuntimeError(f"Missing {name} in {ENV_PATH}")
    return value


def notion_headers() -> dict[str, str]:
    """Headers for Notion API."""
    return {
        "Authorization": f"Bearer {required_env('NOTION_TOKEN')}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }


def raise_api_error(response: requests.Response, service: str, action: str) -> None:
    if response.ok:
        return
    try:
        detail = response.json().get("message", response.text)
    except ValueError:
        detail = response.text
    raise RuntimeError(f"{service} {action} failed ({response.status_code}): {detail}")


def github_headers() -> dict[str, str]:
    """Headers for GitHub API."""
    token = env("TOKEN_GITHUB")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def load_json(path: Path, default: Any) -> Any:
    """Load JSON, returning default when missing."""
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    """Save JSON to disk."""
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def write_database_id(database_id: str) -> None:
    """Replace DATABASE_ID in .env with the latest Notion database ID."""
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines() if ENV_PATH.exists() else []
    found = False
    next_lines = []

    for line in lines:
        if line.strip().startswith("DATABASE_ID="):
            next_lines.append(f"DATABASE_ID={database_id}")
            found = True
        else:
            next_lines.append(line)

    if not found:
        next_lines.append(f"DATABASE_ID={database_id}")

    ENV_PATH.write_text("\n".join(next_lines) + "\n", encoding="utf-8")
    os.environ["DATABASE_ID"] = database_id
    print(f"DATABASE_ID updated in .env: {database_id}", flush=True)


def load_user_mapping() -> dict[str, dict[str, str]]:
    """Load GitHub/Notion/Slack member mapping from env or local file."""
    mapping_json = env("USER_MAPPING_JSON")
    if mapping_json:
        try:
            return json.loads(mapping_json)
        except json.JSONDecodeError as exc:
            raise RuntimeError("USER_MAPPING_JSON is not valid JSON") from exc
    return load_json(USER_MAPPING_PATH, {})


def normalize_name(name: str | None) -> str:
    """Normalize Gemini assignee text to a known Notion assignee name."""
    if not name:
        return "Unassigned"

    needle = name.strip().lower()
    known_names: dict[str, str] = {}
    for user in load_user_mapping().values():
        notion_name = user.get("notion_name")
        slack_name = user.get("slack_display_name")
        github_name = user.get("github_username")
        if notion_name:
            known_names[notion_name.lower()] = notion_name
        if slack_name and notion_name:
            known_names[slack_name.lower()] = notion_name
        if github_name and notion_name:
            known_names[github_name.lower()] = notion_name

    return known_names.get(needle, name.strip())


def user_for_github(username: str | None) -> dict[str, str] | None:
    """Find mapped user by GitHub username."""
    if not username:
        return None
    for user in load_user_mapping().values():
        if user.get("github_username", "").lower() == username.lower():
            return user
    return None


def user_for_notion(name: str | None) -> dict[str, str] | None:
    """Find mapped user by Notion assignee name."""
    if not name:
        return None
    for user in load_user_mapping().values():
        if user.get("notion_name", "").lower() == name.lower():
            return user
    return None


def extract_tasks_from_summary(summary_path: Path = SUMMARY_PATH) -> list[dict[str, Any]]:
    """Read meeting_summary.json action items as Notion tasks."""
    data = load_json(summary_path, {})
    structured = data.get("structured_data_json", data)
    action_items = structured.get("action_items", []) if isinstance(structured, dict) else []

    tasks = []
    for item in action_items:
        task_name = str(item.get("task", "")).strip()
        if not task_name:
            continue
        tasks.append(
            {
                "task": task_name,
                "assignee": normalize_name(item.get("assignee")),
                "status": TASK_STATUS_TODO,
            }
        )

    return tasks


def build_task_input(summary_path: Path = SUMMARY_PATH) -> dict[str, Any]:
    """Preview task payload extracted from the summary."""
    return {
        "tasks": extract_tasks_from_summary(summary_path),
    }


def create_notion_database(title: str | None = None) -> str:
    """Create a fresh task database under PARENT_PAGE_ID and write DATABASE_ID."""
    database_title = title or f"Meeting Tasks {datetime.now().strftime('%Y-%m-%d %H-%M-%S')}"
    payload = {
        "parent": {"type": "page_id", "page_id": required_env("PARENT_PAGE_ID")},
        "title": [{"type": "text", "text": {"content": database_title}}],
        "properties": {
            "Task": {"title": {}},
            "Assignee": {"rich_text": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": TASK_STATUS_TODO, "color": "red"},
                        {"name": TASK_STATUS_DONE, "color": "green"},
                    ]
                }
            },
        },
    }
    response = requests.post("https://api.notion.com/v1/databases", headers=notion_headers(), json=payload, timeout=30)
    raise_api_error(response, "Notion", "database creation")
    database_id = response.json()["id"]
    write_database_id(database_id)
    reset_state()
    return database_id


def database_id() -> str:
    """Read the active Notion database ID from .env."""
    load_dotenv(ENV_PATH, override=True)
    return required_env("DATABASE_ID")


def property_text(properties: dict[str, Any], name: str) -> str:
    """Read a Notion title/rich_text property as plain text."""
    prop = properties.get(name, {})
    values = prop.get("title") or prop.get("rich_text") or []
    if not values:
        return ""
    return values[0].get("plain_text") or values[0].get("text", {}).get("content", "")


def property_status(properties: dict[str, Any]) -> str:
    """Read Notion Status select."""
    status = properties.get("Status", {}).get("select")
    return status.get("name", "") if status else ""


def query_notion_tasks() -> list[dict[str, Any]]:
    """Fetch tasks from the active DATABASE_ID."""
    db_id = database_id()
    response = requests.post(
        f"https://api.notion.com/v1/databases/{db_id}/query",
        headers=notion_headers(),
        timeout=30,
    )
    raise_api_error(response, "Notion", "database query")
    return response.json().get("results", [])


def add_task_to_notion(database_id: str, task: dict[str, Any]) -> str:
    """Create one row/page in the active Notion database."""
    properties: dict[str, Any] = {
        "Task": {"title": [{"type": "text", "text": {"content": task["task"]}}]},
        "Assignee": {"rich_text": [{"type": "text", "text": {"content": task.get("assignee", "Unassigned")}}]},
        "Status": {"select": {"name": task.get("status") or TASK_STATUS_TODO}},
    }
    response = requests.post(
        "https://api.notion.com/v1/pages",
        headers=notion_headers(),
        json={"parent": {"database_id": database_id}, "properties": properties},
        timeout=30,
    )
    raise_api_error(response, "Notion", "task creation")
    return response.json()["id"]


def import_meeting_tasks(
    summary_path: Path = SUMMARY_PATH,
    *,
    fresh_database: bool = True,
    database_title: str | None = None,
) -> dict[str, Any]:
    """Create a fresh Notion database and insert tasks from meeting_summary.json."""
    tasks = build_task_input(summary_path).get("tasks", [])
    target_database_id = create_notion_database(database_title) if fresh_database else database_id()

    for task in tasks:
        add_task_to_notion(target_database_id, task)

    return {"created": len(tasks), "total": len(tasks), "database_id": target_database_id}


def fetch_recent_commits(limit: int = 30) -> list[dict[str, Any]]:
    """Fetch recent commits from configured GitHub repo."""
    response = requests.get(
        f"https://api.github.com/repos/{required_env('REPO_OWNER')}/{required_env('REPO_NAME')}/commits",
        headers=github_headers(),
        params={"per_page": limit},
        timeout=30,
    )
    raise_api_error(response, "GitHub", "commit fetch")
    return response.json()


def load_state() -> dict[str, Any]:
    """Load last processed commit state."""
    return load_json(STATE_PATH, {})


def save_state(state: dict[str, Any]) -> None:
    """Save last processed commit state."""
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_json(STATE_PATH, state)


def reset_state() -> None:
    """Reset commit tracking for each fresh meeting database."""
    if STATE_PATH.exists():
        STATE_PATH.unlink()


def print_commit_log(label: str, commits: list[dict[str, Any]]) -> None:
    """Print fetched/tracked commits in terminal."""
    print(f"\n========== {label} ({len(commits)}) ==========", flush=True)
    if not commits:
        print("No commits found.", flush=True)
    for commit in commits:
        sha = commit.get("sha", "")[:8]
        author = (commit.get("author") or {}).get("login") or "unknown"
        date = commit.get("commit", {}).get("author", {}).get("date", "unknown-date")
        message = commit.get("commit", {}).get("message", "").splitlines()[0]
        print(f"{sha} | {author} | {date} | {message}", flush=True)
    print("========================================\n", flush=True)


def new_commits(commits: list[dict[str, Any]], state: dict[str, Any]) -> list[dict[str, Any]]:
    """Return commits newer than last_seen_sha."""
    last_seen = state.get("last_seen_sha")
    if not commits:
        return []
    if not last_seen:
        return commits[:1]

    unseen = []
    for commit in commits:
        if commit.get("sha") == last_seen:
            break
        unseen.append(commit)
    return list(reversed(unseen))


def mark_task_done(page_id: str) -> None:
    """Set one Notion database row/page to Done."""
    response = requests.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers=notion_headers(),
        json={"properties": {"Status": {"select": {"name": TASK_STATUS_DONE}}}},
        timeout=30,
    )
    raise_api_error(response, "Notion", "task status update")


def keywords(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {word for word in words if len(word) > 2 and word not in STOP_WORDS}


def task_match_score(commit_message: str, task_name: str) -> int:
    commit_words = keywords(commit_message)
    task_words = keywords(task_name)
    if not commit_words or not task_words:
        return 0
    return len(commit_words & task_words)


def best_task_match(commit_message: str, pages: list[dict[str, Any]], assignee: str) -> dict[str, Any] | None:
    best_page = None
    best_score = 0

    for page in pages:
        props = page.get("properties", {})
        task_name = property_text(props, "Task")
        task_assignee = property_text(props, "Assignee")
        status = property_status(props)
        if not task_name or task_assignee.lower() != assignee.lower() or status == TASK_STATUS_DONE:
            continue

        score = task_match_score(commit_message, task_name)
        if score > best_score:
            best_score = score
            best_page = page

    return best_page if best_score >= 1 else None


def update_tasks_from_commits(commits: list[dict[str, Any]]) -> list[dict[str, str]]:
    """For each tracked commit, mark the matching assigned task Done."""
    updated = []
    tasks = query_notion_tasks()
    print(f"Loaded {len(tasks)} Notion tasks from DATABASE_ID={database_id()}", flush=True)

    for commit in commits:
        author = commit.get("author") or {}
        user = user_for_github(author.get("login"))
        assignee = user.get("notion_name") if user else None
        message = commit.get("commit", {}).get("message", "")

        if not assignee:
            print(f"Skipping commit by unmapped GitHub user: {author.get('login') or 'unknown'}", flush=True)
            continue

        page = best_task_match(message, tasks, assignee)
        if not page:
            print(f"No matching task found for commit by {author.get('login')}: {message}", flush=True)
            continue

        task_name = property_text(page.get("properties", {}), "Task")
        mark_task_done(page["id"])
        print(f"Marked Done: {task_name}", flush=True)
        updated.append(
            {
                "task": task_name,
                "assignee": assignee,
                "commit": message,
                "url": commit.get("html_url", ""),
            }
        )

    return updated


def tasks_by_user() -> dict[str, list[dict[str, str]]]:
    """Group active database tasks by Slack display name."""
    grouped: dict[str, list[dict[str, str]]] = {}
    for page in query_notion_tasks():
        props = page.get("properties", {})
        assignee = property_text(props, "Assignee") or "Unassigned"
        user = user_for_notion(assignee)
        display = user.get("slack_display_name") if user else assignee
        grouped.setdefault(display, []).append(
            {
                "task": property_text(props, "Task"),
                "assignee": assignee,
                "status": property_status(props) or TASK_STATUS_TODO,
            }
        )
    return grouped


def commits_by_user(commits: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Group commit messages by Slack display name."""
    grouped: dict[str, list[str]] = {}
    for commit in commits:
        author = commit.get("author") or {}
        user = user_for_github(author.get("login"))
        display = user.get("slack_display_name") if user else author.get("login", "Unknown")
        grouped.setdefault(display, []).append(commit.get("commit", {}).get("message", ""))
    return grouped


def format_progress_report(commits: list[dict[str, Any]], updated: list[dict[str, str]]) -> str:
    """Build Slack progress report."""
    task_groups = tasks_by_user()
    commit_groups = commits_by_user(commits)
    users = sorted(set(task_groups) | set(commit_groups))

    total_done = sum(1 for tasks in task_groups.values() for task in tasks if task["status"] == TASK_STATUS_DONE)
    total_not_done = sum(1 for tasks in task_groups.values() for task in tasks if task["status"] != TASK_STATUS_DONE)

    lines = [
        "*SyncMaster Team Progress Report*",
        f"*Summary:* {total_done} done, {total_not_done} not done. {len(updated)} task status update(s) from recent commits.",
        "",
    ]

    for user in users:
        tasks = task_groups.get(user, [])
        done_tasks = [task for task in tasks if task["status"] == TASK_STATUS_DONE]
        not_done_tasks = [task for task in tasks if task["status"] != TASK_STATUS_DONE]
        assignee = tasks[0]["assignee"] if tasks else user

        lines.append(f"*Assignee:* {assignee} ({user})")
        for message in commit_groups.get(user, []):
            lines.append(f"> Recent commit: {message}")

        lines.append(f"*Done ({len(done_tasks)}):*")
        lines.extend([f"- {task['task']}" for task in done_tasks] or ["- None"])

        lines.append(f"*Not Done ({len(not_done_tasks)}):*")
        lines.extend([f"- {task['task']}" for task in not_done_tasks] or ["- None"])
        lines.append("")

    if not users:
        lines.append("No tasks found in the active Notion database yet.")

    return "\n".join(lines).strip()


def send_to_slack(message: str) -> None:
    """Send report to Slack webhook."""
    webhook = env("SLACK_WEBHOOK_URL")
    if not webhook:
        raise RuntimeError("Missing SLACK_WEBHOOK_URL in .env")
    response = requests.post(webhook, json={"text": message}, timeout=30)
    response.raise_for_status()


def sync_once(send_slack: bool = True, force_slack: bool = False, import_tasks: bool = False) -> dict[str, Any]:
    """Run one sync pass."""
    import_result = import_meeting_tasks() if import_tasks else {"created": 0, "total": 0}
    state = load_state()
    commits = fetch_recent_commits()
    print_commit_log("FETCHED GITHUB COMMITS", commits)
    unseen = new_commits(commits, state)
    if not unseen and commits:
        print("No unseen commits from state; rechecking latest commit for recovery.", flush=True)
        unseen = commits[:1]
    print_commit_log("TRACKED NEW COMMITS", unseen)

    updated = update_tasks_from_commits(unseen) if unseen else []
    if commits:
        state["last_seen_sha"] = commits[0]["sha"]
        save_state(state)

    report = format_progress_report(unseen, updated)
    should_send_slack = send_slack and (force_slack or bool(unseen) or bool(updated))
    if should_send_slack:
        send_to_slack(report)

    return {
        "notion": import_result,
        "new_commits": len(unseen),
        "updated_tasks": updated,
        "slack_sent": should_send_slack,
        "report": report,
    }
