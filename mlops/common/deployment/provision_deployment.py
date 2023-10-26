
import json
import argparse

from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    ManagedOnlineDeployment,
    Environment,
    OnlineRequestSettings
)
from azure.identity import DefaultAzureCredential



parser = argparse.ArgumentParser("provision_deployment")
parser.add_argument("--subscription_id", type=str, help="Azure subscription id", required=True)
parser.add_argument("--model_version", type=str, help="registered model version to be deployed", required=True)
parser.add_argument("--build_id", type=str, help="build id for deployment", required=True)
parser.add_argument("--env_type", type=str, help="env name (dev, test, prod) for deployment", required=True)
parser.add_argument("--model_type", type=str, help="name of the flow", required=True)


args = parser.parse_args()

model_version = args.model_version
build_id = args.build_id
stage = args.env_type
model_type = args.model_type
model_name = f"{model_type}_{stage}"
main_config = open(f"{model_type}/config.json")
model_config = json.load(main_config)

for obj in model_config["envs"]:
    if obj.get("ENV_NAME") == stage:
        config = obj
        break

resource_group_name = config["RESOURCE_GROUP_NAME"]
workspace_name = config["WORKSPACE_NAME"]
real_config = f"{model_type}/configs/deployment_config.json"

print(f"Model name: {model_name}")

ml_client = MLClient(
    DefaultAzureCredential(), args.subscription_id, resource_group_name, workspace_name
)

model = ml_client.models.get(model_name, model_version)

config_file = open(real_config)
endpoint_config = json.load(config_file)
for elem in endpoint_config['azure_managed_endpoint']:
    if 'ENDPOINT_NAME' in elem and 'ENV_NAME' in elem:
        if stage == elem['ENV_NAME']:
            endpoint_name = elem["ENDPOINT_NAME"]
            deployment_name = elem["CURRENT_DEPLOYMENT_NAME"]
            deployment_conda_path = elem["DEPLOYMENT_CONDA_PATH"]
            deployment_base_image = elem["DEPLOYMENT_BASE_IMAGE_NAME"]
            deployment_vm_size = elem["DEPLOYMENT_VM_SIZE"]
            deployment_instance_count = elem["DEPLOYMENT_INSTANCE_COUNT"]
            deployment_traffic_allocation = elem["CURRENT_DEPLOYMENT_TRAFFIC_ALLOCATION"]
            prior_deployment_name = elem["PRIOR_DEPLOYMENT_NAME"]
            prior_deployment_traffic_allocation = elem["PRIOR_DEPLOYMENT_TRAFFIC_ALLOCATION"]
            deployment_desc = elem["DEPLOYMENT_DESC"]
            environment_variables = dict(elem["ENVIRONMENT_VARIABLES"])
            environment_variables["PROMPTFLOW_RUN_MODE"] = "serving"
            environment_variables["PRT_CONFIG_OVERRIDE"] = f"deployment.subscription_id={args.subscription_id},deployment.resource_group={resource_group_name},deployment.workspace_name={workspace_name},deployment.endpoint_name={endpoint_name},deployment.deployment_name={deployment_name}"

            environment = Environment(
                image=deployment_base_image,
                inference_config = {
                    "liveness_route": {
                        "path" : "/health",
                        "port": "8080"
                    },
                   "readiness_route": {
                        "path" : "/health",
                        "port": "8080"
                    },
                   "scoring_route": {
                        "path" : "/score",
                        "port": "8080"
                    },
                }
            )

            traffic_allocation = {}
            deployments = ml_client.online_deployments.list(endpoint_name, local=False)

            deploy_count = sum(1 for _ in deployments)
            
            if deploy_count >= 1:
                traffic_allocation[deployment_name] = deployment_traffic_allocation
                traffic_allocation[prior_deployment_name] = 100 - int(deployment_traffic_allocation)
            else:
                traffic_allocation[deployment_name] = 100

            blue_deployment = ManagedOnlineDeployment(
                name=deployment_name,
                endpoint_name=endpoint_name,
                model=model,
                description=deployment_desc,
                environment=environment,
                instance_type=deployment_vm_size,
                instance_count=deployment_instance_count,
                environment_variables = dict(environment_variables),
                tags={"build_id": build_id},
                app_insights_enabled = True,
                request_settings=OnlineRequestSettings(request_timeout_ms=90000)
            )

            ml_client.online_deployments.begin_create_or_update(blue_deployment).result()
            
            endpoint = ml_client.online_endpoints.get(endpoint_name,local=False)
            endpoint.traffic = traffic_allocation
            ml_client.begin_create_or_update(endpoint).result()
            
            

