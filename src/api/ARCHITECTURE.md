# API Architecture - Agent Boundaries

This document defines the strict operational boundaries between the main components of the Token-Guard Agentic Router to enforce separation of concerns and prevent monolithic/generative coding hazards.

## 1. Orchestrator
- **Role**: Coordinates the entire execution lifecycle.
- **Responsibilities**:
  - Receives input and schedules execution tasks.
  - Delegates development/implementation tasks to the **Builder Agent**.
  - Submits code written by the Builder to the **Critic Agent** for evaluation.
  - Controls flow redirection and overall decision-making.
- **Boundary**: Never writes application code directly, and never performs validation evaluation.

## 2. Builder Agent
- **Role**: Code Generator.
- **Responsibilities**:
  - Implements functionality and writes raw code files.
  - Works strictly based on instructions provided by the Orchestrator.
- **Boundary**: **NEVER** runs, tests, or evaluates its own work. Once code is written, control must be returned immediately.

## 3. Critic Agent
- **Role**: Quality & Security Assurer.
- **Responsibilities**:
  - Audits the Builder's code for security vulnerabilities, logic bugs, and compliance.
  - Approves code or reports issues back to the Orchestrator for refactoring.
- **Boundary**: **NEVER** writes feature or application code. It only outputs review results, feedback, or validation status.

## 4. LLM Inference Engine
Both the Builder Agent and the Critic Agent rely on the **Google Gemini API** for inference:
- **Model**: `gemini-flash-latest` (resolving to the latest Flash model)
- **Authentication**: Authenticated via the `GEMINI_API_KEY` environment variable.
- **Endpoint**: `https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={API_KEY}`
- **Mechanism**: Sub-agents communicate using raw HTTP requests via Python's built-in `urllib.request` and `json` modules (zero external dependencies).


