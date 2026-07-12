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
const reportPointers = document.getElementById("report-pointers");

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
  
  reportPointers.innerHTML = "";
  const li = document.createElement("li");
  li.textContent = `The orchestrator run encountered an error: ${message}`;
  reportPointers.appendChild(li);
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

  // Clear existing pointers
  reportPointers.innerHTML = "";

  // Split feedback string programmatically by sentences or existing markdown points
  let points = [];
  const blocks = feedback.split(/\r?\n+/);
  for (let block of blocks) {
    block = block.trim();
    if (!block) continue;
    
    // Strip leading list characters: -, *, +, 1., 2. etc.
    const cleanBlock = block.replace(/^[\s\-\*\+\d\.\)]+\s*/, "").trim();
    if (!cleanBlock) continue;
    
    // Split block into sentences
    const sentences = cleanBlock.split(/(?<=[.!?])\s+(?=[A-Z0-9])/);
    for (let s of sentences) {
      s = s.trim();
      if (s) {
        points.push(s);
      }
    }
  }

  if (points.length === 0) {
    points.push("No feedback provided.");
  }

  // Append points to report-pointers list
  points.forEach(point => {
    const li = document.createElement("li");
    li.textContent = point;
    reportPointers.appendChild(li);
  });
}

// Filter and format logs dynamically based on content and bracket tags
function processLog(msg) {
  let cleanMessage = msg || "";

  // If a log line contains raw orchestrator dictionary payloads, strip it
  if (cleanMessage.includes("{'") || cleanMessage.includes('{"') || cleanMessage.includes("[{")) {
    if (cleanMessage.includes("History:")) {
      cleanMessage = cleanMessage.replace(/\s*History:[\s\S]*/i, "...");
    } else if (cleanMessage.includes("with parameters:")) {
      cleanMessage = cleanMessage.replace(/\s*with parameters:[\s\S]*/i, "...");
    } else {
      const match = cleanMessage.match(/[\{\[]/);
      if (match) {
        cleanMessage = cleanMessage.substring(0, match.index).trim() + "...";
      }
    }
  }

  // Format logs dynamically based on bracket tags
  let logClass = "verbose";
  if (cleanMessage.includes("[ERROR]")) {
    logClass = "error";
  } else if (cleanMessage.includes("[WARN]")) {
    logClass = "warn";
  } else if (cleanMessage.includes("[INFO]")) {
    logClass = "info";
  } else if (cleanMessage.includes("[VERBOSE]")) {
    logClass = "verbose";
  }

  appendConsoleLine(cleanMessage, logClass);
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
              processLog(payload.message);
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
            processLog(payload.message);
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

// Hero CTA smooth scroll to workspace
const heroCtaStart = document.getElementById("hero-cta-start");
if (heroCtaStart) {
  heroCtaStart.addEventListener("click", () => {
    const workspace = document.getElementById("workspace");
    if (workspace) {
      workspace.scrollIntoView({ behavior: "smooth" });
      // Auto-focus the editor after scrolling
      setTimeout(() => {
        solidityCodeEl.focus();
      }, 600);
    }
  });
}

// ================================================================
// CRYPTOGRAPHIC DECRYPTION TEXT REVEAL
// ================================================================
function decryptText(element, finalString, durationMs = 1800) {
  const hexChars = "0123456789ABCDEF";
  const len = finalString.length;
  const intervalMs = 30;
  const totalSteps = Math.floor(durationMs / intervalMs);
  let step = 0;

  // Initially show random hex for the full length
  element.textContent = Array.from({ length: len }, () =>
    hexChars[Math.floor(Math.random() * hexChars.length)]
  ).join("");

  const timer = setInterval(() => {
    step++;
    const resolvedCount = Math.floor((step / totalSteps) * len);
    let display = "";
    for (let i = 0; i < len; i++) {
      if (i < resolvedCount) {
        display += finalString[i];
      } else {
        display += hexChars[Math.floor(Math.random() * hexChars.length)];
      }
    }
    element.textContent = display;

    if (step >= totalSteps) {
      clearInterval(timer);
      element.textContent = finalString;
    }
  }, intervalMs);
}

// Trigger decryption on the hero headline
const heroHeadline = document.getElementById("hero-headline");
if (heroHeadline) {
  const finalText = heroHeadline.textContent;
  decryptText(heroHeadline, finalText, 1800);
}

// ================================================================
// CONSENSUS GRID — Interactive Particle Network Canvas
// ================================================================
(function initParticleNetwork() {
  const canvas = document.getElementById("web3-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  let width, height;
  let mouse = { x: -9999, y: -9999 };
  const NODE_COUNT = 60;
  const CONNECT_DIST = 140;
  const MOUSE_RADIUS = 180;
  const nodes = [];

  function resize() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener("resize", resize);

  // Track mouse position
  document.addEventListener("mousemove", (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
  });

  // Seed nodes
  for (let i = 0; i < NODE_COUNT; i++) {
    nodes.push({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      radius: Math.random() * 1.5 + 0.8,
    });
  }

  function tick() {
    ctx.clearRect(0, 0, width, height);

    for (let i = 0; i < nodes.length; i++) {
      const n = nodes[i];

      // Mouse repulsion
      const mdx = n.x - mouse.x;
      const mdy = n.y - mouse.y;
      const mDist = Math.sqrt(mdx * mdx + mdy * mdy);
      if (mDist < MOUSE_RADIUS && mDist > 0) {
        const force = (MOUSE_RADIUS - mDist) / MOUSE_RADIUS * 0.6;
        n.vx += (mdx / mDist) * force;
        n.vy += (mdy / mDist) * force;
      }

      // Damping
      n.vx *= 0.98;
      n.vy *= 0.98;

      // Move
      n.x += n.vx;
      n.y += n.vy;

      // Wrap around edges
      if (n.x < 0) n.x = width;
      if (n.x > width) n.x = 0;
      if (n.y < 0) n.y = height;
      if (n.y > height) n.y = 0;

      // Draw node
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(94, 234, 212, 0.5)";
      ctx.fill();

      // Draw connections
      for (let j = i + 1; j < nodes.length; j++) {
        const o = nodes[j];
        const dx = n.x - o.x;
        const dy = n.y - o.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < CONNECT_DIST) {
          const alpha = 1 - dist / CONNECT_DIST;
          ctx.beginPath();
          ctx.moveTo(n.x, n.y);
          ctx.lineTo(o.x, o.y);
          ctx.strokeStyle = `rgba(94, 234, 212, ${0.2 * alpha})`;
          ctx.lineWidth = 0.6;
          ctx.stroke();
        }
      }
    }

    requestAnimationFrame(tick);
  }

  requestAnimationFrame(tick);
})();
