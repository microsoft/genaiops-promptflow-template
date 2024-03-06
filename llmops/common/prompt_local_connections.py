"""
This module evaluates bulk-runs using evaluation flows.

Args:
--subscription_id: The Azure subscription ID.
This argument is required for identifying the Azure subscription.
--build_id: The unique identifier for build execution.
This argument is required to identify the specific build execution.
--env_name: The environment name for execution/deployment.
This argument is required to specify the environment (dev, test, prod)
--data_purpose: The data identified by its purpose.
This argument is required to specify the purpose of the data.
--run_id: The bulk run IDs.
This argument is required to specify the bulk run IDs for execution.
--flow_to_execute: The name of the flow use case.
This argument is required to specify the name of the flow for execution.
"""

import argparse
import json
from dotenv import load_dotenv
from promptflow.entities import AzureOpenAIConnection
from promptflow import PFClient

from llmops.common.logger import llmops_logger
from llmops.common.experiment_cloud_config import ExperimentCloudConfig

logger = llmops_logger("prompt_aoai_connection")


def prepare_and_execute(
    base_path,
    env_name,
    connection_details,
):
    """
    Run the evaluation loop by executing evaluation flows.

    reads latest evaluation data assets
    executes evaluation flow against each provided bulk-run
    executes the flow creating a new evaluation job
    saves the results in both csv and html format

    Returns:
        None
    """
    config = ExperimentCloudConfig(env_name=env_name)
    logger.info(f"Using environment '{config.environment_name}'")

    secret_config = json.loads(connection_details)

    dep_config = f"{base_path}/configs/deployment_config.json"
    config_file = open(dep_config)

    pf = PFClient()

    connection_config = json.load(config_file)
    for elem in connection_config["webapp_endpoint"]:
        if "CONNECTION_NAMES" in elem and "ENV_NAME" in elem:
            if env_name == elem["ENV_NAME"]:
                con_to_create = list(elem["CONNECTION_NAMES"])

                for con in con_to_create:
                    for avail_con in secret_config:
                        if avail_con["name"] == con:
                            if avail_con["type"] == "azure_open_ai":
                                connection = AzureOpenAIConnection(
                                    name=avail_con["name"],
                                    api_key=avail_con["api_key"],
                                    api_base=avail_con["api_base"],
                                    api_type=avail_con["api_type"],
                                    api_version=avail_con["api_version"],
                                )
                                pf.connections.create_or_update(connection)

                                logger.info(f"{avail_con['name']} created successfully")


def main():
    """
    Create local Azure OpenAI connection objects.

    Returns:
        None
    """
    parser = argparse.ArgumentParser("aoai_pf_connection")

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

    parser.add_argument(
        "--connection_details",
        type=str,
        help="JSON string describing the details of local pf connection",
        required=True,
    )

    args = parser.parse_args()

    prepare_and_execute(args.base_path, args.env_name, args.connection_details)


if __name__ == "__main__":
    # Load variables from .env file into the environment
    load_dotenv(override=True)

    main()
