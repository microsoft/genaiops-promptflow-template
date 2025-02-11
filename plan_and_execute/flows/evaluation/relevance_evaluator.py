"""Relevance evaluation node for the plan_and_execute evaluation flow."""
from promptflow.core import tool
from promptflow.core import AzureOpenAIModelConfiguration
from connection_utils import CustomConnection
from promptflow.evals.evaluators import RelevanceEvaluator


@tool
def relevance_evaluator_tool(
    connection: CustomConnection, question: str, answer: str, steps: str
) -> dict:
    """
    Evaluate the relevance of the answer to the question, given the steps.

    :param connection: The connection object.
    :param question: The question to evaluate.
    :param answer: The answer to evaluate.
    :param steps: The context to evaluate against.
    :return: A dictionary with 'gpt_relevance' indicating the relevance score.
    """
    model_config = AzureOpenAIModelConfiguration(
        azure_endpoint=connection.configs["aoai_base_url"],
        api_key=connection.secrets["aoai_api_key"],
        api_version=connection.configs["aoai_api_version"],
        azure_deployment=connection.configs["aoai_model_gpt4"],
    )

    relevance_evaluator = RelevanceEvaluator(model_config)

    return relevance_evaluator(question=question, answer=answer, context=steps)
