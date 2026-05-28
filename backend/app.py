"""Audio transcription and Gemini task extraction."""

import json
import os
import re
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv
from faster_whisper import WhisperModel  # type: ignore


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
SUMMARY_PATH = BASE_DIR / "meeting_summary.json"
LATEST_TRANSCRIPT_PATH = BASE_DIR / "latest_transcript.txt"

load_dotenv(dotenv_path=ROOT_DIR / ".env", override=True)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = WhisperModel("small.en", device="cpu", compute_type="int8")


def print_transcript(text: str, label: str = "TRANSCRIPT") -> None:
    print(f"\n========== {label} START ==========", flush=True)
    print(text, flush=True)
    print(f"=========== {label} END ===========\n", flush=True)


def transcribe(audio_path: Path) -> str:
    segments, _ = model.transcribe(str(audio_path), language="en", beam_size=5)
    text = " ".join(segment.text for segment in segments).strip()
    if not text:
        raise RuntimeError("Whisper returned an empty transcript. Check that the uploaded file contains clear speech.")

    print_transcript(text)
    LATEST_TRANSCRIPT_PATH.write_text(text, encoding="utf-8")
    return text


# Debug shortcut if you want to test Gemini without retranscribing audio.
# def transcribe(audio_path: Path) -> str:
#     if not LATEST_TRANSCRIPT_PATH.exists():
#         raise RuntimeError(f"{LATEST_TRANSCRIPT_PATH} does not exist yet.")
#     text = LATEST_TRANSCRIPT_PATH.read_text(encoding="utf-8").strip()
#     if not text:
#         raise RuntimeError(f"{LATEST_TRANSCRIPT_PATH} is empty.")
#     print_transcript(text, "TRANSCRIPT FROM FILE")
#     return text


def clean_json_text(text: str) -> str:
    text = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE)
    return text.replace("```", "").strip()


def format_summary(tasks: list[dict]) -> str:
    if not tasks:
        return "No tasks were found in the meeting transcript."

    lines = ["Meeting Tasks", ""]
    for task in tasks:
        assignee = task.get("assignee") or "Unassigned"
        lines.append(f"- {assignee}: {task.get('task', '').strip()}")
    return "\n".join(lines)


def generate_summary(transcript: str) -> dict:
    try:
        gemini_model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"""
Convert this meeting transcript into STRICT VALID JSON only.

Transcript:
{transcript}

Return ONLY this format:

{{
  "action_items": [
    {{
      "task": "",
      "assignee": null
    }}
  ]
}}

Rules:
- Output valid JSON only.
- No markdown.
- No explanation.
- Include only real tasks discussed in the meeting.
- Use null for assignee when no person is clearly assigned.
"""
        raw_json = gemini_model.generate_content(prompt).text
        structured_data_json = json.loads(clean_json_text(raw_json))
        tasks = structured_data_json.get("action_items", [])

        return {
            "structured_data_json": {"action_items": tasks},
            "raw_json": raw_json,
            "formatted_text": format_summary(tasks),
        }
    except Exception as exc:
        return {
            "error": str(exc),
            "structured_data_json": {"action_items": []},
            "formatted_text": None,
        }


def process(audio_path: Path) -> dict:
    transcript = transcribe(audio_path)
    result = generate_summary(transcript)

    if not result.get("formatted_text"):
        raise RuntimeError(result.get("error") or "Gemini did not return usable task JSON.")

    SUMMARY_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Saved: {SUMMARY_PATH}", flush=True)
    return result
