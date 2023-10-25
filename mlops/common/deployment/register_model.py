
import argparse
import shutil
import os
import json
from azure.ai.ml import MLClient
from azure.ai.ml.entities import Model
from azure.identity import DefaultAzureCredential

parser = argparse.ArgumentParser("register Model")
parser.add_argument("--subscription_id", type=str, help="Azure subscription id", required=True)
parser.add_argument("--build_id", type=str, help="Azure DevOps build id for deployment", required=True)
parser.add_argument("--env_type", type=str, help="env name (dev, test, prod) for deployment", required=True)
parser.add_argument("--model_type", type=str, help="model type")
parser.add_argument("--output_file", type=str, required=False, help="A file to save run model version")

args = parser.parse_args()



stage = args.env_type
model_type = args.model_type
model_name = f"{model_type}_{stage}"
build_id = args.build_id
output_file = args.output_file

main_config = open(f"{model_type}/config.json")
model_config = json.load(main_config)

for obj in model_config["envs"]:
    if obj.get("ENV_NAME") == stage:
        config = obj
        break

resource_group_name = config["RESOURCE_GROUP_NAME"]
workspace_name = config["WORKSPACE_NAME"]
model_path= config["STANDARD_FLOW_PATH"]

print(f"Model name: {model_name}")



if os.path.exists(f"{model_type}/flow.dag.yaml"): 
    file_to_replace = "flow.dag.yaml"
    source_path = os.path.join(os.getcwd(), f"{model_type}/flow.dag.yaml")
    destination_path = os.path.join(os.getcwd(), model_path, file_to_replace)
    shutil.copy(source_path, destination_path)

ml_client = MLClient(
    DefaultAzureCredential(), args.subscription_id, resource_group_name, workspace_name
)

model = Model(
    name = model_name,
    path = f"{model_type}/{model_path}",
    stage = "Production",
    description = f"{model_type} model registered for prompt flow deployment",
    properties={
        "azureml.promptflow.source_flow_id": model_type
    },
    tags={"build_id": build_id}

)

model_info = ml_client.models.create_or_update(model)

if output_file is not None:
    with open(output_file, "w") as out_file:
        out_file.write(str(model_info.version))



