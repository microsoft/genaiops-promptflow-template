"""
This module does deployment of flows to Kubernetes.

The code used AML Attached kubernetes computes as deployment target.
It configures Kubernetes Online deployments for Prompt Flow 'flows'

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
    KubernetesOnlineDeployment,
    Environment,
    OnlineRequestSettings,
    BuildContext
)
from azure.identity import DefaultAzureCredential
from azure.ai.ml.entities._deployment.resource_requirements_settings import (
    ResourceRequirementsSettings,
)
from azure.ai.ml.entities._deployment.container_resource_settings import (
    ResourceSettings,
)

from llmops.common.logger import llmops_logger
logger = llmops_logger("kubernetes_deployment")

parser = argparse.ArgumentParser("provision_kubernetes_deployment")
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
    "--flow_to_execute", type=str, help="name of the flow", required=True
)


args = parser.parse_args()

model_version = args.model_version
build_id = args.build_id
stage = args.env_name
flow_to_execute = args.flow_to_execute
model_name = f"{flow_to_execute}_{stage}"
main_config = open(f"{flow_to_execute}/llmops_config.json")
model_config = json.load(main_config)

for obj in model_config["envs"]:
    if obj.get("ENV_NAME") == stage:
        config = obj
        break

resource_group_name = config["RESOURCE_GROUP_NAME"]
workspace_name = config["WORKSPACE_NAME"]
real_config = f"{flow_to_execute}/configs/deployment_config.json"

logger.info(f"Model name: {model_name}")

ml_client = MLClient(
    DefaultAzureCredential(),
    args.subscription_id,
    resource_group_name,
    workspace_name
)

model = ml_client.models.get(model_name, model_version)

config_file = open(real_config)
endpoint_config = json.load(config_file)
for elem in endpoint_config["kubernetes_endpoint"]:
    if "ENDPOINT_NAME" in elem and "ENV_NAME" in elem:
        if stage == elem["ENV_NAME"]:
            flow_path = elem["STANDARD_FLOW_PATH"]
            endpoint_name = elem["ENDPOINT_NAME"]
            deployment_name = elem["CURRENT_DEPLOYMENT_NAME"]
            deployment_vm_size = elem["DEPLOYMENT_VM_SIZE"]
            deployment_instance_count = elem["DEPLOYMENT_INSTANCE_COUNT"]
            deployment_traffic_allocation = elem[
                "CURRENT_DEPLOYMENT_TRAFFIC_ALLOCATION"
            ]
            prior_deployment_name = elem["PRIOR_DEPLOYMENT_NAME"]
            cpu_allocation = elem["CPU_ALLOCATION"]
            memory_allocation = elem["MEMORY_ALLOCATION"]
            prior_deployment_traffic_allocation = elem[
                "PRIOR_DEPLOYMENT_TRAFFIC_ALLOCATION"
            ]
            deployment_desc = elem["DEPLOYMENT_DESC"]
            environment_variables = dict(elem["ENVIRONMENT_VARIABLES"])
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
            environment = Environment(
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

            traffic_allocation = {}
            deployments = ml_client.online_deployments.list(
                endpoint_name, local=False
                )

            deploy_count = sum(1 for _ in deployments)

            if deploy_count >= 1:
                traffic_allocation[deployment_name] = \
                    deployment_traffic_allocation
                traffic_allocation[prior_deployment_name] = 100 - int(
                    deployment_traffic_allocation
                )
            else:
                traffic_allocation[deployment_name] = 100

            blue_deployment = KubernetesOnlineDeployment(
                name=deployment_name,
                endpoint_name=endpoint_name,
                model=model,
                description=deployment_desc,
                environment=environment,
                instance_type=deployment_vm_size,
                instance_count=deployment_instance_count,
                environment_variables=dict(environment_variables),
                tags={"build_id": build_id},
                app_insights_enabled=True,
                request_settings=OnlineRequestSettings(
                    request_timeout_ms=90000
                    ),
                resources=ResourceRequirementsSettings(
                    requests=ResourceSettings(
                        cpu=cpu_allocation,
                        memory=memory_allocation,
                    ),
                ),
            )

            ml_client.online_deployments.begin_create_or_update(
                blue_deployment
            ).result()

            endpoint = ml_client.online_endpoints.get(
                endpoint_name, local=False
                )
            endpoint.traffic = traffic_allocation
            ml_client.begin_create_or_update(endpoint).result()
