# Auralix.ai

**Where Meetings Turn into Momentum**

📹 **[Watch Demo Video](https://youtu.be/b38ItkhMtxQ)**

Auralix.ai is an AI-powered meeting assistant that records or uploads team meeting audio, transcribes it with Whisper, summarizes it with Gemini, creates team tasks in Notion, tracks GitHub commits, and sends clean Slack progress reports.

The current version uses one backend folder: `backend`.

---

## 🚀 Features

- **🎙️ Meeting Audio Capture**: Record from the web app or Chrome extension, or upload an audio file.
- **🤖 AI Processing**: Faster Whisper transcription plus Gemini meeting summary and task extraction.
- **📋 Notion Task Creation**: Click `Create Notion DB` after a summary is generated to create a fresh task database under one parent page.
- **🐙 GitHub Tracking**: Checks commits and marks the matching assigned task as `Done`.
- **📤 Slack Progress Report**: Sends one formatted report with assignee, done tasks, not-done tasks, and progress summary.
- **🧭 Simple Controls**: `Check GitHub Commits` updates Notion, and `Send Progress Report` posts to Slack.

---

## 🏗️ Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                              INPUT SOURCES                                  │
│        Web App  |  Chrome Extension  |  Microphone  |  Audio Upload         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AI PROCESSING ENGINE                                │
│        Faster Whisper transcription  →  Gemini summary and task JSON        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TASK MANAGEMENT                                     │
│        New Notion database under PARENT_PAGE_ID  →  task rows created       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GITHUB MONITORING                                   │
│        Commit author + message matching  →  matching task becomes Done      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SLACK REPORTING                                     │
│        Done tasks + Not Done tasks + progress summary                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Quick Start

### 1. Setup

```bash
git clone <repo-url>
cd meeting
pip install -r requirements.txt
```

If you are using the included virtual environment on Windows:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. Create A Notion Parent Page

Create one Notion page and connect it to your Notion integration. Auralix will create a new task database inside that parent page when you click `Create Notion DB`.

### 3. Configure

Create a `.env` file in the project root:

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
```

`DATABASE_ID` is updated automatically whenever `Create Notion DB` creates a new Notion database. If you want to continue tracking an older meeting, paste the old database ID into `.env`, restart the backend, then use the GitHub or Slack buttons.

### 4. Run The Backend

```bash
python backend/server.py
```

With the included Windows virtual environment:

```powershell
.\venv\Scripts\python.exe backend\server.py
```

The backend runs at:

```text
http://127.0.0.1:5000
```

Whisper prints the meeting transcript in this backend terminal.

### 5. Use The Web App

Open another terminal:

```powershell
cd web_app
..\venv\Scripts\python.exe -m http.server 8000
```

Then open:

```text
http://127.0.0.1:8000/index.html
```

### 6. Install The Chrome Extension

1. Open `chrome://extensions/`.
2. Enable Developer Mode.
3. Click `Load unpacked`.
4. Select the `extension` folder.
5. Keep the backend running on `http://127.0.0.1:5000`.
6. Allow microphone permissions when recording.

---

## 🔄 Workflow

1. **Record or Upload** → Use the web app or extension to send meeting audio.
2. **Transcribe** → Whisper converts audio to text and prints the transcript in the terminal.
3. **Summarize** → Gemini creates a readable summary and structured task JSON.
4. **Create Tasks** → Click `Create Notion DB` to create a new database from `meeting_summary.json`.
5. **Track Commits** → `Check GitHub Commits` marks the matching task for the mapped commit author as `Done`.
6. **Report** → `Send Progress Report` sends the current task status to Slack.

---

## 📁 Structure

```text
meeting/
├── backend/
│   └── whisper_api/
│       ├── app.py                # Whisper + Gemini processing
│       ├── server.py             # Flask API
│       ├── sync_pipeline.py      # Notion, GitHub, Slack workflow
│       ├── user_mapping.json     # Local-only team member mapping fallback
│       └── meeting_summary.json  # Latest generated summary
├── extension/                    # Chrome extension
├── web_app/                      # Web interface
├── requirements.txt              # Python dependencies
└── README.md
```

---

## 🔗 Integrations

- **📝 Notion**: Fresh task database when `Create Notion DB` is clicked.
- **💬 Slack**: One clean progress report button.
- **🐙 GitHub**: Commit monitoring and task status updates.
- **🤖 AI**: Faster Whisper transcription and Gemini analysis.

---

## 🐛 Notes

- `meeting_summary.json` is the source for task creation.
- `USER_MAPPING_JSON` connects GitHub usernames to Notion assignees and Slack display names in deployment.
- `backend/user_mapping.json` can still be used locally, but it is ignored by git.
- `.sync_state.json` only remembers the last GitHub commit checked.
- To reuse an old Notion database, manually update `DATABASE_ID` in `.env` and restart the backend.
- For a workflow-first code explanation, read `workflow_docs/README.md`. That is a docs index, not a second project README.

---

## 🚢 Deployment

Deploy the backend and frontend separately.

### Backend On Render

1. Push this project to GitHub.
2. Open Render and create a new `Web Service`.
3. Connect your GitHub repo.
4. Use these settings:

```text
Build Command:
pip install -r requirements.txt

Start Command:
gunicorn --chdir backend server:app
```

This repo also includes `render.yaml`, so Render can detect the same backend settings from the repo.

Add these environment variables in Render:

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
```

After deployment, Render gives you a backend URL like:

```text
https://syncmaster-backend.onrender.com
```

### Web App On Vercel Or Netlify

Before deploying the web app, open `web_app/config.js` and replace localhost with your deployed backend URL:

```js
window.SYNCMASTER_API_URL = "https://your-backend-url.onrender.com";
```

Deploy `web_app` as a static site:

```text
Root / publish directory:
web_app

Build command:
leave empty
```

### Chrome Extension After Backend Deploy

Update `extension/popup.js`:

```js
const API_URL = "https://your-backend-url.onrender.com";
```

Update `extension/manifest.json`:

```json
"host_permissions": ["https://your-backend-url.onrender.com/*"]
```

Then reload the unpacked extension from `chrome://extensions/`.

### Deployment Note

When `Create Notion DB` runs, the backend updates `DATABASE_ID` at runtime. On free hosts, that value can reset after redeploy or sleep. If that happens, copy the created Notion database ID into the host dashboard environment variable `DATABASE_ID`.

---

**Built for efficient team collaboration.**
