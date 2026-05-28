const API_URL = "http://127.0.0.1:5000";

let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let activeStream;
let latestTasks = [];

const statusDisplay = document.getElementById("status");
const toast = document.getElementById("toast");
const recordBtn = document.getElementById("recordBtn");
const meetingTitleInput = document.getElementById("meetingTitle");
const uploadFile = document.getElementById("uploadFile");
const createNotionDbBtn = document.getElementById("createNotionDb");
const checkCommitsBtn = document.getElementById("checkCommits");
const sendStandupBtn = document.getElementById("sendStandup");

// Show the current workflow status in the popup.
function showStatus(message, type = "") {
  const text = statusDisplay.querySelector(".status-text");
  if (text) {
    text.textContent = message;
  } else {
    statusDisplay.textContent = message;
  }
  statusDisplay.className = `status${type ? ` ${type}` : ""}`;
}

// Show a short popup message.
function showToast(message, type = "") {
  toast.textContent = message;
  toast.className = `toast show${type ? ` ${type}` : ""}`;
  setTimeout(() => {
    toast.className = "toast";
  }, 3000);
}

// Update the record button while recording starts or stops.
function setRecordingUI(recording) {
  isRecording = recording;
  recordBtn.classList.toggle("recording", recording);
  recordBtn.querySelector(".label").textContent = recording ? "Stop Recording" : "Start Recording";
  showStatus(recording ? "Recording..." : "Ready to record", recording ? "processing" : "");
}

// Parse backend JSON and throw useful errors.
async function readJson(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.message || data.error || "Request failed");
  }
  return data;
}

// Call a simple backend route and show status.
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

// Send extracted tasks to create a Notion database.
async function createNotionDb() {
  try {
    if (!latestTasks.length) {
      throw new Error("No tasks ready yet. Upload or record audio first.");
    }

    showStatus("Creating Notion DB...", "processing");
    const data = await fetch(`${API_URL}/create-notion-db`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        meetingTitle: meetingTitleInput.value || "Untitled Meeting",
        tasks: latestTasks,
      }),
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

// Upload audio to backend and store extracted tasks.
async function uploadAudio(audioBlob, filename = "meeting_audio.webm") {
  latestTasks = [];
  showStatus("Processing audio and extracting tasks...", "processing");

  const formData = new FormData();
  formData.append("file", audioBlob, filename);
  formData.append("meetingTitle", meetingTitleInput.value || "Untitled Meeting");

  try {
    const data = await fetch(`${API_URL}/transcribe`, {
      method: "POST",
      body: formData,
    }).then(readJson);

    latestTasks = data.summary?.tasks || [];
    if (!latestTasks.length) {
      throw new Error("No tasks were extracted.");
    }

    showStatus(`Tasks ready: ${latestTasks.length}. Click Create Notion DB next.`, "success");
    showToast("Tasks extracted.", "success");
  } catch (error) {
    showStatus(error.message, "error");
    showToast("Audio processing failed.", "error");
  }
}

// Start microphone recording from the extension popup.
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

// Stop recording and trigger audio upload.
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

setRecordingUI(false);
