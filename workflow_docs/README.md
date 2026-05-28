# SyncMaster Code Workflow Guide

This is not the main project README. The main user/deployment README is `../README.md`.

This folder explains the project by workflow, not by reading each file from top to bottom.

That is intentional. In this project, one user action moves through multiple files:

```text
button click -> Flask route -> AI processing -> Notion/GitHub/Slack helper functions -> response to UI
```

If you read one whole file at a time, the logic feels broken because the next important step may live in another file. These docs follow the same path the code follows at runtime.

## Read In This Order

1. [End-to-End Workflow](./end_to_end_workflow.md)
2. [File Responsibility Map](./file_responsibility_map.md)

## Main Idea

- `web_app/` and `extension/` are the user interfaces.
- `backend/server.py` receives button requests.
- `backend/app.py` handles Whisper and Gemini.
- `backend/sync_pipeline.py` handles Notion, GitHub, and Slack.
- `backend/meeting_summary.json` is the latest AI-generated meeting summary.
- `.env` stores API keys and the active Notion `DATABASE_ID`.
