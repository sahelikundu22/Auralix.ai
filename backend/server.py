"""Flask API used by the web app and Chrome extension."""

import tempfile
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS #type:ignore

from app import process
from sync_pipeline import ENV_PATH, import_meeting_tasks, sync_once


load_dotenv(ENV_PATH, override=True)

app = Flask(__name__)
CORS(app)


# Clean task data before sending it to Notion.
def validate_tasks(tasks: list[dict]) -> list[dict]:
    if not tasks:
        raise RuntimeError("No extracted tasks found. Upload or record audio before creating the Notion DB.")

    cleaned = []
    print("\n========== EXTRACTED TASKS START ==========", flush=True)
    for task in tasks:
        task_name = str(task.get("task", "")).strip()
        assignee = str(task.get("assignee") or "Unassigned").strip()
        if task_name:
            cleaned.append({"task": task_name, "assignee": assignee})
            print(f"- {assignee}: {task_name}", flush=True)
    print("=========== EXTRACTED TASKS END ===========\n", flush=True)

    if not cleaned:
        raise RuntimeError("No valid task names found.")
    return cleaned


# Show basic backend status and available routes.
@app.get("/")
def home():
    return jsonify(
        {
            "status": "running",
            "service": "Auralix meeting automation",
            "endpoints": ["/health", "/transcribe", "/create-notion-db", "/check-commits", "/send-standup"],
        }
    )


# Health check used by the frontend.
@app.get("/health")
def health():
    return jsonify({"status": "healthy"})


# Receive audio and return extracted tasks.
@app.post("/transcribe")
def transcribe_audio():
    if "file" not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400

    audio_file = request.files["file"]
    suffix = Path(audio_file.filename or "meeting.wav").suffix or ".wav"
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            audio_file.save(temp.name)
            temp_path = Path(temp.name)

        summary = process(temp_path)
        return jsonify({"status": "success", "summary": summary})
    except Exception as exc:
        print(f"Request failed: {exc}", flush=True)
        return jsonify({"status": "error", "message": str(exc)}), 500
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


# Create a fresh Notion database from extracted tasks.
@app.post("/create-notion-db")
def create_notion_db():
    try:
        data = request.get_json(silent=True) or {}
        meeting_title = data.get("meetingTitle") or "Meeting"
        tasks = validate_tasks(data.get("tasks") or [])
        result = import_meeting_tasks(fresh_database=True, database_title=f"{meeting_title} Tasks", tasks=tasks)
        return jsonify({"status": "success", "tasks": result})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


# Check recent GitHub commits and update Notion.
@app.get("/check-commits")
def check_commits():
    try:
        return jsonify({"status": "success", **sync_once(send_slack=False)})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


# Send the current Notion progress report to Slack.
@app.get("/send-standup")
def send_standup():
    try:
        return jsonify({"status": "success", **sync_once(send_slack=True, force_slack=True)})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
