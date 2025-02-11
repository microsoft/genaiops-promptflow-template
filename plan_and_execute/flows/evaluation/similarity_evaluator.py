"""Similarity evaluation node for the plan_and_execute evaluation flow."""
from promptflow.core import tool
from promptflow.core import AzureOpenAIModelConfiguration
from connection_utils import CustomConnection
from promptflow.evals.evaluators import SimilarityEvaluator


@tool
def similarity_evaluator_tool(
    connection: CustomConnection, question: str, answer: str, ground_truth: str
) -> dict:
    """
    Evaluate the similarity between answer and ground_truth.

    :param connection: The connection object.
    :param question: The question to evaluate.
    :param answer: The answer to evaluate.
    :param ground_truth: The ground truth answer to evaluate against.
    :return: A dictionary with 'gpt_similarity'
             indicating the similarity score.
    """
    model_config = AzureOpenAIModelConfiguration(
        azure_endpoint=connection.configs["aoai_base_url"],
        api_key=connection.secrets["aoai_api_key"],
        api_version=connection.configs["aoai_api_version"],
        azure_deployment=connection.configs["aoai_model_gpt4"],
    )

    similarity_evaluator = SimilarityEvaluator(model_config)

    return similarity_evaluator(
        question=question, answer=answer, ground_truth=ground_truth
    )
