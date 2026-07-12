import pytest
import json
import os
from unittest.mock import patch, MagicMock
from src.api.sub_agents import Builder, Critic

# Set the environment variable for testing
os.environ["GEMINI_API_KEY"] = "mock_gemini_key"

def _make_mock_gemini_response(text: str) -> bytes:
    """Helper to generate a mock Gemini API JSON response payload."""
    response_structure = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": text
                        }
                    ]
                }
            }
        ]
    }
    return json.dumps(response_structure).encode("utf-8")

def test_builder_only_returns_code_payload():
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = _make_mock_gemini_response("Reentrancy vulnerability detected in withdraw function.")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        builder = Builder()
        payload = builder.generate_code("pragma solidity ^0.8.0; contract Test { ... }")

        # Verify Builder strictly filters out anything that isn't code or file_path
        assert list(payload.keys()) == ["code", "file_path"]
        assert payload["code"] == "Reentrancy vulnerability detected in withdraw function."
        assert payload["file_path"] == "analysis.txt"

def test_critic_only_returns_evaluation_payload_passing():
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        model_output_json = json.dumps({
            "passed": True,
            "severity": "Secure",
            "feedback": "No vulnerabilities found.",
            "patched_code": "",
            "poc_exploit": None
        })
        # Mocking markdown JSON block
        mock_response.read.return_value = _make_mock_gemini_response(f"```json\n{model_output_json}\n```")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        critic = Critic()
        payload = critic.evaluate_code("Reentrancy vulnerability detected...", context="Test context")

        # Verify Critic returns evaluation payload with patched_code and poc_exploit fields
        assert list(payload.keys()) == ["passed", "severity", "feedback", "patched_code", "poc_exploit"]
        assert payload["passed"] is True
        assert payload["severity"] == "Secure"
        assert payload["feedback"] == "No vulnerabilities found."
        assert payload["patched_code"] == ""
        assert payload["poc_exploit"] == ""

def test_critic_only_returns_evaluation_payload_failing():
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        model_output_json = json.dumps({
            "passed": False,
            "severity": "High",
            "feedback": "Contract contains a reentrancy hazard.",
            "patched_code": "",
            "poc_exploit": "contract Attacker { function attack() external { /* exploit */ } }"
        })
        mock_response.read.return_value = _make_mock_gemini_response(model_output_json)
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        critic = Critic()
        payload = critic.evaluate_code("Reentrancy vulnerability detected...", context="Test context")

        assert list(payload.keys()) == ["passed", "severity", "feedback", "patched_code", "poc_exploit"]
        assert payload["passed"] is False
        assert payload["severity"] == "High"
        assert payload["feedback"] == "Contract contains a reentrancy hazard."
        assert payload["patched_code"] == ""
        assert "Attacker" in payload["poc_exploit"]

def test_missing_api_key_raises_value_error():
    # Temporarily remove key to test validation
    with patch.dict(os.environ, {}, clear=True):
        builder = Builder()
        with pytest.raises(ValueError) as exc_info:
            builder.generate_code("task")
        assert "GEMINI_API_KEY environment variable is missing" in str(exc_info.value)
