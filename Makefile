.PHONY: setup test lint check

setup:
	python -m venv venv
	venv/bin/pip install -r requirements.txt

test:
	venv/bin/python -m pytest

lint:
	venv/bin/python -m py_compile src/middleware/loop_guard.py tests/test_loop_guard.py src/api/sub_agents.py tests/test_sub_agents.py src/orchestrator.py tests/test_orchestrator.py src/cli.py tests/test_cli.py

check: lint test



