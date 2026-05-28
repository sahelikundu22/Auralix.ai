# Auralix.ai

**Where Meetings Turn into Momentum**

[Watch Demo Video](https://youtu.be/b38ItkhMtxQ)

Auralix.ai is an AI-powered meeting assistant that records or uploads meeting audio, transcribes it with Whisper, extracts tasks with Gemini, creates a Notion task database, tracks GitHub commits, and sends Slack progress reports.

## Features

- Record or upload meeting audio from the web app or Chrome extension.
- Transcribe audio with Faster Whisper.
- Extract only task name and assignee with Gemini.
- Create a fresh Notion database from the latest `meeting_summary.json`.
- Match GitHub commits to assigned tasks and mark only the matching task as `Done`.
- Send one Slack progress report using current Notion task statuses.

## Workflow

```text
+-----------------------------------------------------------------------------+
|                               INPUT SOURCES                                  |
|        Web App  |  Chrome Extension  |  Microphone  |  Audio Upload          |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
|                            AI PROCESSING                                     |
|        Faster Whisper transcript  ->  Gemini task JSON: task + assignee      |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
|                              TASK SOURCE                                     |
|        Latest task summary is saved in backend/meeting_summary.json          |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
|                            NOTION WORKFLOW                                   |
|        Create Notion DB button  ->  new task database under parent page      |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
|                            GITHUB TRACKING                                   |
|        Commit author + message matching  ->  matching task becomes Done      |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
|                            SLACK REPORTING                                   |
|        Done tasks + Not Done tasks + assignee progress summary               |
+-----------------------------------------------------------------------------+
```

## Project Structure

```text
meeting/
+-- backend/
|   +-- app.py                # Whisper + Gemini task extraction
|   +-- server.py             # Flask API
|   +-- sync_pipeline.py      # Notion, GitHub, Slack workflow
|   +-- meeting_summary.json  # Latest generated task summary
|   +-- user_mapping.json     # Local-only mapping fallback, ignored by git
+-- extension/                # Chrome extension
+-- web_app/                  # Static web app
+-- workflow_docs/            # Extra workflow explanation docs
+-- requirements.txt
```

Create a `.env` file in the project root:

```env
# Google
GEMINI_API_KEY=your_gemini_api_key

# GitHub Integration
TOKEN_GITHUB=your_github_personal_access_token
REPO_OWNER=your_github_username_or_org
REPO_NAME=your_working_repository_name

# Slack Configuration
SLACK_WEBHOOK_URL=your_slack_webhook_url

# Notion Configuration
NOTION_TOKEN=your_notion_integration_token
PARENT_PAGE_ID=your_notion_parent_page_id
DATABASE_ID=optional_existing_database_id
```

Create one Notion parent page, connect it to your Notion integration, and put that page ID in `PARENT_PAGE_ID`.

User mapping connects GitHub commit authors to Notion assignees and Slack display names. Add one entry for every team member whose commits should update tasks.

For local use, create:

```text
backend/user_mapping.json
```

Example:

```json
{
  "member_one": {
    "github_username": "member_one_github",
    "notion_name": "Member One",
    "slack_display_name": "Member One"
  },
  "member_two": {
    "github_username": "member_two_github",
    "notion_name": "Member Two",
    "slack_display_name": "Member Two"
  }
}
```

`backend/user_mapping.json` is ignored by git so private member mapping does not get pushed.

You can also use this `.env` variable instead of the file:

```env
USER_MAPPING_JSON={"member_one":{"github_username":"member_one_github","notion_name":"Member One","slack_display_name":"Member One"},"member_two":{"github_username":"member_two_github","notion_name":"Member Two","slack_display_name":"Member Two"}}
```

## Run Locally

Install dependencies:

```powershell
pip install -r requirements.txt
```

Start backend:

```powershell
python backend\server.py
```

Start web app in another terminal:

```powershell
cd web_app
python -m http.server 8001
```

Open:

```text
http://127.0.0.1:8001/index.html
```

Use order:

1. Upload or record audio.
2. Click `Create Notion DB`.
3. Click `Check GitHub Commits`.
4. Click `Send Progress Report`.

## Notes

- `meeting_summary.json` is the source for Notion task creation.
- `DATABASE_ID` is updated when a new Notion database is created.
- For deployment, the backend uses `tiny.en` by default to reduce memory usage. You can change it to `small.en` in the environment if you want better transcription quality.
- Extra workflow explanations are in `workflow_docs/end_to_end_workflow.md` and `workflow_docs/file_responsibility_map.md`.

## Acknowledgement

This is not a team project. I independently rebuilt the application with cleaner code. The original idea, frontend code, and demo video were from our previous Hack4Bengal 4.0 team project, [sahelikundu22/Auralix.ai_H4B4.0](https://github.com/sahelikundu22/Auralix.ai_H4B4.0), which was awarded 2nd runner up at Hack4Bengal 4.0.

I also took help from Codex for understanding and improving certain parts.
