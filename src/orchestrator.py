from typing import Dict, Any, List
from src.api.sub_agents import Builder, Critic
from src.middleware.loop_guard import detect_loop

class Orchestrator:
    """
    Orchestrator coordinates the execution loop by delegating code generation to the Builder
    and code evaluation to the Critic, while monitoring for infinite loops via the Loop Guard.
    """
    def __init__(self, builder: Builder, critic: Critic):
        self.builder = builder
        self.critic = critic
        self.action_history: List[Dict[str, Any]] = []

    def run(self, initial_task: str, verbose: bool = False) -> Dict[str, Any]:
        """
        Executes the Orchestrator loop.
        
        Args:
            initial_task: The initial user prompt or coding task.
            verbose: Enable verbose logging to stdout.
            
        Returns:
            Dict containing the final approved code and execution metadata.
            
        Raises:
            RuntimeError: If a loop is detected by the Loop Protection Middleware.
        """
        current_task_description = initial_task
        
        while True:
            # 1. Log the action with current parameters
            action_log = {
                "tool_name": "generate_code",
                "parameters": {
                    "task_description": current_task_description
                }
            }
            self.action_history.append(action_log)
            
            if verbose:
                print(f"[VERBOSE] Orchestrator invoking Builder with parameters: {action_log['parameters']}")
            
            # 2. Check with the Loop Protection Middleware
            if detect_loop(self.action_history):
                if verbose:
                    print(f"[VERBOSE] Loop Guard triggered. History: {self.action_history}")
                raise RuntimeError(
                    "Loop Protection Middleware triggered: Identical tool call parameters invoked 3 times consecutively."
                )
            
            # 3. Invoke the Builder to get the code payload
            builder_payload = self.builder.generate_code(current_task_description)
            code = builder_payload.get("code", "")
            
            # 4. Invoke the Critic to evaluate the code
            critic_payload = self.critic.evaluate_code(code, context=initial_task)
            passed = critic_payload.get("passed", False)
            feedback = critic_payload.get("feedback", "")
            
            # 5. If Critic approves, return final code
            if passed:
                if verbose:
                    print(f"[VERBOSE] Critic approved code after {len(self.action_history)} iteration(s).")
                return {
                    "code": code,
                    "file_path": builder_payload.get("file_path", "solution.py"),
                    "iterations": len(self.action_history),
                    "critic_report": critic_payload
                }
            
            if verbose:
                print(f"[VERBOSE] Critic rejected code on iteration {len(self.action_history)}. Feedback: {feedback}")
            
            # 6. If Critic rejects, update task description with the latest feedback
            # Using replacement rather than cumulative appending ensures that if the feedback
            # remains the same, the parameters will be identical, triggering loop protection.
            current_task_description = (
                f"{initial_task}\n\n"
                f"Previous implementation failed. Feedback: {feedback}"
            )
