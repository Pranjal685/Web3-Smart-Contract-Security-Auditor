import sys
import os
import argparse

# Ensure the project root is on sys.path so 'src' imports work
# regardless of whether the script is run directly or via python -m
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.api.sub_agents import Builder, Critic
from src.orchestrator import Orchestrator

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Token-Guard Agentic Router CLI - Orchestrator Execution Wrapper"
    )
    parser.add_argument(
        "task",
        type=str,
        help="The prompt or coding task for the agentic router"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print Critic's intermediate rejections and Loop Guard logs"
    )

    args = parser.parse_args(argv)

    # Initialize sub-agents and orchestrator
    builder = Builder()
    critic = Critic()
    orchestrator = Orchestrator(builder=builder, critic=critic)

    if args.verbose:
        print(f"[INFO] Starting Orchestrator with task: {args.task}")

    try:
        result = orchestrator.run(args.task, verbose=args.verbose)
        print("Success! Final code generated:")
        print(result["code"])
        return 0
    except ValueError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
