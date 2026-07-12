import asyncio
import contextvars
import io
import json
import sys
from typing import AsyncGenerator, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from src.api.sub_agents import Builder, Critic
from src.orchestrator import Orchestrator

log_queue_var: contextvars.ContextVar[Optional["ContextVarStdoutReceiver"]] = contextvars.ContextVar("log_queue", default=None)

class ContextVarStdoutReceiver:
    def __init__(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        self.queue = queue
        self.loop = loop
        self.buffer = ""

    def write(self, s: str):
        self.buffer += s
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            self.loop.call_soon_threadsafe(self.queue.put_nowait, line)

    def flush(self):
        pass

class ContextVarStdout(io.TextIOBase):
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout

    def write(self, s: str):
        self.original_stdout.write(s)
        receiver = log_queue_var.get()
        if receiver is not None:
            receiver.write(s)
        return len(s)

    def flush(self):
        self.original_stdout.flush()

def ensure_stdout_wrapped():
    if not isinstance(sys.stdout, ContextVarStdout):
        sys.stdout = ContextVarStdout(sys.stdout)

ensure_stdout_wrapped()

app = FastAPI(title="Token-Guard Smart Contract Security Auditor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AuditRequest(BaseModel):
    contract: str

async def audit_stream(contract: str) -> AsyncGenerator[str, None]:
    ensure_stdout_wrapped()
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    receiver = ContextVarStdoutReceiver(queue, loop)
    token = log_queue_var.set(receiver)
    
    builder = Builder()
    critic = Critic()
    orchestrator = Orchestrator(builder=builder, critic=critic)

    async def run_orchestrator():
        try:
            res = await asyncio.to_thread(orchestrator.run, contract, True)
            return res
        except Exception as e:
            return e
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)

    task = asyncio.create_task(run_orchestrator())

    try:
        while True:
            line = await queue.get()
            if line is None:
                break
            if any(line.startswith(prefix) for prefix in ("[INFO]", "[VERBOSE]", "[WARN]")):
                yield f"data: {json.dumps({'type': 'log', 'message': line})}\n\n"

        result = await task
        if isinstance(result, Exception):
            yield f"data: {json.dumps({'type': 'error', 'message': str(result)})}\n\n"
        else:
            report_payload = result.get('critic_report', {})
            report_payload['patched_code'] = report_payload.get('patched_code', '')
            yield f"data: {json.dumps({'type': 'report', 'data': report_payload})}\n\n"
    finally:
        log_queue_var.reset(token)

@app.post("/api/audit")
async def audit(request: AuditRequest):
    return StreamingResponse(audit_stream(request.contract), media_type="text/event-stream")

app.mount("/", StaticFiles(directory="src/static", html=True), name="static")
