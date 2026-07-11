from typing import Dict, Any, List
from src.api.sub_agents import Builder, Critic
from src.middleware.loop_guard import detect_loop, IterationLimitExceeded, MAX_ITERATIONS

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
            IterationLimitExceeded: If the maximum iteration limit is reached.
        """
        # Cost-Efficiency Clause
        clause = (
            "INSTRUCTION: You are an expert smart contract auditor. You must solve the vulnerability in 3 iterations or fewer. "
            "If you cannot solve it, explain clearly why. Do not iterate for the sake of iterating. "
            "Your primary goal is high-accuracy security analysis, but your secondary goal is token efficiency."
        )
        modified_initial_task = f"{clause}\n\n{initial_task}"
        current_task_description = modified_initial_task
        last_state: Dict[str, Any] = {}

        try:
            while True:
                iteration_count = len(self.action_history) + 1
                
                # Penultimate step warning (iteration count is 2)
                if iteration_count == 2:
                    builder_task = (
                        f"{current_task_description}\n\n"
                        f"[FINAL EFFORT] This is your penultimate attempt. Prioritize all remaining fixes "
                        f"in a single pass to ensure completion before the hard limit is hit."
                    )
                else:
                    builder_task = current_task_description

                # 1. Log the action with current parameters
                action_log = {
                    "tool_name": "generate_code",
                    "parameters": {
                        "task_description": builder_task
                    }
                }
                self.action_history.append(action_log)
                
                # Check Iteration Limit
                if len(self.action_history) > MAX_ITERATIONS:
                    raise IterationLimitExceeded(
                        f"Iteration limit reached: {MAX_ITERATIONS}",
                        last_state=last_state
                    )

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
                builder_payload = self.builder.generate_code(builder_task)
                code = builder_payload.get("code", "")
                
                # 4. Invoke the Critic to evaluate the code
                critic_payload = self.critic.evaluate_code(code, context=modified_initial_task)
                passed = critic_payload.get("passed", False)
                feedback = critic_payload.get("feedback", "")
                
                # Save the current state as the last known best version
                last_state = {
                    "code": code,
                    "file_path": builder_payload.get("file_path", "solution.py"),
                    "iterations": len(self.action_history),
                    "critic_report": critic_payload
                }

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
                current_task_description = (
                    f"{modified_initial_task}\n\n"
                    f"Previous implementation failed. Feedback: {feedback}"
                )
        except IterationLimitExceeded as e:
            if verbose:
                print(f"[VERBOSE] Iteration limit exceeded. Serving last-known best version.")
            result = e.last_state
            result["status"] = "PARTIAL_AUDIT_COMPLETE"
            if "critic_report" in result:
                result["critic_report"]["status"] = "PARTIAL_AUDIT_COMPLETE"
            return result

