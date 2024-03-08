"""
This module tests a standard flow deployed on AML Kubernetes attached compute.

Args:
--subscription_id: The Azure subscription ID.
This argument is required for identifying the Azure subscription.
--flow_to_execute: The name of the flow to test.
This argument is required to specify the name of the flow for testing.
--env_name: The environment name for deployment.
This argument is required to specify the
deployment environment (dev, test, prod).
"""

import argparse
import json
from azure.ai.ml import MLClient

from azure.identity import DefaultAzureCredential
from llmops.common.config_utils import LLMOpsConfig
from llmops.common.logger import llmops_logger
logger = llmops_logger("test_model_on_kubernetes")

parser = argparse.ArgumentParser("test_flow")
parser.add_argument(
    "--subscription_id",
    type=str,
    help="Azure subscription id",
    required=True
)

parser.add_argument(
    "--flow_to_execute",
    type=str,
    help="name of the flow",
    required=True
)

parser.add_argument(
    "--env_name",
    type=str,
    help="environment name (dev, test, prod) for deployment",
    required=True,
)

args = parser.parse_args()


stage = args.env_name
flow_to_execute = args.flow_to_execute

main_config = LLMOpsConfig(flow_name=flow_to_execute, environment=stage)
config = main_config.model_config

resource_group_name = config["RESOURCE_GROUP_NAME"]
workspace_name = config["WORKSPACE_NAME"]

ml_client = MLClient(
    DefaultAzureCredential(),
    args.subscription_id,
    resource_group_name,
    workspace_name
)

endpoint_config = main_config.kubernetes_endpoint_config
if "ENDPOINT_NAME" in endpoint_config and "ENV_NAME" in endpoint_config:
    if stage == endpoint_config["ENV_NAME"]:
        endpoint_name = endpoint_config["ENDPOINT_NAME"]
        deployment_name = endpoint_config["CURRENT_DEPLOYMENT_NAME"]
        test_model_file = endpoint_config["TEST_FILE_PATH"]

        endpoint_url = ml_client.online_endpoints.get(
            name=endpoint_name
        ).scoring_uri
        api_key = ml_client.online_endpoints.get_keys(
            name=endpoint_name
        ).primary_key

        request_result = ml_client.online_endpoints.invoke(
            endpoint_name=endpoint_name,
            deployment_name=deployment_name,
            request_file=f"{flow_to_execute}/{test_model_file}",
        )

        logger.info(request_result)
