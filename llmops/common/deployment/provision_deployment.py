"""
This module does deployment of flows to AML Managed compute.

The code used AML compute as deployment target.
It configures Managed Online deployments for Prompt Flow 'flows'

Args:
--subscription_id: The Azure subscription ID.
This argument is required for identifying the Azure subscription.
--model_version: The registered model version to be deployed.
This argument is required to specify the version of the model for deployment.
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
import os
from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    ManagedOnlineDeployment,
    Environment,
    OnlineRequestSettings,
    BuildContext
)
from azure.identity import DefaultAzureCredential
from llmops.common.config_utils import LLMOpsConfig
from llmops.common.logger import llmops_logger
logger = llmops_logger("provision_deployment")

parser = argparse.ArgumentParser("provision_deployment")
parser.add_argument(
    "--subscription_id",
    type=str,
    help="Azure subscription id",
    required=True
)
parser.add_argument(
    "--model_version",
    type=str,
    help="registered model version to be deployed",
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
    help="environment name (dev, test, prod) for deployment",
    required=True,
)
parser.add_argument(
    "--flow_to_execute",
    type=str,
    help="name of the flow",
    required=True
)


args = parser.parse_args()

model_version = args.model_version
build_id = args.build_id
stage = args.env_name
flow_to_execute = args.flow_to_execute
model_name = f"{flow_to_execute}_{stage}"
main_config = LLMOpsConfig(flow_name=flow_to_execute, environment=stage)
config = main_config.model_config

resource_group_name = config["RESOURCE_GROUP_NAME"]
workspace_name = config["WORKSPACE_NAME"]
flow_path =  config["STANDARD_FLOW_PATH"]

logger.info(f"Model name: {model_name}")

ml_client = MLClient(
    DefaultAzureCredential(),
    args.subscription_id,
    resource_group_name,
    workspace_name
)

model = ml_client.models.get(model_name, model_version)

endpoint_config = main_config.azure_managed_endpoint_config
if "ENDPOINT_NAME" in endpoint_config and "ENV_NAME" in endpoint_config:
    if stage == endpoint_config["ENV_NAME"]:
        endpoint_name = endpoint_config["ENDPOINT_NAME"]
        deployment_name = endpoint_config["CURRENT_DEPLOYMENT_NAME"]
        deployment_vm_size = endpoint_config["DEPLOYMENT_VM_SIZE"]
        deployment_instance_count = endpoint_config["DEPLOYMENT_INSTANCE_COUNT"]
        deployment_traffic_allocation = endpoint_config[
            "CURRENT_DEPLOYMENT_TRAFFIC_ALLOCATION"
        ]
        prior_deployment_name = endpoint_config["PRIOR_DEPLOYMENT_NAME"]
        prior_deployment_traffic_allocation = endpoint_config[
            "PRIOR_DEPLOYMENT_TRAFFIC_ALLOCATION"
        ]
        deployment_desc = endpoint_config["DEPLOYMENT_DESC"]
        environment_variables = dict(endpoint_config["ENVIRONMENT_VARIABLES"])
        environment_variables["PROMPTFLOW_RUN_MODE"] = "serving"
        environment_variables[
            "PRT_CONFIG_OVERRIDE"
            ] = (
                f"deployment.subscription_id={args.subscription_id},"
                f"deployment.resource_group={resource_group_name},"
                f"deployment.workspace_name={workspace_name},"
                f"deployment.endpoint_name={endpoint_name},"
                f"deployment.deployment_name={deployment_name}"
            )

        traffic_allocation = {}
        deployments = ml_client.online_deployments.list(
            endpoint_name,
            local=False
        )

        deploy_count = sum(1 for _ in deployments)

        if deploy_count >= 1:
            traffic_allocation[deployment_name] = \
                deployment_traffic_allocation
            traffic_allocation[prior_deployment_name] = \
                100 - int(
                deployment_traffic_allocation
            )
        else:
            traffic_allocation[deployment_name] = 100

        env_docker = Environment(
            build = BuildContext(
                path = os.path.join(flow_to_execute,flow_path),
                dockerfile_path = "docker/dockerfile"
            ),
            name=deployment_name,
            description="Environment created from a Docker context.",
            inference_config={
                "liveness_route": {"path": "/health", "port": "8080"},
                "readiness_route": {"path": "/health", "port": "8080"},
                "scoring_route": {"path": "/score", "port": "8080"},
            }

        )

        blue_deployment = ManagedOnlineDeployment(
            name=deployment_name,
            endpoint_name=endpoint_name,
            model=model,
            description=deployment_desc,
            environment=env_docker,
            instance_type=deployment_vm_size,
            instance_count=deployment_instance_count,
            environment_variables=dict(environment_variables),
            tags={
                "build_id": build_id
                },
            app_insights_enabled=True,
            request_settings=OnlineRequestSettings(
                request_timeout_ms=90000
            ),
        )

        ml_client.online_deployments.begin_create_or_update(
            blue_deployment
        ).result()

        endpoint = ml_client.online_endpoints.get(
            endpoint_name,
            local=False
        )

        endpoint.traffic = traffic_allocation
        ml_client.begin_create_or_update(endpoint).result()
