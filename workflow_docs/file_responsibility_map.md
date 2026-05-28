# File Responsibility Map

This page explains what each important file owns. It does not explain every line. It explains why the file exists and where it appears in the workflow.

## Frontend Files

### `web_app/index.html`

Defines the visible web app:

- meeting title input
- record button
- upload audio button
- `Check GitHub Commits` button
- `Send Progress Report` button
- summary text area

It does not do backend work by itself. It only provides the screen.

### `web_app/app.js`

Controls the web app behavior:

- records microphone audio
- uploads selected audio files
- sends requests to `http://127.0.0.1:5000`
- shows success and error messages
- displays the Gemini summary

Main calls:

```text
POST /transcribe       when audio is recorded or uploaded
POST /create-notion-db when Create Notion DB is clicked
GET /check-commits    when Check GitHub Commits is clicked
GET /send-standup     when Send Progress Report is clicked
```

### `extension/popup.html`

Defines the Chrome extension popup UI. It mirrors the web app controls.

### `extension/popup.js`

Controls the extension behavior. It uses the same backend routes as `web_app/app.js`, so the extension and web app trigger the same workflow.

## Backend Entry File

### `backend/server.py`

This is the Flask API. It connects frontend buttons to backend functions.

Routes:

```text
GET  /health
POST /transcribe
POST /create-notion-db
GET  /check-commits
GET  /send-standup
```

Why this file exists:

```text
Frontend JavaScript cannot directly call Python functions.
server.py exposes Python workflow functions as local HTTP routes.
```

Request path:

```text
Frontend button -> server.py route -> app.py or sync_pipeline.py
```

## AI Processing File

### `backend/app.py`

This file owns the meeting intelligence part:

```text
audio file -> Whisper transcript -> Gemini summary JSON -> meeting_summary.json
```

Important functions:

```text
transcribe(audio_path)
  uses Faster Whisper and prints the transcript

generate_summary(transcript)
  sends transcript to Gemini
  asks for strict JSON
  asks for readable summary text

process(audio_path)
  runs transcription and summary
  saves meeting_summary.json
```

Why `app.py` does not create Notion tasks:

```text
AI processing and workflow integrations are separate jobs.
app.py only produces the summary.
sync_pipeline.py decides what to do with that summary.
```

## Integration Workflow File

### `backend/sync_pipeline.py`

This file owns Notion, GitHub, and Slack.

It has three responsibilities:

```text
1. Create Notion task database from meeting_summary.json
2. Track GitHub commits and update Notion statuses
3. Build and send Slack progress reports
```

Main Notion flow:

```text
server.py:create_notion_db()
  -> import_meeting_tasks()
  -> build_task_input()
  -> extract_tasks_from_summary()
  -> create_notion_database()
  -> add_task_to_notion()
```

This flow starts only after the user clicks `Create Notion DB`.

Main GitHub flow:

```text
sync_once()
  -> fetch_recent_commits()
  -> new_commits()
  -> update_tasks_from_commits()
  -> mark_task_done()
```

Main Slack flow:

```text
sync_once()
  -> format_progress_report()
  -> send_to_slack()
```

Why one file owns all three:

```text
Notion, GitHub, and Slack are all part of the same progress-sync workflow.
The code needs to read Notion tasks, compare GitHub commits, then report that result to Slack.
Keeping those integration steps together makes the workflow easier to follow.
```

## Data Files

### `backend/meeting_summary.json`

The latest Gemini result.

Used by:

```text
sync_pipeline.py -> extract_tasks_from_summary()
```

Purpose:

```text
Stores the latest summary and action_items so Notion task creation has a clear source.
```

### `USER_MAPPING_JSON` Or `backend/user_mapping.json`

Maps team members across tools.

Example purpose:

```text
GitHub username "sahel-dev"
  -> Notion assignee "Sahel"
  -> Slack display name "Sahel"
```

Used when:

```text
GitHub commits need to update the correct Notion assignee.
Slack reports need readable team member names.
```

Deployment should use the private `USER_MAPPING_JSON` environment variable. Local development can use `backend/user_mapping.json`, which is ignored by git.

### `.env`

Stores secrets and active configuration.

Important values:

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

Special rule:

```text
Clicking Create Notion DB creates a new Notion database from meeting_summary.json.
The new database id replaces DATABASE_ID in .env.
```

### `backend/.sync_state.json`

Remembers the last GitHub commit checked.

This is not Notion task data. It only prevents the same old commit from being treated as new every time.

## Why The Explanation Is Workflow-First

The project is not linear like this:

```text
read all of app.py
then read all of server.py
then read all of sync_pipeline.py
```

The runtime path is more like this:

```text
web_app/app.js
  -> server.py
    -> app.py
    -> sync_pipeline.py
  -> web_app/app.js
```

That is why these docs jump between files. The jumping matches how the code actually runs.
