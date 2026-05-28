const API_URL = window.SYNCMASTER_API_URL || "http://127.0.0.1:5000";

let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let activeStream;

const statusDisplay = document.getElementById("status");
const summarySection = document.getElementById("summarySection");
const summaryEdit = document.getElementById("summaryEdit");
const toast = document.getElementById("toast");
const serverStatus = document.getElementById("serverStatus");
const recordBtn = document.getElementById("recordBtn");
const meetingTitleInput = document.getElementById("meetingTitle");
const uploadFile = document.getElementById("uploadFile");
const createNotionDbBtn = document.getElementById("createNotionDb");
const checkCommitsBtn = document.getElementById("checkCommits");
const sendStandupBtn = document.getElementById("sendStandup");

checkServerStatus();
setInterval(checkServerStatus, 30000);

async function checkServerStatus() {
  try {
    const response = await fetch(`${API_URL}/health`);
    if (!response.ok) {
      throw new Error("Backend server disconnected");
    }
    serverStatus.textContent = "Backend server connected";
    serverStatus.className = "server-status connected";
  } catch {
    serverStatus.textContent = "Backend server disconnected";
    serverStatus.className = "server-status disconnected";
  }
}

function showStatus(message, type = "") {
  statusDisplay.textContent = message;
  statusDisplay.className = `status${type ? ` ${type}` : ""}`;
}

function showToast(message, type = "") {
  toast.textContent = message;
  toast.className = `toast show${type ? ` ${type}` : ""}`;
  setTimeout(() => {
    toast.className = "toast";
  }, 3000);
}

function showSummary(summary) {
  summarySection.classList.add("show");
  summaryEdit.value = summary || "";
}

function hideSummary() {
  summarySection.classList.remove("show");
  summaryEdit.value = "";
}

function setRecordingUI(recording) {
  isRecording = recording;
  recordBtn.classList.toggle("recording", recording);
  recordBtn.querySelector(".label").textContent = recording ? "Stop Recording" : "Start Recording";
  showStatus(recording ? "Recording..." : "Ready to record", recording ? "processing" : "");
}

async function readJson(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.message || data.error || "Request failed");
  }
  return data;
}

async function callBackend(endpoint, action) {
  try {
    showStatus(`${action}...`, "processing");
    const data = await fetch(`${API_URL}${endpoint}`).then(readJson);
    showStatus(`${action} complete.`, "success");
    showToast(`${action} complete.`, "success");
    return data;
  } catch (error) {
    showStatus(error.message, "error");
    showToast(error.message, "error");
    return null;
  }
}

async function createNotionDb() {
  try {
    showStatus("Creating Notion DB...", "processing");
    const data = await fetch(`${API_URL}/create-notion-db`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ meetingTitle: meetingTitleInput.value || "Untitled Meeting" }),
    }).then(readJson);

    showStatus(`Notion DB created. Tasks: ${data.tasks.created}.`, "success");
    showToast("Notion DB created.", "success");
    return data;
  } catch (error) {
    showStatus(error.message, "error");
    showToast("Could not create Notion DB.", "error");
    return null;
  }
}

async function uploadAudio(audioBlob, filename = "meeting_audio.webm") {
  hideSummary();
  showStatus("Processing audio and generating summary JSON...", "processing");

  const formData = new FormData();
  formData.append("file", audioBlob, filename);
  formData.append("meetingTitle", meetingTitleInput.value || "Untitled Meeting");

  try {
    const data = await fetch(`${API_URL}/transcribe`, {
      method: "POST",
      body: formData,
    }).then(readJson);

    const formattedText = data.summary?.formatted_text;
    if (!formattedText) {
      throw new Error("Summary was not generated.");
    }

    showSummary(formattedText);
    showStatus("Summary JSON ready. Click Create Notion DB next.", "success");
    showToast("Summary generated.", "success");
  } catch (error) {
    showStatus(error.message, "error");
    showToast("Audio processing failed.", "error");
  }
}

async function startRecording() {
  try {
    activeStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(activeStream);
    audioChunks = [];

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.push(event.data);
      }
    };

    mediaRecorder.onstop = () => {
      const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
      activeStream.getTracks().forEach((track) => track.stop());
      activeStream = null;
      uploadAudio(audioBlob, "meeting_audio.webm");
    };

    mediaRecorder.start();
    setRecordingUI(true);
  } catch (error) {
    showStatus(error.message, "error");
    showToast("Microphone access failed.", "error");
  }
}

function stopRecording() {
  if (mediaRecorder && isRecording) {
    mediaRecorder.stop();
    setRecordingUI(false);
    showStatus("Processing audio...", "processing");
  }
}

recordBtn.addEventListener("click", () => {
  if (isRecording) {
    stopRecording();
  } else {
    startRecording();
  }
});

uploadFile.addEventListener("change", (event) => {
  const file = event.target.files[0];
  if (file) {
    uploadAudio(file, file.name);
  }
});

createNotionDbBtn.addEventListener("click", createNotionDb);
checkCommitsBtn.addEventListener("click", () => callBackend("/check-commits", "Check GitHub commits"));
sendStandupBtn.addEventListener("click", () => callBackend("/send-standup", "Send progress report"));

hideSummary();
setRecordingUI(false);
