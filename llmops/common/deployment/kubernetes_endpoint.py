"""
This module creates Kubernetes AML online endpoint as flow deployment process.

Args:
--subscription_id: The Azure subscription ID.
This argument is required for identifying the Azure subscription.
--output_file: The file path for the output file needed for
the endpoint principal. This argument is required to specify the path
to the output file necessary for the endpoint principal.
--build_id: The build ID for deployment.
This argument is required to identify the build to be deployed.
--env_name: The environment name for deployment.
This argument is required to specify the
deployment environment (dev, test, prod).
--flow_to_execute: The name of the flow to execute.
This argument is required to specify the name of the flow for execution.
"""

import json
import argparse
from azure.ai.ml import MLClient
from azure.ai.ml.entities import KubernetesOnlineEndpoint
from azure.identity import DefaultAzureCredential
from llmops.common.config_utils import LLMOpsConfig

parser = argparse.ArgumentParser("provision_kubernetes_endpoints")
parser.add_argument(
    "--subscription_id",
    type=str,
    help="Azure subscription id",
    required=True
)
parser.add_argument(
    "--output_file",
    type=str,
    help="outfile file needed for endpoint principal",
    required=True,
)
parser.add_argument(
    "--build_id",
    type=str,
    help="build id for deployment",
    required=True
)
parser.add_argument(
    "--env_name",
    type=str,
    help="environment name (e.g. dev, test, prod)",
    required=True,
)
parser.add_argument(
    "--flow_to_execute",
    type=str,
    help="name of the flow",
    required=True
)
args = parser.parse_args()

build_id = args.build_id
output_file = args.output_file
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
        endpoint_desc = endpoint_config["ENDPOINT_DESC"]
        compute_name = endpoint_config["COMPUTE_NAME"]

        endpoint = KubernetesOnlineEndpoint(
            name=endpoint_name,
            description=endpoint_desc,
            compute=compute_name,
            auth_mode="key",
            tags={
                "build_id": build_id
                },
        )

        ml_client.online_endpoints.begin_create_or_update(
            endpoint=endpoint
        ).result()

        principal_id = ml_client.online_endpoints.get(
            endpoint_name
        ).identity.principal_id

        if output_file is not None:
            with open(output_file, "w") as out_file:
                out_file.write(str(principal_id))
