"""
This module creates the data assets.
"""
from azure.identity import DefaultAzureCredential
from azure.ai.ml.entities import Data
from azure.ai.ml import MLClient
from azure.ai.ml.constants import AssetTypes
import os
import argparse
import json

pipeline_components = []

"""
This function creates and returns an ml client.
The client is used to interact with Azure Machine Learning services.

Args:
--subscription_id: The Azure subscription ID.
This argument is required for identifying the Azure subscription.
--resource_group_name: The name of the resource group in Azure.
This argument is required to specify the resource group in Azure.
--workspace_name: The name of the workspace in Azure Machine Learning.
This argument is required to specify the workspace in Azure Machine Learning.
"""


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


"""
This function registers a data asset in Azure Machine Learning.
The data asset is identified by its name and description, and is associated with a specific data store and file path.

Args:
--name: The name of the data asset.
This argument is required to specify the name of the data asset.
--description: The description of the data asset.
This argument is required to provide a description of the data asset.
--aml_client: The Azure Machine Learning client.
This argument is required to interact with Azure Machine Learning services.
--data_store: The name of the data store in Azure.
This argument is required to specify the data store in Azure.
--file_path: The file path of the data asset in the data store.
This argument is required to specify the file path of the data asset in the data store.
"""


def register_data_asset(
        name,
        description,
        aml_client,
        data_store,
        file_path
):
    target_path = f"azureml://datastores/{data_store}/paths/{file_path}"
    aml_dataset = Data(
        path=target_path,
        type=AssetTypes.URI_FILE,
        description=description,
        name=name
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

    config_path = os.path.join(os.getcwd(), f"{config_path_root_dir}/configs/dataops_config.json")
    config = json.load(open(config_path))

    aml_client = get_aml_client(
        subscription_id,
        resource_group_name,
        workspace_name,
    )

    data_store = config["DATA_STORE_NAME"]
    data_asset_configs = config['DATA_ASSETS']
    for data_asset_config in data_asset_configs:
        data_asset_name = data_asset_config['NAME']
        data_asset_file_path = data_asset_config['PATH']
        data_asset_description = data_asset_config['DESCRIPTION']

        register_data_asset(
            name=data_asset_name,
            description=data_asset_description,
            aml_client=aml_client,
            data_store=data_store,
            file_path=data_asset_file_path
        )


if __name__ == "__main__":
    main()
