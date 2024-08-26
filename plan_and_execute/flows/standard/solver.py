"""Solver node for the plan_and_execute flow."""
from promptflow.core import tool
from autogen import AssistantAgent
from connection_utils import CustomConnection


@tool
def solver_tool(
    connection: CustomConnection, system_message: str,
    question: str, results: str
) -> str:
    """Create a final response to the user's request."""
    config_list_gpt4 = [
        {
            "model": connection.configs["aoai_model_gpt4"],
            "api_key": connection.secrets["aoai_api_key"],
            "base_url": connection.configs["aoai_base_url"],
            "api_type": "azure",
            "api_version": connection.configs["aoai_api_version"],
        }
    ]

    solver = AssistantAgent(
        name="SOLVER",
        description="""
        An agent expert in creating a final response to the user's request.
        """,
        system_message=system_message,
        code_execution_config=False,
        llm_config={"config_list": config_list_gpt4,
                    "timeout": 60, "cache_seed": None},
    )

    solver_message = f"""
    Question:
    {question}

    Step results:
    {results}
    """

    return solver.generate_reply(
        messages=[{"content": solver_message, "role": "user"}]
    )
