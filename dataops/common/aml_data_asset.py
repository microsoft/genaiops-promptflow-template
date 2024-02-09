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
    parser.add_argument(
        "--env_name",
        type=str,
        help="Azure environment name",
        required=True,
    )
    parser.add_argument(
        "--step_action",
        type=str,
        help="Step action",
        required=True,
    )

    args = parser.parse_args()

    subscription_id = args.subscription_id
    resource_group_name = args.resource_group_name
    workspace_name = args.workspace_name
    step_action = args.step_action
    
    raw_data_dir = 'dataops_named_entity_recognition/data'
    target_dir = 'dataops_named_entity_recognition/data'
    data_pipeline_code_dir = 'dataops_named_entity_recognition/aml/data_pipeline'
    experiment_name = 'NER data pipeline'
    data_prep_component_name = 'prep_data'
    data_asset_name = 'ner_exp'

    aml_client = get_aml_client(
        subscription_id,
        resource_group_name,
        workspace_name,
    )

    if step_action == 'register_data_asset':
        register_data_asset(
            name = data_asset_name,
            description = 'ner experiment data',
            target_dir = target_dir,
            aml_client = aml_client
        )

if __name__ == "__main__":
    main()