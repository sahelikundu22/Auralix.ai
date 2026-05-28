# Auralix.ai

**Where Meetings Turn into Momentum**

[Watch Demo Video](https://youtu.be/b38ItkhMtxQ)

Auralix.ai is an AI-powered meeting assistant that records or uploads meeting audio, transcribes it with Whisper, extracts team tasks with Gemini, creates a Notion task database, tracks GitHub commits, and sends clean Slack progress reports.

This version is a cleaner independent rebuild of the original Hack4Bengal 4.0 project.

---

## Features

- **Meeting Audio Capture**: Record audio from the web app or Chrome extension, or upload an audio file.
- **AI Processing**: Faster Whisper transcription and Gemini task extraction.
- **Notion Sync**: Create a fresh Notion task database from Gemini-extracted tasks.
- **GitHub Monitoring**: Check commits from the last 24 hours, match them to assigned tasks, and update only the matching task status.
- **Slack Reporting**: Send one progress report with done and not-done tasks.
- **Simple Controls**: Upload audio, create Notion DB, check GitHub commits, and send Slack report.

---

## Architecture

```text
+-----------------------------------------------------------------------------+
|                               INPUT SOURCES                                  |
|        Chrome Extension  |  Web App  |  Microphone  |  Audio Upload          |
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
|        Gemini-extracted tasks kept in frontend memory until DB creation      |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
|                         TASK MANAGEMENT (NOTION)                             |
|        Create Notion DB  ->  Task Creation  |  Assignment  |  Status         |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
|                            GITHUB MONITORING                                 |
|        Commit Tracking  ->  Task Matching  ->  Auto Status Updates           |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
|                           PROGRESS REPORTING                                 |
|        Current Notion Status  ->  Team Progress Summary  ->  Slack           |
+-----------------------------------------------------------------------------+
```

---

## Quick Start

### 1. Setup

```bash
git clone <repo-url>
cd meeting
pip install -r requirements.txt
```

### 2. Configure Notion

Create one Notion parent page and connect it to your Notion integration. Put that page ID in `PARENT_PAGE_ID`.

### 3. Configure Environment

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

### 4. Configure User Mapping

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

### 5. Run Backend

```bash
python backend/server.py
```

### 6. Use Chrome Extension

1. Open `chrome://extensions/`.
2. Enable Developer Mode.
3. Click `Load unpacked`.
4. Select the `extension` folder.
5. Keep the backend running on `http://127.0.0.1:5000`.
6. Allow microphone permissions if prompted.

### Alternative: Use Web App

If you do not want to use the extension, start the web app instead:

```bash
cd web_app
python -m http.server 8001
```

Open:

```text
http://127.0.0.1:8001/index.html
```

---

## Workflow

1. **Record or Upload** -> Send meeting audio from the web app or extension.
2. **Process** -> Whisper transcribes audio and Gemini extracts task/assignee data.
3. **Create** -> Click `Create Notion DB`; the frontend sends the extracted tasks to the backend.
4. **Track** -> Click `Check GitHub Commits` to check the last 24 hours of commits and update matching task statuses.
5. **Report** -> Click `Send Progress Report` to send the Slack update.

---

## Structure

```text
meeting/
+-- backend/          # Flask backend, Whisper/Gemini, Notion/GitHub/Slack logic
+-- extension/        # Chrome extension
+-- web_app/          # Web interface
+-- workflow_docs/    # Extra workflow explanation docs
+-- requirements.txt  # Python dependencies
```

---

## Integrations

- **Notion**: Task database creation and status tracking.
- **Slack**: Progress report delivery through webhook.
- **GitHub**: Commit monitoring and task matching.
- **AI**: Faster Whisper transcription and Gemini task extraction.

---

## Notes

- Gemini-extracted tasks are sent directly from the frontend to Notion creation.
- GitHub tracking checks commits from the last 24 hours and skips tasks that are already `Done`.
- `DATABASE_ID` is updated when a new Notion database is created.
- For deployment, the backend uses `tiny.en` by default to reduce memory usage. You can change it to `small.en` in the environment for better transcription quality.

---

## Acknowledgement

This is not a team project. I independently rebuilt the application with cleaner code. The original idea, frontend code, and demo video were from our previous Hack4Bengal 4.0 team project, [sahelikundu22/Auralix.ai_H4B4.0](https://github.com/sahelikundu22/Auralix.ai_H4B4.0), which was awarded 2nd runner up at Hack4Bengal 4.0.

I also took help from Codex for understanding and improving certain parts.
