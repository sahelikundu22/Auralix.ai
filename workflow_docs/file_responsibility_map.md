# File Responsibility Map

This explains what each important file owns in the current workflow.

## Frontend

### `web_app/index.html`

Defines the web app screen: meeting title, record/upload controls, backend buttons, and status messages.

### `web_app/app.js`

Runs the web app behavior:

```text
record/upload audio
store Gemini-extracted tasks in memory
send tasks to /create-notion-db
trigger GitHub check and Slack report
```

### `extension/popup.html`

Defines the Chrome extension popup UI.

### `extension/popup.js`

Runs the same workflow as the web app, but inside the extension popup.

## Backend

### `backend/server.py`

Owns the Flask routes:

```text
POST /transcribe
POST /create-notion-db
GET  /check-commits
GET  /send-standup
```

It validates the extracted task list before sending it to the Notion workflow.

### `backend/app.py`

Owns AI processing:

```text
audio file
  -> Faster Whisper transcript
  -> Gemini task extraction
  -> task objects returned to the frontend
```

It does not create Notion tasks.

### `backend/sync_pipeline.py`

Owns external integrations:

```text
Notion database creation
GitHub commit fetching and task matching
Slack progress report formatting and sending
```

The Notion creation flow receives task objects directly from `server.py`.
The GitHub flow checks commits from the last 24 hours and lets Notion task status prevent duplicate updates.

## Private Data

### `USER_MAPPING_JSON` Or `backend/user_mapping.json`

Maps each team member across tools:

```text
GitHub username -> Notion assignee name -> Slack display name
```

Use `USER_MAPPING_JSON` for deployment. Local development can use `backend/user_mapping.json`, which is ignored by git.

### `.env`

Stores API keys and active configuration:

```text
GEMINI_API_KEY
NOTION_TOKEN
PARENT_PAGE_ID
DATABASE_ID
TOKEN_GITHUB
REPO_OWNER
REPO_NAME
SLACK_WEBHOOK_URL
```

## Why These Docs Jump Between Files

The runtime path is workflow-based:

```text
frontend button
  -> server.py route
    -> app.py for AI work
    -> sync_pipeline.py for integrations
  -> frontend status update
```

That is why the explanation follows the button flow instead of explaining one whole file at a time.
