"""Planner node for the plan_and_execute flow."""
from promptflow.core import tool
from autogen import AssistantAgent
from connection_utils import CustomConnection
from tools import register_tools


@tool
def planner_tool(
    connection: CustomConnection, system_message: str, question: str
) -> str:
    """Generate a step-by-step execution plan to solve the user's request."""
    config_list_gpt4 = [
        {
            "model": connection.configs["aoai_model_gpt4"],
            "api_key": connection.secrets["aoai_api_key"],
            "base_url": connection.configs["aoai_base_url"],
            "api_type": "azure",
            "api_version": connection.configs["aoai_api_version"],
        }
    ]

    planner = AssistantAgent(
        name="PLANNER",
        description="""
        An agent expert in creating a step-by-step execution plan
        to solve the user's request.
        """,
        system_message=system_message,
        code_execution_config=False,
        llm_config={
            "config_list": config_list_gpt4,
            "temperature": 0,
            "timeout": 120,
            "cache_seed": None,
        },
    )

    register_tools(planner)

    planner_reply = planner.generate_reply(
        messages=[{"content": question, "role": "user"}]
    )
    planner_reply = planner_reply.replace(
        "```json", "").replace("```", "").strip()

    return planner_reply
