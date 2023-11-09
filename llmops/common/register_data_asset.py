from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential
import argparse
from azure.ai.ml.entities import Data
from azure.ai.ml.constants import AssetTypes
import json

parser = argparse.ArgumentParser("register data assets")
parser.add_argument("--subscription_id", type=str, help="Azure subscription id", required=True)
parser.add_argument("--data_purpose", type=str, help="data to be registered identified by purpose", required=True)
parser.add_argument("--flow_to_execute", type=str, help="data config file path", required=True)
parser.add_argument("--env_name",type=str,help="environment name (e.g. dev, test, prod)", required=True)
 
args = parser.parse_args()

stage = args.env_name
main_config = open(f"{args.flow_to_execute}/config.json")
config = json.load(main_config)

for obj in config["envs"]:
    if obj.get("ENV_NAME") == stage:
        model_config = obj
        break

data_config_path = f"{args.flow_to_execute}/configs/data_config.json"
resource_group_name = model_config["RESOURCE_GROUP_NAME"]
workspace_name= model_config["WORKSPACE_NAME"]
data_purpose = args.data_purpose


ml_client = MLClient(
    DefaultAzureCredential(), args.subscription_id, resource_group_name, workspace_name
)

config_file = open(data_config_path)
data_config = json.load(config_file)
#csv_file_path = 'output.csv'
for elem in data_config['datasets']:
    if 'DATA_PURPOSE' in elem and 'ENV_NAME' in elem:
        if data_purpose == elem["DATA_PURPOSE"] and stage == elem['ENV_NAME']:
            data_path = f"{args.flow_to_execute}/{elem['DATA_PATH']}"
            dataset_desc = elem["DATASET_DESC"]
            dataset_name = elem["DATASET_NAME"]

            aml_dataset = Data(
                path=data_path,
                type=AssetTypes.URI_FILE,
                description=dataset_desc,
                name=dataset_name,
            )
            ml_client.data.create_or_update(aml_dataset)

            aml_dataset_unlabeled = ml_client.data.get(name=dataset_name, label="latest")

            print(aml_dataset_unlabeled.latest_version)
            print(aml_dataset_unlabeled.id)