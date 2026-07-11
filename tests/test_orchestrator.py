import pytest
from unittest.mock import MagicMock
from src.api.sub_agents import Builder, Critic
from src.orchestrator import Orchestrator

def test_scenario_a_success_on_first_try():
    # Scenario A: Builder generates code, Critic approves immediately.
    mock_builder = MagicMock(spec=Builder)
    mock_builder.generate_code.return_value = {
        "code": "print('hello')",
        "file_path": "hello.py"
    }

    mock_critic = MagicMock(spec=Critic)
    mock_critic.evaluate_code.return_value = {
        "passed": True,
        "feedback": "LGTM"
    }

    orchestrator = Orchestrator(builder=mock_builder, critic=mock_critic)
    result = orchestrator.run("Write a print hello statement")

    assert result["code"] == "print('hello')"
    assert result["file_path"] == "hello.py"
    assert result["iterations"] == 1
    assert len(orchestrator.action_history) == 1

def test_scenario_b_loop_middleware_trigger():
    # Scenario B: Builder gets stuck generating the exact same payload,
    # Critic repeatedly rejects it with the same feedback.
    # Under the strict convergence policy, it terminates at 3 iterations
    # with status PARTIAL_AUDIT_COMPLETE.
    mock_builder = MagicMock(spec=Builder)
    mock_builder.generate_code.return_value = {
        "code": "print('bad code')",
        "file_path": "bad.py"
    }

    mock_critic = MagicMock(spec=Critic)
    mock_critic.evaluate_code.return_value = {
        "passed": False,
        "feedback": "Code is insecure."
    }

    orchestrator = Orchestrator(builder=mock_builder, critic=mock_critic)

    result = orchestrator.run("Write secure code")

    assert result["status"] == "PARTIAL_AUDIT_COMPLETE"
    assert result["iterations"] == 3
    assert result["critic_report"]["status"] == "PARTIAL_AUDIT_COMPLETE"
    assert len(orchestrator.action_history) == 4
    
    history = orchestrator.action_history
    assert "Write secure code" in history[0]["parameters"]["task_description"]
    assert "Write secure code" in history[1]["parameters"]["task_description"]
    assert "Write secure code" in history[2]["parameters"]["task_description"]
    assert "Write secure code" in history[3]["parameters"]["task_description"]

