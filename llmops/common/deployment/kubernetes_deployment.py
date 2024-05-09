"""
This module does deployment of flows to Kubernetes.

The code used AML Attached kubernetes computes as deployment target.
It configures Kubernetes Online deployments for Prompt Flow 'flows'

Args:
--file: The name of the experiment file. Default is 'experiment.yaml'.
--base_path: Base path of the use case. Where flows, data,
and experiment.yaml are expected to be found.
--subscription_id: The Azure subscription ID. If this argument is not
specified, the SUBSCRIPTION_ID environment variable is expected to be provided.
--build_id: The unique identifier for build execution.
This argument is not required but will be added as a run tag if specified.
--env_name: The environment name for execution and deployment. This argument
is not required but will be used to read experiment overlay files if specified.
--model_version: The registered model version to be deployed.
This argument is required to specify the version of the model for deployment.
"""

import json
import argparse
import os
from typing import Optional

from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    KubernetesOnlineDeployment,
    Environment,
    OnlineRequestSettings,
    BuildContext,
)
from azure.identity import DefaultAzureCredential
from azure.ai.ml.entities._deployment.resource_requirements_settings import (
    ResourceRequirementsSettings,
)
from azure.ai.ml.entities._deployment.container_resource_settings import (
    ResourceSettings,
)
from dotenv import load_dotenv


from llmops.common.logger import llmops_logger
from llmops.common.experiment_cloud_config import ExperimentCloudConfig
from llmops.common.experiment import load_experiment

logger = llmops_logger("kubernetes_deployment")


def create_kubernetes_deployment(
    model_version: str,
    exp_filename: Optional[str] = None,
    base_path: Optional[str] = None,
    build_id: Optional[str] = None,
    env_name: Optional[str] = None,
    subscription_id: Optional[str] = None,
):
    config = ExperimentCloudConfig(subscription_id=subscription_id, env_name=env_name)
    experiment = load_experiment(
        filename=exp_filename, base_path=base_path, env=config.environment_name
    )
    experiment_name = experiment.name
    model_name = f"{experiment_name}_{env_name}"

    real_config = f"{base_path}/configs/deployment_config.json"

    logger.info(f"Model name: {model_name}")

    ml_client = MLClient(
        DefaultAzureCredential(),
        config.subscription_id,
        config.resource_group_name,
        config.workspace_name,
    )

    model = ml_client.models.get(model_name, model_version)

    config_file = open(real_config)
    endpoint_config = json.load(config_file)
    for elem in endpoint_config["kubernetes_endpoint"]:
        if "ENDPOINT_NAME" in elem and "ENV_NAME" in elem:
            if env_name == elem["ENV_NAME"]:
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
                environment_variables["PRT_CONFIG_OVERRIDE"] = (
                    f"deployment.subscription_id={config.subscription_id},"
                    f"deployment.resource_group={config.resource_group_name},"
                    f"deployment.workspace_name={config.workspace_name},"
                    f"deployment.endpoint_name={endpoint_name},"
                    f"deployment.deployment_name={deployment_name}"
                )
                environment = Environment(
                    build=BuildContext(
                        path=experiment.get_flow_detail().flow_path,
                        dockerfile_path="docker/dockerfile",
                    ),
                    name=deployment_name,
                    description="Environment created from a Docker context.",
                    inference_config={
                        "liveness_route": {"path": "/health", "port": "8080"},
                        "readiness_route": {"path": "/health", "port": "8080"},
                        "scoring_route": {"path": "/score", "port": "8080"},
                    },
                )

                traffic_allocation = {}
                deployments = ml_client.online_deployments.list(
                    endpoint_name, local=False
                )

                deploy_count = sum(1 for _ in deployments)

                if deploy_count >= 1:
                    traffic_allocation[deployment_name] = deployment_traffic_allocation
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
                    tags={"build_id": build_id} if build_id else {},
                    app_insights_enabled=True,
                    request_settings=OnlineRequestSettings(request_timeout_ms=90000),
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

                endpoint = ml_client.online_endpoints.get(endpoint_name, local=False)
                endpoint.traffic = traffic_allocation
                ml_client.begin_create_or_update(endpoint).result()


def main():
    parser = argparse.ArgumentParser("provision_kubernetes_deployment")
    parser.add_argument(
        "--file",
        type=str,
        help="The experiment file. Default is 'experiment.yaml'",
        required=False,
        default="experiment.yaml",
    )
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
    parser.add_argument(
        "--build_id",
        type=str,
        help="Unique identifier for build execution",
        default=None,
    )
    parser.add_argument(
        "--model_version",
        type=str,
        help="registered model version to be deployed",
        required=True,
    )

    args = parser.parse_args()

    create_kubernetes_deployment(
        args.model_version,
        args.file,
        args.base_path,
        args.build_id,
        args.env_name,
        args.subscription_id,
    )


if __name__ == "__main__":
    # Load variables from .env file into the environment
    load_dotenv(override=True)

    main()
