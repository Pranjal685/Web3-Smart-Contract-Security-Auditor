# Token-Guard // Web3 Smart Contract Security Auditor

**AI-powered multi-agent security auditing for Solidity smart contracts.**

Token-Guard is an agentic router that orchestrates Builder and Critic AI agents to reach consensus on your smart contract's vulnerabilities — in under 3 iterations, with zero human review overhead.

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)
![Gemini](https://img.shields.io/badge/Google%20Gemini-Flash-orange.svg)
![Tests](https://img.shields.io/badge/tests-20%20passed-brightgreen.svg)

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

### Installation

```bash
# Clone the repository
git clone https://github.com/Pranjal685/Web3-Smart-Contract-Security-Auditor.git
cd Web3-Smart-Contract-Security-Auditor

# Create virtual environment and install dependencies
python -m venv venv
source venv/bin/activate          # Linux/macOS
# venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

### Set API Key

```bash
export GEMINI_API_KEY="your-api-key-here"

# Windows PowerShell:
# $env:GEMINI_API_KEY="your-api-key-here"
```

### Run the Web Server

```bash
uvicorn src.server:app --reload --host 0.0.0.0 --port 8000
```

Then open [http://localhost:8000](http://localhost:8000) in your browser.

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
