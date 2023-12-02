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
from llmops.common.logger import llmops_logger
import argparse

logger = llmops_logger("get_workspace")


def get_workspace(subscription_id: str,
                  resource_group_name: str,
                  workspace_name: str):
    """
    Run to get workspace object.

    This function uses default Azure credentials.

    Args:
        subscription_id (str): user provided azure subscription id.
        resource_group_name (str): user provided resource group name.
        workspace_name (str): user provided azure AML workspace name.

    Returns:
        object: The generated workspace object
    """
    try:
        logger.info(f"Getting access to {workspace_name} workspace.")
        client = MLClient(
            DefaultAzureCredential(),
            subscription_id=subscription_id,
            resource_group_name=resource_group_name,
            workspace_name=workspace_name,
        )

        workspace = client.workspaces.get(workspace_name)
        logger.info(f"Reference to {workspace_name} has been obtained.")
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
        help="Azure subscription id"
        )

    parser.add_argument(
        "--resource_group_name",
        type=str,
        help="Azure Machine learning resource group"
    )
    parser.add_argument(
        "--workspace_name",
        type=str,
        help="Azure Machine learning Workspace name"
    )

    args = parser.parse_args()

    get_workspace(
        args.subscription_id,
        args.resource_group_name,
        args.workspace_name
        )


if __name__ == "__main__":
    main()
