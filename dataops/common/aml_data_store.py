"""
This module registers the data store.
"""
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential
from azure.ai.ml.entities import AzureBlobDatastore
from azure.ai.ml.entities import SasTokenConfiguration
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


def register_data_store(
        name_datastore,
        description,
        sa_account_name,
        sa_container_name,
        sa_acc_key,
        aml_client
):
    store = AzureBlobDatastore(
        name=name_datastore,
        description=description,
        account_name=sa_account_name,
        container_name=sa_container_name,
        credentials= sa_acc_key
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
        "--sa_acc_key",
        type=str,
        help="SAS token for target storage account",
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
    sa_acc_key = args.sa_acc_key
    config_path_root_dir = args.config_path_root_dir

    config_path = os.path.join(os.getcwd(), f"{config_path_root_dir}/configs/dataops_config.json")
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
        sa_acc_key=sa_acc_key,
        aml_client=aml_client
    )


if __name__ == "__main__":
    main()