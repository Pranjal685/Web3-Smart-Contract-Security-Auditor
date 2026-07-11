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
    # Critic repeatedly rejects it with the same feedback,
    # and Loop Guard terminates the loop after 3 identical consecutive calls.
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

    # The loop should raise RuntimeError due to Loop Guard trigger
    with pytest.raises(RuntimeError) as exc_info:
        orchestrator.run("Write secure code")

    assert "Loop Protection Middleware triggered" in str(exc_info.value)
    
    # Trace:
    # Call 1: "Write secure code"
    # Call 2: "Write secure code\n\nPrevious implementation failed. Feedback: Code is insecure."
    # Call 3: "Write secure code\n\nPrevious implementation failed. Feedback: Code is insecure."
    # Call 4: "Write secure code\n\nPrevious implementation failed. Feedback: Code is insecure." -> Triggered (consecutive calls 2, 3, 4 are identical)
    assert len(orchestrator.action_history) == 4
    
    history = orchestrator.action_history
    assert history[0]["parameters"]["task_description"] == "Write secure code"
    assert history[1]["parameters"]["task_description"] == "Write secure code\n\nPrevious implementation failed. Feedback: Code is insecure."
    assert history[2]["parameters"]["task_description"] == "Write secure code\n\nPrevious implementation failed. Feedback: Code is insecure."
    assert history[3]["parameters"]["task_description"] == "Write secure code\n\nPrevious implementation failed. Feedback: Code is insecure."
