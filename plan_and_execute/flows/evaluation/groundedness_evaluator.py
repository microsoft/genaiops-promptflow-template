"""Groundedness evaluation node for the plan_and_execute evaluation flow."""
from promptflow.core import tool
from promptflow.core import AzureOpenAIModelConfiguration
from connection_utils import CustomConnection
from promptflow.evals.evaluators import GroundednessEvaluator


@tool
def groundedness_evaluator_tool(
    connection: CustomConnection, steps: str, answer: str
) -> dict:
    """
    Evaluate the groundedness between answer and steps.

    :param connection: The connection object.
    :param steps: The context to ground the answer to.
    :param answer: The answer to evaluate against the context.
    :return: A dictionary with 'gpt_groundedness'
             indicating the grounding score.
    """
    model_config = AzureOpenAIModelConfiguration(
        azure_endpoint=connection.configs["aoai_base_url"],
        api_key=connection.secrets["aoai_api_key"],
        api_version=connection.configs["aoai_api_version"],
        azure_deployment=connection.configs["aoai_model_gpt4"],
    )

    groundedness_evaluator = GroundednessEvaluator(model_config)

    return groundedness_evaluator(answer=answer, context=steps)
