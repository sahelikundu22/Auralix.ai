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
Audio Upload / Recording
        |
        v
Whisper transcript
        |
        v
Gemini task JSON: task + assignee
        |
        v
meeting_summary.json
        |
        v
Create Notion DB button
        |
        v
GitHub commit tracking -> matching task marked Done
        |
        v
Slack progress report
```

## Project Structure

```text
meeting/
├── backend/
│   ├── app.py                # Whisper + Gemini task extraction
│   ├── server.py             # Flask API
│   ├── sync_pipeline.py      # Notion, GitHub, Slack workflow
│   ├── meeting_summary.json  # Latest generated task summary
│   └── user_mapping.json     # Local-only mapping fallback, ignored by git
├── extension/                # Chrome extension
├── web_app/                  # Static web app
├── workflow_docs/            # Extra workflow explanation docs
├── requirements.txt
└── render.yaml
```

## Environment Variables

Create `.env` locally, and add the same values in Render for deployment:

```env
GEMINI_API_KEY=your_gemini_api_key
NOTION_TOKEN=your_notion_integration_token
PARENT_PAGE_ID=your_notion_parent_page_id
DATABASE_ID=optional_existing_database_id
USER_MAPPING_JSON={"saheli":{"github_username":"your_github","notion_name":"Saheli","slack_display_name":"Saheli"}}
TOKEN_GITHUB=your_github_personal_access_token
REPO_OWNER=your_github_username_or_org
REPO_NAME=your_repository_name
SLACK_WEBHOOK_URL=your_slack_webhook_url
WHISPER_MODEL=tiny.en
```

`USER_MAPPING_JSON` is private team mapping data. Locally, you can use `backend/user_mapping.json` instead, but that file is ignored by git.

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

## Deploy

Deploy the backend and frontend separately.

### Backend On Render

Choose `Web Service`.

```text
Root Directory:
leave empty

Build Command:
pip install -r requirements.txt

Start Command:
gunicorn --chdir backend server:app
```

Add all environment variables from the section above in Render.

Render Free has 512 MB RAM, so use:

```env
WHISPER_MODEL=tiny.en
```

If Whisper still causes memory issues, use a larger Render instance or move transcription to an external API.

### Web App On Vercel Or Netlify

Set the static site directory to:

```text
web_app
```

Before deploying, update `web_app/config.js`:

```js
window.AURALIX_API_URL = "https://your-render-backend-url.onrender.com";
```

### Chrome Extension

Update `extension/popup.js`:

```js
const API_URL = "https://your-render-backend-url.onrender.com";
```

Update `extension/manifest.json`:

```json
"host_permissions": ["https://your-render-backend-url.onrender.com/*"]
```

Reload the unpacked extension from `chrome://extensions/`.

## Notes

- `meeting_summary.json` is the source for Notion task creation.
- `DATABASE_ID` is updated when a new Notion database is created.
- On hosted platforms, runtime file changes can reset after redeploy. If needed, copy the latest Notion database ID into the hosted `DATABASE_ID` environment variable.
- Extra workflow explanations are in `workflow_docs/end_to_end_workflow.md` and `workflow_docs/file_responsibility_map.md`.

## Acknowledgement

This is not a team project. I independently rebuilt the application with cleaner code. The original idea, frontend code, and demo video were from our previous Hack4Bengal 4.0 team project, [sahelikundu22/Auralix.ai_H4B4.0](https://github.com/sahelikundu22/Auralix.ai_H4B4.0), which was awarded 2nd runner up at Hack4Bengal 4.0.

I also took help from Codex for understanding and improving certain parts.
