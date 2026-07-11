import json
import re
from typing import List, Dict, Any

def detect_loop(tool_calls: List[Dict[str, Any]]) -> bool:
    """
    Detects if the exact same tool and parameters were called 3 times consecutively.
    
    Args:
        tool_calls: A list of dictionaries, where each dict has 'tool_name' and 'parameters'.
        
    Returns:
        bool: True if a loop is detected (3 identical consecutive calls), False otherwise.
    """
    if len(tool_calls) < 3:
        return False

    for i in range(len(tool_calls) - 2):
        call1 = tool_calls[i]
        call2 = tool_calls[i + 1]
        call3 = tool_calls[i + 2]
        
        # Compare tool names
        if call1.get("tool_name") == call2.get("tool_name") == call3.get("tool_name"):
            # Compare parameters (dict comparison is order-independent in Python)
            p1 = call1.get("parameters")
            p2 = call2.get("parameters")
            p3 = call3.get("parameters")
            if p1 == p2 == p3:
                return True
                
    return False

def detect_loop_regex(tool_calls: List[Dict[str, Any]]) -> bool:
    """
    Alternative regex-based implementation matching the description in CONSTRAINTS.md.
    
    Args:
        tool_calls: A list of dictionaries, where each dict has 'tool_name' and 'parameters'.
        
    Returns:
        bool: True if a loop is detected via regex pattern matching, False otherwise.
    """
    # Serialize each tool call into the format: tool:<tool_name>|params:<JSON_serialized_params>
    serialized = []
    for call in tool_calls:
        name = call.get("tool_name", "")
        # Sort keys to ensure stable string representation for regex match
        params = call.get("parameters", {})
        params_str = json.dumps(params, sort_keys=True)
        # Remove whitespace to match the \{.*?\} regex pattern without space issues
        params_str_compact = params_str.replace(" ", "")
        serialized.append(f"tool:{name}|params:{params_str_compact}")
        
    # Combine the serialized calls
    stream = ", ".join(serialized)
    
    # Regex matching 3 identical consecutive calls. We search for the pattern anywhere in the stream.
    # Pattern uses backreference (?P=call) to check for three identical matches of the group 'call'
    pattern = r"(?P<call>tool:[a-zA-Z0-9_-]+\|params:\{.*?\}),?\s*(?P=call),?\s*(?P=call)"
    
    match = re.search(pattern, stream)
    return match is not None

MAX_ITERATIONS = 3

class IterationLimitExceeded(Exception):
    def __init__(self, message: str, last_state: dict):
        super().__init__(message)
        self.last_state = last_state

