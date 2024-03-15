"""
This module returns a AML workspace object after authentication.

Args:
--subscription_id: The Azure subscription ID.
This argument is required for identifying the Azure subscription.
--resource_group_name: The name of the resource group associated with
AML workspace.
--workspace_name: The AML workspace name.
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
        target_sa_sas_token,
        aml_client
):
    store = AzureBlobDatastore(
        name=name_datastore,
        description=description,
        account_name=sa_account_name,
        container_name=sa_container_name
    )
    store = AzureBlobDatastore(
        name=name_datastore,
        description=description,
        account_name=sa_account_name,
        container_name=sa_container_name,
        credentials=SasTokenConfiguration(
            sas_token= target_sa_sas_token
        )
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
        "--sa_account_name",
        type=str,
        help="Storage account name",
        required=True,
    )

    parser.add_argument(
        "--sa_container_name",
        type=str,
        help="Container name",
        required=True,
    )

    parser.add_argument(
        "--target_sa_sas_token",
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
    sa_account_name = args.sa_account_name
    sa_container_name = args.sa_container_name
    target_sa_sas_token = args.target_sa_sas_token
    config_path_root_dir = args.config_path_root_dir

    config_path = os.path.join(os.getcwd(), f"{config_path_root_dir}/configs/dataops_config.json")
    config = json.load(open(config_path))

    aml_client = get_aml_client(
        subscription_id,
        resource_group_name,
        workspace_name,
    )

    register_data_store(
        name_datastore=config["DATA_STORE_NAME"],
        description=config["DATA_STORE_DESCRIPTION"],
        sa_account_name=sa_account_name,
        sa_container_name=sa_container_name,
        target_sa_sas_token=target_sa_sas_token,
        aml_client=aml_client
    )


if __name__ == "__main__":
    main()