"""
This module registers the data store.
"""
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential
from azure.ai.ml.entities import AzureBlobDatastore, AccountKeyConfiguration
import os
import argparse
import json

pipeline_components = []
"""
This function creates and returns a ml client.
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
This function registers a data store in Azure Machine Learning.
The data store is identified by its name and description, 
and is associated with a specific storage account and container.

Args:
--name_datastore: The name of the data store.
This argument is required to specify the name of the data store.
--description: The description of the data store.
This argument is required to provide a description of the data store.
--sa_account_name: The name of the storage account in Azure.
This argument is required to specify the storage account in Azure.
--sa_container_name: The name of the container in the storage account.
This argument is required to specify the container in the storage account.
--sa_key: The key of the storage account.
This argument is required to authenticate with the storage account.
--aml_client: The Azure Machine Learning client.
This argument is required to interact with Azure Machine Learning services.
"""


def register_data_store(
        name_datastore,
        description,
        sa_account_name,
        sa_container_name,
        sa_key,
        aml_client
):
    store = AzureBlobDatastore(
        name=name_datastore,
        description=description,
        account_name=sa_account_name,
        container_name=sa_container_name,
        credentials=AccountKeyConfiguration(account_key=sa_key)
    )
    aml_client.create_or_update(store)


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
        "--sa_key",
        type=str,
        help="Storage account key",
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
    sa_key = args.sa_key
    config_path_root_dir = args.config_path_root_dir

    config_path = os.path.join(os.getcwd(),
                               f"{config_path_root_dir}/configs/dataops_config.json")
    config = json.load(open(config_path))

    aml_client = get_aml_client(
        subscription_id,
        resource_group_name,
        workspace_name,
    )

    storage_config = config['STORAGE']
    storage_account = storage_config['STORAGE_ACCOUNT']
    target_container_name = storage_config['TARGET_CONTAINER']

    register_data_store(
        name_datastore=config["DATA_STORE_NAME"],
        description=config["DATA_STORE_DESCRIPTION"],
        sa_account_name=storage_account,
        sa_container_name=target_container_name,
        sa_key=sa_key,
        aml_client=aml_client
    )


if __name__ == "__main__":
    main()
