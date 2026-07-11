// Register PWA service worker
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js")
      .then((reg) => {
        console.log("Service Worker registered successfully.", reg.scope);
      })
      .catch((err) => {
        console.error("Service Worker registration failed:", err);
      });
  });
}

// DOM Elements
const auditButton = document.getElementById("audit-button");
const solidityCodeEl = document.getElementById("solidity-code");
const consoleOutput = document.getElementById("console-output");
const statusDot = document.getElementById("status-dot");
const statusText = document.getElementById("status-text");

const reportPlaceholder = document.getElementById("report-placeholder");
const reportDetails = document.getElementById("report-details");
const reportStatus = document.getElementById("report-status");
const reportSeverityVal = document.getElementById("report-severity-val");
const reportFeedback = document.getElementById("report-feedback");
const reportRaw = document.getElementById("report-raw");

// Utility to update header status
function updateSystemStatus(text, state) {
  statusText.textContent = text;
  statusDot.className = "status-indicator";
  if (state) {
    statusDot.classList.add(state);
  }
}

// Append line to console
function appendConsoleLine(text, className = "verbose") {
  const lineEl = document.createElement("div");
  lineEl.className = `console-line ${className}`;
  lineEl.textContent = text;
  consoleOutput.appendChild(lineEl);
  consoleOutput.scrollTop = consoleOutput.scrollHeight;
}

// Clear console
function clearConsole() {
  consoleOutput.innerHTML = "";
}

// Render error in the report card
function renderErrorInReport(message) {
  reportPlaceholder.style.display = "none";
  reportDetails.style.display = "flex";

  reportStatus.textContent = "FAILURE";
  reportStatus.className = "report-status-badge badge-failed";
  reportSeverityVal.textContent = "UNKNOWN";
  reportSeverityVal.style.color = "var(--status-error)";
  reportFeedback.textContent = `The orchestrator run encountered an error:\n\n${message}`;
  reportRaw.textContent = JSON.stringify({ status: "error", error: message }, null, 2);
}

// Render report in the card
function renderReport(data) {
  reportPlaceholder.style.display = "none";
  reportDetails.style.display = "flex";

  // Safely extract properties with defaults matching the Critic JSON schema
  const passed = data.passed;
  const severity = data.severity || "Unknown";
  const feedback = data.feedback || "No feedback provided.";

  reportStatus.textContent = passed ? "PASSED" : "FAILED";
  reportStatus.className = `report-status-badge ${passed ? "badge-passed" : "badge-failed"}`;
  
  reportSeverityVal.textContent = severity.toUpperCase();
  
  const sevLower = severity.toLowerCase();
  if (sevLower === "secure" || passed === true) {
    reportSeverityVal.style.color = "var(--status-success)";
  } else if (sevLower === "high" || sevLower === "critical") {
    reportSeverityVal.style.color = "var(--status-error)";
  } else if (sevLower === "medium" || sevLower === "low") {
    reportSeverityVal.style.color = "var(--status-warning)";
  } else {
    reportSeverityVal.style.color = "var(--text-primary)";
  }

  reportFeedback.textContent = feedback;
  reportRaw.textContent = JSON.stringify(data, null, 2);
}

// Main audit request execution
async function runAudit() {
  const contractCode = solidityCodeEl.value.trim();
  if (!contractCode) {
    alert("Please enter Solidity code before auditing.");
    return;
  }

  // UI state updates: Start auditing
  clearConsole();
  updateSystemStatus("AUDITING CONTRACT...", "processing");
  auditButton.disabled = true;
  
  // Reset report panel
  reportDetails.style.display = "none";
  reportPlaceholder.style.display = "flex";
  reportPlaceholder.innerHTML = `
    <div style="animation: pulse 1s infinite ease-in-out; color: var(--accent-color);">
      AUDIT PROCESSING...
    </div>
  `;

  try {
    const response = await fetch("/api/audit", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ contract: contractCode })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    let reportData = null;

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      let lines = buffer.split("\n");
      buffer = lines.pop(); // Keep any partial line in buffer

      for (const line of lines) {
        const trimmedLine = line.trim();
        if (trimmedLine.startsWith("data: ")) {
          const rawData = trimmedLine.substring(6).trim();
          try {
            const payload = JSON.parse(rawData);
            
            if (payload.type === "log") {
              const msg = payload.message || "";
              let logClass = "verbose";
              if (msg.startsWith("[INFO]")) {
                logClass = "info";
              } else if (msg.startsWith("[WARN]")) {
                logClass = "warn";
              }
              appendConsoleLine(msg, logClass);
            } else if (payload.type === "error") {
              appendConsoleLine(`[ERROR] ${payload.message}`, "error");
              renderErrorInReport(payload.message);
              updateSystemStatus("AUDIT FAILED", "error");
            } else if (payload.type === "report") {
              reportData = payload.data;
            }
          } catch (e) {
            console.error("Failed to parse SSE JSON payload:", e, trimmedLine);
          }
        }
      }
    }

    // Process any leftover text in the buffer
    if (buffer.trim()) {
      const trimmedLine = buffer.trim();
      if (trimmedLine.startsWith("data: ")) {
        const rawData = trimmedLine.substring(6).trim();
        try {
          const payload = JSON.parse(rawData);
          if (payload.type === "log") {
            appendConsoleLine(payload.message, "verbose");
          } else if (payload.type === "error") {
            appendConsoleLine(`[ERROR] ${payload.message}`, "error");
            renderErrorInReport(payload.message);
            updateSystemStatus("AUDIT FAILED", "error");
          } else if (payload.type === "report") {
            reportData = payload.data;
          }
        } catch (e) {
          console.error("Failed to parse leftover SSE JSON payload:", e, trimmedLine);
        }
      }
    }

    // Finalize report render if available
    if (reportData) {
      renderReport(reportData);
      updateSystemStatus("AUDIT COMPLETED", "active");
    } else {
      // If done but no report was parsed
      const currentStatus = statusText.textContent;
      if (currentStatus !== "AUDIT FAILED") {
        renderErrorInReport("Stream ended without returning a final Critic report.");
        updateSystemStatus("AUDIT FAILED", "error");
      }
    }

  } catch (error) {
    console.error("Error executing audit:", error);
    appendConsoleLine(`[CRITICAL ERROR] ${error.message}`, "error");
    renderErrorInReport(error.message);
    updateSystemStatus("CONNECTION ERROR", "error");
  } finally {
    // Restore button status
    auditButton.disabled = false;
    // Restore placeholder structure back to default
    if (reportDetails.style.display !== "flex") {
      reportPlaceholder.innerHTML = `
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
          <line x1="9" y1="9" x2="15" y2="9"/>
          <line x1="9" y1="13" x2="15" y2="13"/>
          <line x1="9" y1="17" x2="11" y2="17"/>
        </svg>
        <div>No audit performed yet.</div>
      `;
    }
  }
}

// Wire Event Listener
auditButton.addEventListener("click", runAudit);
