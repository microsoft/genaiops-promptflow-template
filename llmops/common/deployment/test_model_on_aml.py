"""
This module tests a standard flow deployed on AML managed compute.

Args:
--base_path: Base path of the use case. Where flows, data,
and experiment.yaml are expected to be found.
--subscription_id: The Azure subscription ID. If this argument is not
specified, the SUBSCRIPTION_ID environment variable is expected to be provided.
--env_name: The environment name for execution and deployment. This argument
is not required but will be used to read experiment overlay files if specified.
"""

import argparse
import json
from dotenv import load_dotenv
from typing import Optional

from azure.ai.ml import MLClient

from azure.identity import DefaultAzureCredential

from llmops.common.logger import llmops_logger
from llmops.common.experiment_cloud_config import ExperimentCloudConfig

logger = llmops_logger("test_model_on_aml")


def test_aml_model(
    base_path: Optional[str],
    env_name: Optional[str],
    subscription_id: Optional[str],
):
    config = ExperimentCloudConfig(subscription_id=subscription_id, env_name=env_name)
    real_config = f"{base_path}/configs/deployment_config.json"

    ml_client = MLClient(
        DefaultAzureCredential(),
        config.subscription_id,
        config.resource_group_name,
        config.workspace_name,
    )

    config_file = open(real_config)
    endpoint_config = json.load(config_file)
    for elem in endpoint_config["azure_managed_endpoint"]:
        if "ENDPOINT_NAME" in elem and "ENV_NAME" in elem:
            if env_name == elem["ENV_NAME"]:
                endpoint_name = elem["ENDPOINT_NAME"]
                deployment_name = elem["CURRENT_DEPLOYMENT_NAME"]
                test_model_file = elem["TEST_FILE_PATH"]

                endpoint_url = ml_client.online_endpoints.get(
                    name=endpoint_name
                ).scoring_uri
                api_key = ml_client.online_endpoints.get_keys(
                    name=endpoint_name
                ).primary_key

                request_result = ml_client.online_endpoints.invoke(
                    endpoint_name=endpoint_name,
                    deployment_name=deployment_name,
                    request_file=f"{base_path}/{test_model_file}",
                )

                logger.info(request_result)


def main():
    parser = argparse.ArgumentParser("test_flow")
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
    test_aml_model(
        args.base_path,
        args.env_name,
        args.subscription_id,
    )


if __name__ == "__main__":
    # Load variables from .env file into the environment
    load_dotenv(override=True)

    main()
