
import argparse
import shutil
import os
import json
from azure.ai.ml import MLClient
from azure.ai.ml.entities import Model
from azure.identity import DefaultAzureCredential

parser = argparse.ArgumentParser("register Model")
parser.add_argument("--subscription_id", type=str, help="Azure subscription id", required=True)
parser.add_argument("--build_id", type=str, help="build id for deployment", required=True)
parser.add_argument("--env_type", type=str, help="env name (dev, test, prod) for deployment", required=True)
parser.add_argument("--flow_to_execute", type=str, help="use case name")
parser.add_argument("--output_file", type=str, required=False, help="A file to save run model version")

args = parser.parse_args()



stage = args.env_type
flow_to_execute = args.flow_to_execute
model_name = f"{flow_to_execute}_{stage}"
build_id = args.build_id
output_file = args.output_file

main_config = open(f"{flow_to_execute}/config.json")
model_config = json.load(main_config)

for obj in model_config["envs"]:
    if obj.get("ENV_NAME") == stage:
        config = obj
        break

resource_group_name = config["RESOURCE_GROUP_NAME"]
workspace_name = config["WORKSPACE_NAME"]
model_path= config["STANDARD_FLOW_PATH"]

print(f"Model name: {model_name}")



if os.path.exists(f"{flow_to_execute}/flow.dag.yaml"): 
    file_to_replace = "flow.dag.yaml"
    source_path = os.path.join(os.getcwd(), f"{flow_to_execute}/flow.dag.yaml")
    destination_path = os.path.join(os.getcwd(), model_path, file_to_replace)
    shutil.copy(source_path, destination_path)

ml_client = MLClient(
    DefaultAzureCredential(), args.subscription_id, resource_group_name, workspace_name
)

model = Model(
    name = model_name,
    path = f"{flow_to_execute}/{model_path}",
    stage = "Production",
    description = f"{flow_to_execute} model registered for prompt flow deployment",
    properties={
        "azureml.promptflow.source_flow_id": flow_to_execute
    },
    tags={"build_id": build_id}

)

model_info = ml_client.models.create_or_update(model)

if output_file is not None:
    with open(output_file, "w") as out_file:
        out_file.write(str(model_info.version))



