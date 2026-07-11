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
