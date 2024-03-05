import json
import os
import subprocess

import yaml
from azure.ai.ml import Input, MLClient, Output, load_component, command
from azure.ai.ml.constants import AssetTypes
from azure.ai.ml.dsl import pipeline
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
import argparse

AML_EXPERIMENT_NAME = "pf_in_pipeline_experiment"
AML_PIPELINE_NAME = "my_pipeline"
AML_DATASTORE_PATH_PREFIX = (
    "azureml://datastores/workspaceblobstore/paths/pf_in_pipeline_test/"
)
AML_DATASTORE_PREPROCESS_FILE_NAME = "data.jsonl"


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

        pf_input_path = Input(
            path=(AML_DATASTORE_PATH_PREFIX + AML_DATASTORE_PREPROCESS_FILE_NAME),
            type=AssetTypes.URI_FILE,
        )
        preprocess_output_path = Output(
            path=AML_DATASTORE_PATH_PREFIX, type=AssetTypes.URI_FOLDER, mode="rw_mount"
        )
        preprocess = pipeline_components[0](
            input_data_path=pf_input_path, max_records=2
        )
        preprocess.outputs.output_data_path = preprocess_output_path

        pf_output = Output(
            path=AML_DATASTORE_PATH_PREFIX,
            type=AssetTypes.URI_FOLDER,
            mode="rw_mount",
        )

        experiment = pipeline_components[1](
            data=preprocess.outputs.output_data_path,
            url="${data.url}",
        )
        experiment.outputs.flow_outputs = pf_output

        postprocess = pipeline_components[2](
            input_data_path=experiment.outputs.flow_outputs,
        )

    return evaluation_pipeline


def build_pipeline(pipeline_name: str, promptflow_component_path: str):
    """
    Constructs an Azure Machine Learning pipeline. It encapsulates the process of defining pipeline inputs,
    loading pipeline components from YAMLs, configuring component environments settings, configuring pipeline settings etc.

    Args:
        pipeline_name (str): Name of the pipeline.

    Returns:
        PipelineJob: Azure Machine Learning pipeline job.
    """
    preprocess_component = command(
        name="preprocess",
        display_name="Data preparation for Promptflow in a pipeline experiment",
        description="Reads the input data and prepares it for the Promptflow experiment",
        inputs={
            "input_data_path": Input(type="uri_folder"),
            "max_records": Input(type="number"),
        },
        outputs = {
            "output_data_path": Output(type="uri_folder", mode="rw_mount"),
        },
        # The source folder of the component
        code="components/src",
        command="""python preprocess.py \
                --input_data_path "${{inputs.input_data_path}}" \
                --max_records "${{inputs.max_records}}" \
                --output_data_path "${{outputs.output_data_path}}" \
                """,
        environment="TODO",
    )
    # This step loads the promptflow in the pipeline as a component
    evaluation_promptflow_component = load_component(
        promptflow_component_path
    )
    postprocess_component = command(
        name="postprocess",
        display_name="Post processing for Promptflow in a pipeline experiment",
        description="Reads the output of the Promptflow experiment and does some post processing.",
        inputs={
            "input_data_path": Input(type="uri_folder"),
            "max_records": Input(type="number"),
        },
        # The source folder of the component
        code="components/src",
        command="""python postprocess.py  \
                --input_data_path "${{inputs.input_data_path}}" \
                """,
        environment="TODO",
    )
    pipeline_components.append(preprocess_component)
    pipeline_components.append(evaluation_promptflow_component)
    pipeline_components.append(postprocess_component)

    pipeline_definition = create_dynamic_evaluation_pipeline(
        pipeline_name=pipeline_name
    )

    return pipeline_definition


def prepare_and_execute(
    subscription_id,
    build_id, stage,
    run_id,
    data_purpose,
    flow_to_execute
):
    """
    Run the evaluation loop by executing evaluation flows.

    reads latest evaluation data assets
    executes evaluation flow against each provided bulk-run
    executes the flow creating a new evaluation job
    saves the results in both csv and html format

    Returns:
        None
    """
    main_config = open(f"{flow_to_execute}/llmops_config.json")
    model_config = json.load(main_config)

    for obj in model_config["envs"]:
        if obj.get("ENV_NAME") == stage:
            config = obj
            break

    resource_group_name = config["RESOURCE_GROUP_NAME"]
    workspace_name = config["WORKSPACE_NAME"]
    data_mapping_config = f"{flow_to_execute}/configs/mapping_config.json"
    standard_flow_path = config["STANDARD_FLOW_PATH"]
    data_config_path = f"{flow_to_execute}/configs/data_config.json"

    runtime = config["RUNTIME_NAME"]
    experiment_name = f"{flow_to_execute}_{stage}"

    ml_client = MLClient(
        DefaultAzureCredential(),
        subscription_id,
        resource_group_name,
        workspace_name
    )
    
    #logger.info(data_mapping_config)
    # TODO data path how to take input in the promptflow

    flow_path = f"{flow_to_execute}/{standard_flow_path}/flow.dag.yaml"
    build_pipeline("TODO_PipelineName", flow_path)
    
    pipeline_definition = build_pipeline(
        pipeline_name="TODO_PipelineName",
    )
    
    pipeline_job = pipeline_definition(name="TODO_PipelineName")
   # pipeline_job.settings.default_compute = compute_target # TODO compute

    # Execute the ML Pipeline
    job = ml_client.jobs.create_or_update(
        pipeline_job,
        experiment_name=experiment_name,
    )

    ml_client.jobs.stream(name=job.name)

    
    
if __name__ == "__main__":
    """
    Run the main evaluation loop by executing evaluation flows.

    Returns:
        None
    """
    parser = argparse.ArgumentParser("prompt_evaluation")
    parser.add_argument(
        "--subscription_id",
        type=str,
        help="Azure subscription id",
        required=True,
    )
    parser.add_argument(
        "--build_id",
        type=str,
        help="Unique identifier for build execution",
        required=True,
    )
    parser.add_argument(
        "--env_name",
        type=str,
        help="environment name(dev, test, prod) for execution/deployment",
        required=True,
    )
    parser.add_argument(
        "--data_purpose",
        type=str,
        help="data identified by purpose",
        required=True
    )
    parser.add_argument(
        "--run_id",
        type=str,
        required=True,
        help="bulk run ids")

    parser.add_argument(
        "--flow_to_execute", type=str, help="flow use case name", required=True
    )

    args = parser.parse_args()
    prepare_and_execute(
        args.subscription_id,
        args.build_id,
        args.env_name,
        args.run_id,
        args.data_purpose,
        args.flow_to_execute,
    )
