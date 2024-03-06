"""
This module returns a AML workspace object after authentication.

Args:
--subscription_id: The Azure subscription ID.
This argument is required for identifying the Azure subscription.
--resource_group_name: The name of the resource group associated with
AML workspace.
--workspace_name: The AML workspace name.
"""

import argparse
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from typing import Optional

from llmops.common.logger import llmops_logger
from llmops.common.experiment_cloud_config import ExperimentCloudConfig

logger = llmops_logger("get_workspace")


def get_workspace(
    subscription_id: Optional[str],
    resource_group_name: Optional[str],
    workspace_name: Optional[str],
):
    """
    Run to get workspace object.

    This function uses default Azure credentials.

    Args:
        subscription_id (Optional[str]): user provided azure subscription id. If not provided, uses SUBSCRIPTION_ID environment variable.
        resource_group_name (Optional[str]): user provided resource group name. If not provided, uses RESOURCE_GROUP_NAME environment variable.
        workspace_name (Optional[str]): user provided azure AML workspace name. If not provided, uses WORKSPACE_NAME environment variable.

    Returns:
        object: The generated workspace object
    """
    try:
        config = ExperimentCloudConfig(
            subscription_id, resource_group_name, workspace_name
        )
        logger.info(f"Getting access to {config.workspace_name} workspace.")
        client = MLClient(
            DefaultAzureCredential(),
            subscription_id=config.subscription_id,
            resource_group_name=config.resource_group_name,
            workspace_name=config.workspace_name,
        )

        workspace = client.workspaces.get(workspace_name)
        logger.info(f"Reference to {workspace.name} has been obtained.")
        return workspace
    except Exception as ex:
        logger.info("Oops! invalid credentials.. Try again...")
        logger.error(ex)
        raise


def main():
    """
    Run the main function to get the workspace object.

    Returns:
        None
    """
    parser = argparse.ArgumentParser("get_workspace")
    parser.add_argument(
        "--subscription_id",
        type=str,
        help="Subscription ID, overrides the SUBSCRIPTION_ID environment variable",
        default=None,
    )

    parser.add_argument(
        "--resource_group_name",
        type=str,
        help="Azure Machine learning resource group, overrides the RESOURCE_GROUP_NAME environment variable",
        default=None,
    )
    parser.add_argument(
        "--workspace_name",
        type=str,
        help="Azure Machine learning Workspace name, overrides the WORKSPACE_NAME environment variable",
        default=None,
    )

    args = parser.parse_args()

    get_workspace(args.subscription_id, args.resource_group_name, args.workspace_name)


if __name__ == "__main__":
    # Load variables from .env file into the environment
    load_dotenv(override=True)

    main()
