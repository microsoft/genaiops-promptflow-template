import argparse
import json
from azure.ai.ml import MLClient

from azure.identity import DefaultAzureCredential

parser = argparse.ArgumentParser("test_model")
parser.add_argument("--subscription_id", type=str, help="Azure subscription id", required=True)
parser.add_argument("--resource_group_name", type=str, help="Azure Machine learning resource group", required=True)
parser.add_argument("--workspace_name", type=str, help="Azure Machine learning Workspace name", required=True)
parser.add_argument("--realtime_deployment_config", type=str, help="file path of realtime config", required=True)
parser.add_argument("--environment_name",type=str,help="env name (dev, test, prod) for deployment", required=True)

args = parser.parse_args()

real_config = args.realtime_deployment_config
environment_name = args.environment_name

ml_client = MLClient(
    DefaultAzureCredential(), args.subscription_id,  args.resource_group_name,  args.workspace_name
)

config_file = open(real_config)
endpoint_config = json.load(config_file)
for elem in endpoint_config['azure_managed_endpoint']:
    if 'ENDPOINT_NAME' in elem and 'ENV_NAME' in elem:
        if environment_name == elem['ENV_NAME']:
            endpoint_name = elem["ENDPOINT_NAME"]
            deployment_name = elem["CURRENT_DEPLOYMENT_NAME"]
            test_model_file = elem["TEST_FILE_PATH"]

            endpoint_url = ml_client.online_endpoints.get(name=endpoint_name).scoring_uri
            api_key = ml_client.online_endpoints.get_keys(name=endpoint_name).primary_key

            request_result = ml_client.online_endpoints.invoke(
                endpoint_name=endpoint_name,
                deployment_name=deployment_name,
                request_file=test_model_file,
            )

            print(request_result)