import pytest
from src.middleware.loop_guard import detect_loop, detect_loop_regex

def test_three_identical_consecutive_calls():
    calls = [
        {"tool_name": "list_dir", "parameters": {"DirectoryPath": "/workspace"}},
        {"tool_name": "list_dir", "parameters": {"DirectoryPath": "/workspace"}},
        {"tool_name": "list_dir", "parameters": {"DirectoryPath": "/workspace"}},
    ]
    assert detect_loop(calls) is True
    assert detect_loop_regex(calls) is True

def test_two_identical_consecutive_calls():
    calls = [
        {"tool_name": "list_dir", "parameters": {"DirectoryPath": "/workspace"}},
        {"tool_name": "list_dir", "parameters": {"DirectoryPath": "/workspace"}},
        {"tool_name": "list_dir", "parameters": {"DirectoryPath": "/other"}},
    ]
    assert detect_loop(calls) is False
    assert detect_loop_regex(calls) is False

def test_three_different_calls():
    calls = [
        {"tool_name": "list_dir", "parameters": {"DirectoryPath": "/workspace"}},
        {"tool_name": "grep_search", "parameters": {"Query": "loop"}},
        {"tool_name": "view_file", "parameters": {"AbsolutePath": "/workspace/file.py"}},
    ]
    assert detect_loop(calls) is False
    assert detect_loop_regex(calls) is False

def test_loop_nested_in_larger_history():
    calls = [
        {"tool_name": "list_dir", "parameters": {"DirectoryPath": "/workspace"}},
        {"tool_name": "grep_search", "parameters": {"Query": "loop"}},
        {"tool_name": "grep_search", "parameters": {"Query": "loop"}},
        {"tool_name": "grep_search", "parameters": {"Query": "loop"}},
        {"tool_name": "view_file", "parameters": {"AbsolutePath": "/workspace/file.py"}},
    ]
    assert detect_loop(calls) is True
    assert detect_loop_regex(calls) is True

def test_empty_or_small_history():
    assert detect_loop([]) is False
    assert detect_loop_regex([]) is False
    assert detect_loop([{"tool_name": "list_dir", "parameters": {}}]) is False
    assert detect_loop_regex([{"tool_name": "list_dir", "parameters": {}}]) is False

def test_strict_3_iteration_limit():
    """
    Assert that the system terminates at 3 iterations with a "PARTIAL_AUDIT_COMPLETE" status.
    """
    from unittest.mock import MagicMock
    from src.orchestrator import Orchestrator
    from src.api.sub_agents import Builder, Critic

    mock_builder = MagicMock(spec=Builder)
    mock_builder.generate_code.side_effect = [
        {"code": "contract V1 {}", "file_path": "Audit.sol"},
        {"code": "contract V2 {}", "file_path": "Audit.sol"},
        {"code": "contract V3 {}", "file_path": "Audit.sol"},
        {"code": "contract V4 {}", "file_path": "Audit.sol"},
    ]

    mock_critic = MagicMock(spec=Critic)
    mock_critic.evaluate_code.return_value = {
        "passed": False,
        "feedback": "Needs security hardening"
    }

    orchestrator = Orchestrator(builder=mock_builder, critic=mock_critic)
    result = orchestrator.run("Audit contract")

    assert result["status"] == "PARTIAL_AUDIT_COMPLETE"
    assert result["iterations"] == 3
    assert result["critic_report"]["status"] == "PARTIAL_AUDIT_COMPLETE"
    assert mock_builder.generate_code.call_count == 3

