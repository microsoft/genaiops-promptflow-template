
# Implement your custom evaluation here
import os
from promptflow.core import AzureOpenAIModelConfiguration
from promptflow.evals.evaluate import evaluate
from promptflow.evals.evaluators import GroundednessEvaluator
from class_flows.flows.chat_basic.flow import ChatFlow


def eval_use_case(
        run_name,
        data_id,
        column_mapping,
        output_path,
        azure_service={},
):
    model_config = AzureOpenAIModelConfiguration(
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
        api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
        azure_deployment=os.environ.get("DEPLOYMENT_NAME"),
    )
    chat_flow = ChatFlow(model_config=model_config, max_total_token=4096)

    groundness_eval = GroundednessEvaluator(model_config=model_config)
    results = evaluate(
        evaluation_name=run_name,
        data=data_id,
        target=chat_flow,
        evaluators={
            "groundness_eval": groundness_eval,
        },
        evaluator_config={
            "groundness_eval": column_mapping,
        },
        azure_ai_project=azure_service,
        output_path=f"{output_path}/{run_name}.json",

    )

    return results
