import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from src.server import app

client = TestClient(app)

def test_audit_endpoint_success():
    """
    Test that the /api/audit endpoint successfully processes a mock request,
    captures and streams logs in real-time, and yields the final Critic JSON report.
    """
    with patch("src.server.Orchestrator") as mock_orchestrator_cls:
        mock_instance = MagicMock()
        
        def mock_run(contract, verbose):
            print("[INFO] Initiating security audit sequence.")
            print("[VERBOSE] Invoking Critic agent.")
            print("[WARN] Rate limiting detected, backing off.")
            return {
                "code": "/* Secure Contract */",
                "file_path": "analysis.txt",
                "iterations": 1,
                "critic_report": {
                    "passed": True,
                    "severity": "Secure",
                    "feedback": "No security issues identified.",
                    "patched_code": "// SPDX-License-Identifier: MIT\ncontract Test {}"
                }
            }
            
        mock_instance.run.side_effect = mock_run
        mock_orchestrator_cls.return_value = mock_instance
        
        response = client.post("/api/audit", json={"contract": "contract Test {}"})
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        lines = [line.strip() for line in response.text.split("\n\n") if line.strip()]
        
        assert len(lines) >= 4
        assert "Initiating security audit sequence." in lines[0]
        assert "Invoking Critic agent." in lines[1]
        assert "Rate limiting detected" in lines[2]
        
        report_line = lines[-1]
        assert "report" in report_line
        assert "Secure" in report_line
        assert "No security issues identified." in report_line

def test_audit_endpoint_error():
    """
    Test that the /api/audit endpoint handles errors raised by the orchestrator
    gracefully by streaming an error event.
    """
    with patch("src.server.Orchestrator") as mock_orchestrator_cls:
        mock_instance = MagicMock()
        mock_instance.run.side_effect = RuntimeError("Mock Loop Guard Triggered")
        mock_orchestrator_cls.return_value = mock_instance
        
        response = client.post("/api/audit", json={"contract": "contract Loop {}"})
        
        assert response.status_code == 200
        
        lines = [line.strip() for line in response.text.split("\n\n") if line.strip()]
        assert len(lines) >= 1
        
        error_line = lines[-1]
        assert "error" in error_line
        assert "Mock Loop Guard Triggered" in error_line

def test_root_route_serves_html():
    """
    Test that a GET request to the root URL (/) returns a 200 status code
    and serves HTML content from index.html.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "TOKEN-GUARD" in response.text

