import json
import os
import subprocess
import yaml
from dotenv import load_dotenv
from azure.ai.ml import MLClient, Input, Output, load_component
from azure.ai.ml.constants import AssetTypes
from azure.ai.ml.dsl import pipeline
from azure.identity import DefaultAzureCredential

AML_DATASTORE_PATH_PREFIX = "azureml://datastores/mydatastore/paths/"
AML_DATASTORE_PREPROCESS_FILE_NAME = "data.jsonl"
AML_DATASTORE_PROMPTFLOW_FILE_NAME = "pf_output.jsonl"
AML_DATASTORE_POSTPROCESS_FILE_NAME = "postprocess.jsonl"


pipeline_components = []
def create_dynamic_evaluation_pipeline(
        pipeline_name,
    ):
    """
        Construct evaluation pipeline definition dynamically for a specific app and evaluator.

        Args:
            pipeline_name (str): Name of the pipeline.
    """
    @pipeline(
        name=pipeline_name,
    )
    def evaluation_pipeline(name: str):

        pf_input_path = Input(path=(AML_DATASTORE_PATH_PREFIX + AML_DATASTORE_PREPROCESS_FILE_NAME), type=AssetTypes.URI_FILE)
        preprocess = pipeline_components[0](
            )
        preprocess_output_path = Output(path=AML_DATASTORE_PATH_PREFIX + "preprocess_output.jsonl", type=AssetTypes.URI_FILE, mode="mount")
        preprocess.outputs.output_data_path = preprocess_output_path

        pf_output = Output(path=AML_DATASTORE_PATH_PREFIX + AML_DATASTORE_PROMPTFLOW_FILE_NAME, type=AssetTypes.URI_FILE, mode="rw_mount")

        evaluation = pipeline_components[1](
            data=preprocess.outputs.output_data_path,
            url="${data.url}",
            answer="${data.answer}",
            eveidence="${data.evidence}",
            )
        evaluation.outputs.flow_outputs = pf_output

        postprocess = pipeline_components[2](
            input_data_path=evaluation.outputs.flow_outputs,
        )

    return evaluation_pipeline

def build_pipeline(
        pipeline_name: str
    ):
    """
    Constructs an Azure Machine Learning pipeline. It encapsulates the process of defining pipeline inputs,
    loading pipeline components from YAMLs, configuring component environments settings, configuring pipeline settings etc.

    Args:
        pipeline_name (str): Name of the pipeline.

    Returns:
        PipelineJob: Azure Machine Learning pipeline job.
    """
    
    preprocess_component = load_component("components/preprocess.yaml")
    evaluation_promptflow_component = load_component("../flows/experiment/flow.dag.yaml")
    postprocess_component = load_component("components/postprocess.yaml")

    pipeline_components.append(preprocess_component)
    pipeline_components.append(evaluation_promptflow_component)
    pipeline_components.append(postprocess_component)

    pipeline_definition = create_dynamic_evaluation_pipeline(
        pipeline_name=pipeline_name
    )

    return pipeline_definition

def get_ml_client():
    # authenticate
    credential = DefaultAzureCredential()

    subscription_id = os.getenv("SUBSCRIPTION_ID")
    resource_group_name = os.getenv("RESOURCE_GROUP_NAME")
    workspace_name = os.getenv("AML_WORKSPACE_NAME")
    # Get a handle to the workspace
    ml_client = MLClient(
        credential=credential,
        subscription_id=subscription_id,
        resource_group_name=resource_group_name,
        workspace_name=workspace_name,
    )
    return ml_client

if __name__ == "__main__":
    load_dotenv()
    subscription_id = os.getenv("SUBSCRIPTION_ID")
    resource_group_name = os.getenv("RESOURCE_GROUP_NAME")
    workspace_name = os.getenv("AML_WORKSPACE_NAME")
    compute_target = os.getenv("AML_COMPUTE_TARGET")
    aml_environment_name = "myenv"
    pipeline_name = "my_pipeline"
    pipeline_definition = build_pipeline(
        pipeline_name=pipeline_name,
    )

    ml_client = get_ml_client()
    pipeline_job = pipeline_definition(name=pipeline_name)
    pipeline_job.settings.default_compute = compute_target
    result = ml_client.jobs.create_or_update(
        pipeline_job,
        experiment_name="pf_in_pipeline_experiment",
    )