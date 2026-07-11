# Token-Guard Agentic Router - Project Rules & Guidelines

## Project Overview
The "Token-Guard" Agentic Router utilizes a strict separation of concerns to avoid monolithic generative coding hazards:
- **Orchestrator**: The central runner that coordinates work and delegates specific tasks.
- **Builder Agent**: Writes raw feature/application code based strictly on local instructions. It must NEVER evaluate or execute its own work.
- **Critic Agent**: Reviews and evaluates the Builder's code for potential vulnerabilities. It must NEVER write any feature or application code.
- **Loop Protection Middleware**: A regex-based safety layer that intercepts tool execution and terminates the session if a tool is called with identical parameters 3 times consecutively.

## Environment Requirements
- **Python**: 3.11+ (necessary for advanced AI orchestration tooling)

## Verification Commands
Ensure code and environment correctness using the following:
- Setup Environment: `make setup`
- Lint Code: `make lint`
- Run Tests: `make test`
- Full Check (Lint + Test): `make check`

## Strict Design Boundaries
- For Builder/Critic boundaries, read [ARCHITECTURE.md](file:///c:/Users/Pranjal/OneDrive/Desktop/Harness%20ToDo/src/api/ARCHITECTURE.md).
- For Loop Protection rules, read [CONSTRAINTS.md](file:///c:/Users/Pranjal/OneDrive/Desktop/Harness%20ToDo/src/middleware/CONSTRAINTS.md).

## Global Invariant
> [!IMPORTANT]
> You MUST update [PROGRESS.md](file:///c:/Users/Pranjal/OneDrive/Desktop/Harness%20ToDo/PROGRESS.md) before terminating any session.
