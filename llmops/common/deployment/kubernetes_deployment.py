"""
This module does deployment of flows to Kubernetes.

The code used Attached kubernetes computes as deployment target.
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
import subprocess
import os
from typing import Optional

from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    KubernetesOnlineDeployment,
    Environment,
    OnlineRequestSettings,
    BuildContext,
    DataCollector,
    DeploymentCollection
)
from azure.identity import DefaultAzureCredential
from azure.ai.ml.entities._deployment.resource_requirements_settings import (
    ResourceRequirementsSettings,
)
from azure.ai.ml.entities._deployment.container_resource_settings import (
    ResourceSettings,
)
from llmops.common.common import REQUEST_TIMEOUT_MS
from dotenv import load_dotenv


from llmops.common.logger import llmops_logger
from llmops.common.experiment_cloud_config import ExperimentCloudConfig
from llmops.common.experiment import load_experiment
from llmops.common.common import resolve_env_vars
from llmops.common.common import FlowTypeOption

logger = llmops_logger("provision_deployment")

_FLOW_DAG_FILENAME = ("flow.dag.yml", "flow.dag.yaml")
_FLOW_FLEX_FILENAME = ("flow.flex.yml", "flow.flex.yaml")


def create_kubernetes_deployment(
    model_version: str,
    exp_filename: Optional[str] = None,
    base_path: Optional[str] = None,
    build_id: Optional[str] = None,
    env_name: Optional[str] = None,
    subscription_id: Optional[str] = None,
):
    """Create deployment for the model version."""
    config = ExperimentCloudConfig(
        subscription_id=subscription_id, env_name=env_name
    )
    experiment = load_experiment(
        filename=exp_filename, base_path=base_path, env=config.environment_name
    )
    experiment_name = experiment.name
    model_name = f"{experiment_name}_{env_name}"

    found_flex = False
    flow_type = FlowTypeOption.CLASS_FLOW
    for root, dirs, files in os.walk(
            os.path.join(experiment.base_path, experiment.flow)
            ):
        for file in files:
            if file in _FLOW_FLEX_FILENAME:
                found_flex = True
                flow_type = FlowTypeOption.CLASS_FLOW
                flow_file_path = os.path.abspath(
                    os.path.join(experiment.base_path, experiment.flow, file)
                    )
            elif file in _FLOW_DAG_FILENAME:
                flow_file_path = os.path.abspath(
                    os.path.join(experiment.base_path, experiment.flow, file)
                    )
                flow_type = FlowTypeOption.DAG_FLOW

    params_dict = {}
    if found_flex:
        result = subprocess.run(
            [
                "python",
                "llmops/common/deployment/generate_config.py",
                flow_file_path,
                "false"
            ],
            stdout=subprocess.PIPE
        )
        output = result.stdout.decode("utf-8")
        substrings = output.split()

        # Iterate over each substring
        for substring in substrings:
            # Split the substring by the "=" delimiter
            key_value = substring.split("=")

            # Check if the substring contains the "=" delimiter
            if len(key_value) == 2:
                key, value = key_value
                params_dict[key] = value

    env_vars = resolve_env_vars(experiment.base_path, logger)

    real_config = f"{base_path}/configs/deployment_config.json"

    logger.info(f"Model name: {model_name}")

    ml_client = MLClient(
        subscription_id=config.subscription_id,
        resource_group_name=config.resource_group_name,
        workspace_name=config.workspace_name,
        credential=DefaultAzureCredential(),
    )

    model = ml_client.models.get(model_name, model_version)

    config_file = open(real_config)
    endpoint_config = json.load(config_file)
    for elem in endpoint_config["kubernetes_endpoint"]:
        if "ENDPOINT_NAME" in elem and "ENV_NAME" in elem:
            if env_name == elem["ENV_NAME"]:
                data_collector = DataCollector(
                    collections={
                        "model_inputs": DeploymentCollection(
                            enabled="true",
                        ),
                        "model_outputs": DeploymentCollection(
                            enabled="true",
                        )
                    },
                    sampling_rate=1,
                )

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
                # prior_deployment_traffic_allocation = elem[
                #    "PRIOR_DEPLOYMENT_TRAFFIC_ALLOCATION"
                # ]
                deployment_desc = elem["DEPLOYMENT_DESC"]
                environment_variables = dict(elem["ENVIRONMENT_VARIABLES"])

                if os.environ.get(
                    "APPLICATIONINSIGHTS_CONNECTION_STRING",
                    None
                ):
                    environment_variables[
                        "APPLICATIONINSIGHTS_CONNECTION_STRING"
                    ] = (
                        os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
                    )

                if isinstance(env_vars, dict):
                    if env_vars:
                        for key, value in env_vars.items():
                            environment_variables[key] = value
                for key, value in params_dict.items():
                    environment_variables[key] = value
                environment_variables["PROMPTFLOW_RUN_MODE"] = "serving"
                environment_variables["PROMPTFLOW_SERVING_ENGINE"] = "fastapi"
                environment_variables["F_LOGGING_LEVEL"] = "WARNING"
                environment_variables["PRT_CONFIG_OVERRIDE"] = (
                    f"deployment.subscription_id={config.subscription_id},"
                    f"deployment.resource_group={config.resource_group_name},"
                    f"deployment.workspace_name={config.workspace_name},"
                    f"deployment.endpoint_name={endpoint_name},"
                    f"deployment.deployment_name={deployment_name}"
                )
                environment = Environment(
                    build=BuildContext(
                        path=experiment.get_flow_detail(flow_type).flow_path,
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
                    traffic_allocation[deployment_name] = (
                        deployment_traffic_allocation
                    )
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
                    request_settings=OnlineRequestSettings(
                        request_timeout_ms=REQUEST_TIMEOUT_MS
                    ),
                    data_collector=data_collector,
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


def main():
    """Entry main function to create deployment."""
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
        help="Subscription ID",
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
        help="environment name(dev, test, prod) for execution and deployment",
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
