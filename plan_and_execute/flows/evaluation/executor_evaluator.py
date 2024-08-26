"""Executor evaluation node for the plan_and_execute evaluation flow."""
from promptflow.core import tool
import re


@tool
def executor_evaluator_tool(plan_steps_count: str, steps: str) -> str:
    """
    Validate whether the generated number of steps is equal to the expected
    number of steps according to the execution plan.

    :param plan_steps_count: The number of plan steps expected in the result.
    :param steps: The generated steps to validate.
    :return: The list 'missing_steps' listing any missing step IDs.
    """
    step_pattern = re.compile(r"#E(\d+)\s*=\s*.*?(?=#E\d+\s*=|$)", re.DOTALL)
    found_steps = step_pattern.findall(steps)

    # Convert found steps to a set of integers
    found_steps = set(map(int, found_steps))

    # Expected steps based on plan_steps_count
    expected_steps = set(range(1, int(plan_steps_count) + 1))

    # Determine missing steps
    missing_steps = expected_steps - found_steps

    return {"missing_steps": list(missing_steps)}
