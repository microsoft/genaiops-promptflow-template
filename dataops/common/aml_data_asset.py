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
import json

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
        "--config_path_root_dir",
        type=str,
        help="Root dir for config file",
        required=True,
    )

    args = parser.parse_args()

    subscription_id = args.subscription_id
    resource_group_name = args.resource_group_name
    workspace_name = args.workspace_name
    config_path_root_dir = args.config_path_root_dir

    config_path = os.path.join(os.getcwd(), f"{config_path_root_dir}/configs/deployment_config.json")
    config = json.load(open(config_path))
    
    path_config = config['PATH']
    target_data_dir = path_config['TARGET_DATA_DIR']

    data_asset_config = config['DATA_ASSET']
    data_asset_name = data_asset_config['NAME']
    data_asset_description = data_asset_config['DESCRIPTION']

    aml_client = get_aml_client(
        subscription_id,
        resource_group_name,
        workspace_name,
    )

    register_data_asset(
        name = data_asset_name,
        description = data_asset_description,
        target_dir = target_data_dir,
        aml_client = aml_client
    )

if __name__ == "__main__":
    main()