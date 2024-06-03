
"""
This module creates connections.

Args:
--subscription_id: The Azure subscription ID.
This argument is required for identifying the Azure subscription.
--file: The name of the experiment file. Default is 'experiment.yaml'.
--base_path: Base path of the use case. Where flows, data,
and experiment.yaml are expected to be found.
--env_name: The environment name for execution and deployment.
This argument is required to specify the environment (dev, test, prod)
for execution or deployment.
"""

import argparse
import hashlib
from azure.ai.ml import MLClient
from azure.ai.ml.entities import Data
from azure.ai.ml.constants import AssetTypes
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from typing import Optional

from llmops.common.experiment_cloud_config import ExperimentCloudConfig
from llmops.common.config_utils import ExperimentConfig
from llmops.common.experiment import load_experiment
from llmops.common.logger import llmops_logger
from typing import Any
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential
from azure.ai.ml.entities import (
    WorkspaceConnection,
    Workspace,
    Hub,
    ApiKeyConfiguration,
    AzureOpenAIConnection,
    AzureAIServicesConnection,
    AzureAISearchConnection,
    AzureContentSafetyConnection,
    AzureSpeechServicesConnection,
    APIKeyConnection,
    OpenAIConnection,
    SerpConnection,
    ServerlessConnection,
    AccountKeyConfiguration,
)

logger = llmops_logger("create_connections")

def create_connections(
    base_path: str,
    subscription_id: Optional[str] = None,
    env_name: Optional[str] = None,
):
    config = ExperimentCloudConfig(subscription_id=subscription_id, env_name=env_name)
    experiment_config = ExperimentConfig(base_path, env_name)

    ml_client = MLClient(
        DefaultAzureCredential(),
        config.subscription_id,
        config.resource_group_name,
        config.workspace_name,
    )

    # Get connections configuration
    connections = experiment_config.connections

    for connection in connections:
        connection_type = connection["connection_type"]
        connection_name = connection["connection"]
        connection_config = connection["config"]
        logger.info(f"Creating connection type : {connection_type} name:  {connection_name}")
        wps_connection = None
        match connection_type:
            case "AzureOpenAIConnection":
                wps_connection = AzureOpenAIConnection(**connection_config)
            case "AzureAISearchConnection":
                wps_connection = AzureAISearchConnection(**connection_config)
            case "OpenAIConnection":
                wps_connection = OpenAIConnection(**connection_config)
            case "Custom":
                wps_connection = WorkspaceConnection(**connection_config)
            case _:
                logger.error("Not implemented or Unknown Connection Type")

        if wps_connection:
            result = ml_client.connections.create_or_update(wps_connection)
            logger.info(f"Created connection {result}")


def main():
    parser = argparse.ArgumentParser("create connections")
    parser.add_argument(
        "--subscription_id",
        type=str,
        help="Subscription ID, overrides the SUBSCRIPTION_ID environment variable",
        default=None,
    )
    parser.add_argument(
        "--base_path",
        type=str,
        help="Base path of the use case",
        required=True,
    )
    parser.add_argument(
        "--env_name",
        type=str,
        help="environment name(dev, test, prod) for execution and deployment, overrides the ENV_NAME environment variable",
        default=None,
    )

    args = parser.parse_args()

    create_connections(args.base_path, args.subscription_id, args.env_name)


if __name__ == "__main__":
    # Load variables from .env file into the environment
    load_dotenv(override=True)

    main()

