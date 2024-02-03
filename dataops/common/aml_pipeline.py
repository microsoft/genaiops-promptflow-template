"""
This module returns a AML workspace object after authentication.

Args:
--subscription_id: The Azure subscription ID.
This argument is required for identifying the Azure subscription.
--resource_group_name: The name of the resource group associated with
AML workspace.
--workspace_name: The AML workspace name.
"""
from azure.ai.ml.dsl import pipeline
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential
from azure.ai.ml import command
from azure.ai.ml import Input, Output
from azure.ai.ml import Input, Output
from azure.ai.ml.entities import Data
from azure.ai.ml import MLClient
from azure.ai.ml.constants import AssetTypes
import os
import argparse

pipeline_components = []

@pipeline(
    compute="serverless",
    description="data prep pipeline",
)
def ner_data_prep_pipeline(
    raw_data_dir
):
    prep_data_job = pipeline_components[0](
        raw_data_dir=raw_data_dir
    )

    return {
        "target_dir": prep_data_job.outputs.target_dir
    }

def get_prep_data_component(
        name,
        display_name,
        description,
        data_pipeline_code_dir,
        environment
):
    data_pipeline_code_dir = os.path.join(os.getcwd(), data_pipeline_code_dir)

    prep_data_component = command(
        name = name,
        display_name = display_name,
        description = description,
        inputs={
            "raw_data_dir": Input(type="uri_folder")
        },
        outputs=dict(
            target_dir=Output(type="uri_folder", mode="rw_mount")
        ),
        code=data_pipeline_code_dir,
        command="""python prep_data.py \
                --raw_data_dir ${{inputs.raw_data_dir}} \
                --target_dir ${{outputs.target_dir}} \
                """,
        environment=environment,
    )

    return prep_data_component

def get_aml_client(
        subscription_id,
        resource_group_name,
        workspace_name,
):
    aml_client = MLClient(
        DefaultAzureCredential(),
        subscription_id=subscription_id,
        resource_group_name=resource_group_name,
        workspace_name=workspace_name,
    )

    return aml_client

def create_pipeline_job(
        experiment_name,
        pipeline_job,
        aml_client,
):
    aml_client.jobs.create_or_update(
        job = pipeline_job, 
        experiment_name = experiment_name
    )

def register_data_asset(
        name,
        description,
        target_dir,
        aml_client
):
    target_path = os.path.join(target_dir, 'data.jsonl')
    aml_dataset = Data(
        path = target_path,
        type = AssetTypes.URI_FILE,
        description = description,
        name = name
    )

    aml_client.data.create_or_update(aml_dataset)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--subscription_id",
        type=str,
        help="Azure subscription id",
        required=True,
    )
    parser.add_argument(
        "--resource_group_name",
        type=str,
        help="Azure resource group",
        required=True,
    )
    parser.add_argument(
        "--workspace_name",
        type=str,
        help="Azure ML workspace",
        required=True,
    )

    args = parser.parse_args()

    subscription_id = args.subscription_id
    resource_group_name = args.resource_group_name
    workspace_name = args.workspace_name
    
    raw_data_dir = 'dataops_named_entity_recognition/data'
    target_dir = 'dataops_named_entity_recognition/data'
    data_pipeline_code_dir = 'dataops_named_entity_recognition/aml/data_pipeline'
    environment = 'AzureML-sklearn-1.0-ubuntu20.04-py38-cpu@latest'
    experiment_name = 'NER data pipeline'
    data_prep_component_name = 'prep_data'
    data_asset_name = 'ner_exp'

    prep_data_component = get_prep_data_component(
        name = data_prep_component_name,
        display_name = 'Preapre data',
        description = 'Loading and processing data for prompt engineering.',
        data_pipeline_code_dir = data_pipeline_code_dir,
        environment = environment
    )

    pipeline_components.append(prep_data_component)

    pipeline_job = ner_data_prep_pipeline(
        raw_data_dir = Input(type="uri_folder", path=os.path.join(os.getcwd(), raw_data_dir))
    )

    aml_client = get_aml_client(
        subscription_id,
        resource_group_name,
        workspace_name,
    )

    create_pipeline_job(
        experiment_name,
        pipeline_job,
        aml_client,
    )

    register_data_asset(
        name = data_asset_name,
        description = 'ner experiment data',
        target_dir = target_dir,
        aml_client = aml_client
    )

if __name__ == "__main__":
    main()