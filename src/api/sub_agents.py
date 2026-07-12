import os
import json
import re
import ssl
import time
import urllib.request
import urllib.error
from typing import Dict, Any

_MAX_RETRIES = 4
_RETRY_DELAY_SECONDS = 2
_RETRYABLE_HTTP_CODES = {429, 503}
_HTTP_BACKOFF = {
    1: 5,
    2: 15,
    3: 30
}

def _call_gemini(prompt: str) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is missing.")
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }
    
    data = json.dumps(payload).encode("utf-8")
    
    try:
        ssl_context = ssl._create_unverified_context()
    except AttributeError:
        ssl_context = None
 
    last_error = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            # Rebuild request each attempt since urlopen consumes the data buffer
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, context=ssl_context, timeout=60) as response:
                res_data = response.read().decode("utf-8")
                res_json = json.loads(res_data)
                text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                return text
        except urllib.error.HTTPError as e:
            last_error = e
            if e.code in _RETRYABLE_HTTP_CODES and attempt < _MAX_RETRIES:
                sleep_seconds = _HTTP_BACKOFF.get(attempt, 5)
                print(f"[WARN] API returned HTTP {e.code}, retrying in {sleep_seconds}s... (attempt {attempt}/{_MAX_RETRIES})")
                print(f"[INFO] Waiting for rate limit window to clear...")
                time.sleep(sleep_seconds)
                continue
            raise RuntimeError(f"Gemini API error after {attempt} attempt(s): HTTP {e.code} - {e.reason}")
        except TimeoutError:
            last_error = TimeoutError("The read operation timed out")
            if attempt < _MAX_RETRIES:
                print(f"[WARN] API request timed out, retrying in {_RETRY_DELAY_SECONDS}s... (attempt {attempt}/{_MAX_RETRIES})")
                time.sleep(_RETRY_DELAY_SECONDS)
                continue
            raise RuntimeError(f"Gemini API timed out after {attempt} attempt(s).")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Gemini API connection error: {e}")
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Failed to parse Gemini API response structure: {e}")
 
    # Unreachable: all loop iterations either return or raise, but this satisfies static analysis.
    raise RuntimeError(f"Gemini API failed after {_MAX_RETRIES} attempt(s).")

class Builder:
    """
    Builder Agent acting as a DeFi Vulnerability Analyzer.
    Uses Google Gemini API (gemini-flash-latest) for inference.
    MUST NOT contain any self-evaluation or execution logic.
    """
    def __init__(self):
        pass

    def generate_code(self, task_description: str) -> Dict[str, Any]:
        """
        Generates a raw technical analysis identifying potential attack vectors in the given Solidity code.
        """
        prompt = (
            f"You are a DeFi Vulnerability Analyzer. Ingest the following Solidity code and output a raw technical analysis identifying potential attack vectors (e.g., Reentrancy, Integer Overflow, Access Control flaws):\n"
            f"{task_description}\n\n"
            f"Provide a detailed raw technical analysis. You must NOT output JSON."
        )
        
        response_text = _call_gemini(prompt)
        
        return {
            "code": response_text.strip(),
            "file_path": "analysis.txt"
        }

class Critic:
    """
    Critic Agent acting as a Lead Smart Contract Auditor.
    Uses Google Gemini API (gemini-flash-latest) for inference.
    MUST NOT generate any feature or application code.
    """
    def __init__(self):
        pass

    def evaluate_code(self, code: str, context: str = "") -> Dict[str, Any]:
        """
        Evaluates the Analyzer's findings and the original Solidity code.
        Returns a dict with passed, severity, feedback, and patched_code fields.
        """
        prompt = (
            f"You are a Lead Smart Contract Auditor. Review the DeFi Vulnerability Analyzer's findings and the original Solidity code.\n"
            f"Original Solidity Code (Context): {context}\n"
            f"Analyzer's Findings: {code}\n\n"
            f"You MUST return a JSON object with exactly the following structure:\n"
            f"{{\n"
            f"  \"passed\": true or false,\n"
            f"  \"severity\": \"Critical\", \"High\", \"Medium\", \"Low\", or \"Secure\",\n"
            f"  \"feedback\": \"Detailed explanation of the vulnerability and how to patch it\",\n"
            f"  \"patched_code\": \"The complete, fully remediated Solidity contract with all vulnerabilities fixed. Reproduce the entire contract source code with corrections applied.\"\n"
            f"}}\n"
            f"The patched_code field is REQUIRED. It must contain the complete remediated Solidity source code.\n"
            f"Do not write any other text outside this JSON."
        )
        
        response_text = _call_gemini(prompt)
        
        # Clean any markdown code blocks (e.g., ```json or ```) before parsing
        clean_text = response_text.strip()
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", clean_text, re.DOTALL)
        if match:
            clean_text = match.group(1).strip()
            
        try:
            eval_data = json.loads(clean_text)
            passed = bool(eval_data.get("passed", False))
            severity = str(eval_data.get("severity", "Secure"))
            feedback = str(eval_data.get("feedback", "No feedback provided."))
            patched_code = str(eval_data.get("patched_code", ""))
        except json.JSONDecodeError:
            passed = False
            severity = "Critical"
            feedback = f"Failed to parse JSON evaluation from Gemini. Raw response: {response_text}"
            patched_code = ""
            
        return {
            "passed": passed,
            "severity": severity,
            "feedback": feedback,
            "patched_code": patched_code
        }
