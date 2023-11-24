import argparse
import json
from azure.ai.ml import MLClient

from azure.identity import DefaultAzureCredential

parser = argparse.ArgumentParser("test_model")
parser.add_argument(
    "--subscription_id", type=str, help="Azure subscription id", required=True
)
parser.add_argument(
    "--flow_to_execute", type=str, help="name of the flow", required=True
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

main_config = open(f"{flow_to_execute}/llmops_config.json")
model_config = json.load(main_config)

for obj in model_config["envs"]:
    if obj.get("ENV_NAME") == stage:
        config = obj
        break

resource_group_name = config["RESOURCE_GROUP_NAME"]
workspace_name = config["WORKSPACE_NAME"]
real_config = f"{flow_to_execute}/configs/deployment_config.json"

ml_client = MLClient(
    DefaultAzureCredential(), args.subscription_id, resource_group_name, workspace_name
)

config_file = open(real_config)
endpoint_config = json.load(config_file)
for elem in endpoint_config["kubernetes_endpoint"]:
    if "ENDPOINT_NAME" in elem and "ENV_NAME" in elem:
        if stage == elem["ENV_NAME"]:
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
                request_file=f"{flow_to_execute}/{test_model_file}",
            )

            print(request_result)
