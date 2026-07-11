import pytest
import sys
from unittest.mock import patch, MagicMock
from src.cli import main

def test_cli_success_parses_task_and_calls_orchestrator():
    # Mock the Orchestrator run method
    with patch("src.cli.Orchestrator") as mock_orchestrator_cls:
        mock_orch_instance = MagicMock()
        mock_orch_instance.run.return_value = {
            "code": "print('hello')",
            "file_path": "hello.py",
            "iterations": 1
        }
        mock_orchestrator_cls.return_value = mock_orch_instance
        
        # Call the CLI main with args
        exit_code = main(["Write a script"])
        
        # Verify exit code is 0
        assert exit_code == 0
        
        # Verify Orchestrator was instantiated and run called with correct task
        mock_orchestrator_cls.assert_called_once()
        mock_orch_instance.run.assert_called_once_with("Write a script", verbose=False)

def test_cli_verbose_flag_passed():
    with patch("src.cli.Orchestrator") as mock_orchestrator_cls:
        mock_orch_instance = MagicMock()
        mock_orch_instance.run.return_value = {
            "code": "print('hello')",
            "file_path": "hello.py",
            "iterations": 1
        }
        mock_orchestrator_cls.return_value = mock_orch_instance
        
        exit_code = main(["Write a script", "--verbose"])
        
        assert exit_code == 0
        mock_orch_instance.run.assert_called_once_with("Write a script", verbose=True)

def test_cli_missing_arguments_raises_system_exit():
    # If a positional argument is missing, argparse calls sys.exit
    # with an error message and code 2.
    with pytest.raises(SystemExit) as exc_info:
        main([])
        
    assert exc_info.value.code == 2

def test_cli_orchestrator_error_returns_failure_exit_code():
    with patch("src.cli.Orchestrator") as mock_orchestrator_cls:
        mock_orch_instance = MagicMock()
        mock_orch_instance.run.side_effect = RuntimeError("Loop detected")
        mock_orchestrator_cls.return_value = mock_orch_instance
        
        exit_code = main(["Write a script"])
        
        assert exit_code == 1

def test_cli_missing_api_key_returns_failure_exit_code():
    with patch("src.cli.Orchestrator") as mock_orchestrator_cls:
        mock_orch_instance = MagicMock()
        mock_orch_instance.run.side_effect = ValueError("GEMINI_API_KEY environment variable is missing.")
        mock_orchestrator_cls.return_value = mock_orch_instance
        
        exit_code = main(["Write a script"])
        
        assert exit_code == 1

