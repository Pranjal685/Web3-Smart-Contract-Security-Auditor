# Token-Guard // Web3 Smart Contract Security Auditor

**AI-powered multi-agent security auditing for Solidity smart contracts.**

Token-Guard is an agentic router that orchestrates Builder and Critic AI agents to reach consensus on your smart contract's vulnerabilities — in under 3 iterations, with zero human review overhead.

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)
![Gemini](https://img.shields.io/badge/Google%20Gemini-Flash-orange.svg)
![Tests](https://img.shields.io/badge/tests-20%20passed-brightgreen.svg)

---

## 🎯 Motivation & Origin

Token-Guard started as an intensive, deep-dive research project into harness engineering and autonomous agent orchestration loops. Driven by the challenge of moving beyond static security scripts, the goal was to explore how multi-agent architectures could dynamically converge on complex smart contract logic flaws—like reentrancy and precision loss—without manual human intervention hooks. What began as a foundational exploration of agent loop mechanics evolved over a month of rapid prototyping into a production-grade, compute-efficient security pipeline. This project stands as a definitive proof-of-concept demonstrating that dynamic, localized LLM consensus models can achieve rapid, automated vulnerability remediation with optimized token efficiency.

---

## Architecture

Token-Guard enforces a strict **separation of concerns** across three core components to prevent monolithic generative coding hazards:

```
┌─────────────────────────────────────────────────┐
│                  ORCHESTRATOR                   │
│         Coordinates execution lifecycle         │
│                                                 │
│   ┌──────────────┐      ┌──────────────────┐    │
│   │ BUILDER AGENT│ ──►  │  CRITIC AGENT    │    │
│   │ (Vuln Analyst│      │  (Lead Auditor)  │    │
│   │  Code Gen)   │ ◄──  │  JSON Verdict)   │    │
│   └──────────────┘      └──────────────────┘    │
│                                                 │
│   ┌────────────────────────────────────────┐    │
│   │     LOOP PROTECTION MIDDLEWARE         │    │
│   │  Regex-based 3-call circuit breaker    │    │
│   └────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

| Component | Role | Boundary |
|---|---|---|
| **Orchestrator** | Coordinates execution, delegates tasks | Never writes code or evaluates |
| **Builder Agent** | DeFi vulnerability analyzer, generates code | Never evaluates its own output |
| **Critic Agent** | Lead smart contract auditor, JSON verdict | Never writes application code |
| **Loop Guard** | Regex middleware, terminates on 3 identical consecutive calls | Hard-cap 3-iteration limit |

Both agents use **Google Gemini Flash** for inference via raw HTTP (`urllib.request`), with zero external AI SDK dependencies.

### Core Orchestration Pipeline & Subsystems

1. **The Multi-Agent Consensus Loop**  
   The execution engine manages an interactive pipeline between the **Builder Agent** and the **Critic Agent**. The Builder acts as a *DeFi Vulnerability Analyzer*, parsing the Solidity input to locate flaws (such as reentrancy, access control bypasses, and overflow issues) and generating raw technical analysis. The Critic acts as the *Lead Smart Contract Auditor*, evaluating the Builder's proposal on its own merits. If flaws remain, the Critic rejects the patch and feeds structured debug context back to the next iteration of the Builder.

2. **Compute Optimization Flow (`LoopGuard`)**  
   To prevent runaway token consumption and infinite loops, the Orchestrator routes all agent calls through the `LoopGuard` middleware. This layer runs a regex-based sequence analyzer to detect if identical parameters are invoked 3 times consecutively. Crucially, the system implements **short-circuit early termination**: if the Critic flags the contract as `"Secure"` or returns `"passed": true`, the loop terminates instantly at $O(1)$ efficiency, bypassing unnecessary subsequent iteration steps.

3. **Automated Exploit Simulator**  
   To prove vulnerability exploitability, the Critic Agent generates a fully functional Solidity attacker contract (`contract Attacker { ... }`) targetting the identified vulnerability. This simulator is dynamically triggered exclusively when the severity level is classified as **High** or **Critical**, providing auditors with immediate Proof-of-Concept (PoC) code to reproduce the issue.

4. **Visual Code Patching**  
   The client-side UI integrates an interactive line-level Diff Viewer utilizing `jsdiff`. When the Critic Agent outputs the final remediated contract in the `patched_code` field, the frontend compares it line-by-line with the original user input, rendering added lines (`+` green) and removed lines (`-` red) with syntax highlight styling.

5. **Report Exporter**  
   Upon audit completion, users can export a complete Markdown security report compile-generated directly from the client-side DOM state. The exporter compiles the audit status, severity, Critic feedback points, PoC exploit code, and final patched Solidity contract into a clean, download-ready Markdown file.

---

## Features

- **Multi-Agent Consensus Loop** — Builder analyzes vulnerabilities, Critic audits assertions, Orchestrator mediates until convergence
- **Cost-Efficient Convergence** — Hard-cap 3-iteration circuit breaker with penultimate-step warning injection
- **Real-Time SSE Streaming** — Live execution logs streamed to the browser via Server-Sent Events
- **Loop Protection Middleware** — Regex-based safety layer terminates on 3 identical consecutive tool calls
- **Dynamic Rate-Limit Backoff** — Automatic retry with exponential backoff on API rate limits
- **Structured Pointer Reports** — Critic feedback parsed into individual vulnerability findings
- **Web3 Landing Page** — Animated glassmorphic frontend with Inter typography and smooth-scroll navigation
- **PWA Support** — Installable Progressive Web App with offline-capable service worker

---

## Project Structure

```
├── src/
│   ├── api/
│   │   ├── ARCHITECTURE.md        # Agent boundary documentation
│   │   └── sub_agents.py          # Builder & Critic agent implementations
│   ├── middleware/
│   │   ├── CONSTRAINTS.md         # Loop protection rules
│   │   └── loop_guard.py          # Regex loop detection + iteration limiter
│   ├── orchestrator.py            # Central orchestration runner
│   ├── cli.py                     # CLI entry point
│   ├── server.py                  # FastAPI server + SSE streaming
│   └── static/
│       ├── index.html             # Web3 landing page + audit workspace
│       ├── app.js                 # SSE stream processor + UI logic
│       ├── sw.js                  # Service worker (PWA)
│       ├── manifest.json          # PWA manifest
│       └── icon.svg               # App icon
├── tests/
│   ├── test_cli.py                # CLI argument parsing tests
│   ├── test_loop_guard.py         # Loop detection + iteration limit tests
│   ├── test_orchestrator.py       # Orchestration flow tests
│   ├── test_server.py             # FastAPI endpoint + SSE tests
│   └── test_sub_agents.py         # Agent boundary enforcement tests
├── AGENTS.md                      # Agent configuration rules
├── PROGRESS.md                    # Development progress log
├── Makefile                       # Setup, lint, test commands
├── requirements.txt               # Python dependencies
└── .gitignore
```

---

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Google Gemini API Key** — Get one from [Google AI Studio](https://aistudio.google.com/apikey)

### Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Pranjal685/Web3-Smart-Contract-Security-Auditor.git
   cd Web3-Smart-Contract-Security-Auditor
   ```

2. **Initialize Virtual Environment & Install Dependencies:**
   ```bash
   python -m venv venv
   
   # Activate on Linux/macOS:
   source venv/bin/activate
   # Activate on Windows PowerShell:
   # .\venv\Scripts\Activate.ps1
   
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Copy the provided environment template to a secure local file (which is automatically blocked by `.gitignore`):
   ```bash
   cp .env.example .env
   ```
   Open the `.env` file and replace `your_api_key_here` with your actual Google Gemini API Key:
   ```env
   GEMINI_API_KEY="your-actual-api-key-value"
   ```

4. **Load the Environment Variables:**
   * **Linux/macOS:**
     ```bash
     export $(cat .env | xargs)
     ```
   * **Windows PowerShell:**
     ```powershell
     Get-Content .env | ForEach-Object {
         if ($_ -and $_ -notmatch '^#') {
             $parts = $_ -split '=', 2
             if ($parts.Length -eq 2) {
                 $key = $parts[0].Trim()
                 $val = $parts[1].Trim().Trim('"').Trim("'")
                 [System.Environment]::SetEnvironmentVariable($key, $val, "Process")
             }
         }
     }
     ```

### Run the Web Server

Launch the FastAPI backend with:
```bash
uvicorn src.server:app --reload --host 0.0.0.0 --port 8000
```
Open [http://localhost:8000](http://localhost:8000) in your web browser to access the dynamic auditing workspace.

### Run via CLI

```bash
python -m src.cli "pragma solidity ^0.8.20; contract Test { ... }" --verbose
```

---

## Testing

The project includes 20 tests covering all components:

```bash
# Set PYTHONPATH for module resolution
export PYTHONPATH="."    # or $env:PYTHONPATH="." on Windows

# Run all tests
python -m pytest -v

# Lint (py_compile)
python -m py_compile src/server.py src/orchestrator.py src/cli.py src/api/sub_agents.py src/middleware/loop_guard.py
```

### Test Coverage

| Suite | Tests | Covers |
|---|---|---|
| `test_cli.py` | 5 | CLI argument parsing, error handling |
| `test_loop_guard.py` | 6 | Loop detection, iteration limits, edge cases |
| `test_orchestrator.py` | 2 | Success flow, loop middleware trigger |
| `test_server.py` | 3 | SSE streaming, error propagation, static serving |
| `test_sub_agents.py` | 4 | Agent boundaries, API key validation |

---

## Critic Report Schema

The Critic Agent outputs a structured JSON verdict:

```json
{
  "passed": false,
  "severity": "High",
  "feedback": "Reentrancy vulnerability detected in withdraw(). The external call via msg.sender.call{value: amount}('') occurs before the state update balances[msg.sender] = 0. An attacker can recursively call withdraw() to drain the contract."
}
```

| Field | Type | Description |
|---|---|---|
| `passed` | `boolean` | Whether the contract passed the security audit |
| `severity` | `string` | One of: `Secure`, `Low`, `Medium`, `High`, `Critical` |
| `feedback` | `string` | Detailed vulnerability findings and remediation |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **AI Inference** | Google Gemini Flash (raw HTTP, zero SDK) |
| **Backend** | FastAPI + Uvicorn |
| **Streaming** | Server-Sent Events (SSE) |
| **Frontend** | Vanilla HTML/CSS/JS, Inter font, PWA |
| **Testing** | pytest |
| **Language** | Python 3.11+ |

---

## License

This project is provided as-is for educational and research purposes.
