import json
import yaml
import datetime
import time
from promptflow.entities import Run
from azure.identity import DefaultAzureCredential
from azure.ai.ml import MLClient
from promptflow.azure import PFClient
import argparse
from promptflow.entities import AzureOpenAIConnection


def are_dictionaries_similar(dict1, old_runs):
    for old_run in old_runs:
        set1 = {frozenset(dict(old_run).items()) }
        set2 = {frozenset(dict1.items()) }
        if set1 == set2:
            return True
    
    return False

def prepare_and_execute(
        subscription_id,
        build_id,
        model_type,
        stage,
        output_file,
        data_purpose,
    ):

    main_config = open(f"{model_type}/config.json")
    model_config = json.load(main_config)

    for obj in model_config["envs"]:
        if obj.get("ENV_NAME") == stage:
            config = obj
            break

    resource_group_name = config["RESOURCE_GROUP_NAME"]
    workspace_name = config["WORKSPACE_NAME"]
    data_mapping_config= f"{model_type}/configs/mapping_config.json"
    standard_flow_path= config["STANDARD_FLOW_PATH"]
    data_config_path= f"{model_type}/configs/data_config.json"
    connection_name= config["CONNECTION_NAME"]
    deployment_name= config["DEPLOYMENT_NAME"]
    runtime= config["RUNTIME_NAME"]
    experiment_name = f"{model_type}_{stage}"

    ml_client = MLClient(DefaultAzureCredential(),subscription_id,resource_group_name,workspace_name)

    pf = PFClient(DefaultAzureCredential(),subscription_id,resource_group_name,workspace_name)
    print(data_mapping_config)
    flow = f"{model_type}/{standard_flow_path}" 
    dataset_name = []
    config_file = open(data_config_path)
    data_config = json.load(config_file)
    for elem in data_config['datasets']:
        if 'DATA_PURPOSE' in elem and 'ENV_NAME' in elem:
            if stage == elem['ENV_NAME'] and data_purpose == elem['DATA_PURPOSE']:
                data_name = elem["DATASET_NAME"]
                data = ml_client.data.get(name=data_name,label='latest')
                data_id = f"azureml:{data.name}:{data.version}" 
                dataset_name.append(data_id)
    print(dataset_name) 
    flow_file = f"{flow}/flow.dag.yaml"

    with open(flow_file, "r") as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)
    all_variants = []
    all_llm_nodes = set()
    default_variants = {}
    for node_name, node_data in yaml_data.get("node_variants", {}).items():
        node_variant_mapping = {}
        variants = node_data.get("variants", {})
        default_variant = node_data['default_variant_id']
        default_variants[node_name] = default_variant
        for variant_name, variant_data in variants.items():
            node_variant_mapping[variant_name] = node_name
            all_llm_nodes.add(node_name)
        all_variants.append(node_variant_mapping)

    for nodes in yaml_data["nodes"]:
        node_variant_mapping = {}
        if nodes.get("type",{}) == 'llm':
            all_llm_nodes.add(nodes['name'])

    connections = {}
    for node in all_llm_nodes:
        connections[node] = {
            "connection": connection_name,
            "deployment_name": deployment_name
        }

    mapping_file = open(data_mapping_config)
    mapping_config = json.load(mapping_file)
    exp_config_node = mapping_config['experiment']


    run_ids = []
    past_runs = []

    for data_id in dataset_name:
        data_ref = data_id.replace("azureml:", "")
        data_ref = data_ref.split(":")[0]
        if len(all_variants) != 0:
            for variant in all_variants:
                for variant_id, node_id in variant.items():
                    variant_string = f"${{{node_id}.{variant_id}}}"
                    print(variant_string)

                    get_current_defaults = {key: value for key, value in default_variants.items() if key != node_id or value != variant_id}
                    get_current_defaults[node_id] = variant_id
                    get_current_defaults['dataset'] = data_ref
                    print(get_current_defaults)
                    if len(past_runs) == 0 or are_dictionaries_similar(get_current_defaults, past_runs) == False: 
                        past_runs.append(get_current_defaults)
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        run = Run( 
                            flow=flow,
                            data=data_id,
                            runtime=runtime,
                            #resources={'instance_type': "Standard_E4ds_v4"},
                            variant=variant_string,
                            name=f"{experiment_name}_{variant_id}_{timestamp}_{data_ref}",
                            display_name=f"{experiment_name}_{variant_id}_{timestamp}_{data_ref}",
                            environment_variables={
                                "key1": "value1"
                            },
                            column_mapping=exp_config_node,
                            # connections=connections,
                            tags={"build_id": build_id},
                        )

                        pipeline_job = pf.runs.create_or_update(run,stream=True)
                        run_ids.append(pipeline_job.name)

                        df_result = None
                        time.sleep(15)
                        if pipeline_job.status == "Completed" or pipeline_job.status == "Finished": # 4
                            print("job completed")
                            df_result = pf.get_details(pipeline_job)
                            run_details = pf.runs.get_metrics(pipeline_job.name)
                            print(df_result.head(10))
                            print("done")
                        else:
                            raise Exception("Sorry, exiting job with failure..")
        else:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            run = Run( 
                flow=flow,
                data=data_id,
                runtime=runtime,
                #resources={'instance_type': "Standard_E4ds_v4"},
                name=f"{experiment_name}_{timestamp}_{data_ref}",
                display_name=f"{experiment_name}_{timestamp}_{data_ref}",
                environment_variables={
                    "key1": "value1"
                },
                column_mapping=exp_config_node,
                tags={"build_id": build_id},
                #connections=connections
            )
            run._experiment_name = experiment_name
            pipeline_job = pf.runs.create_or_update(run, stream=True)
            run_ids.append(pipeline_job.name)

            df_result = None
            time.sleep(15)
            if pipeline_job.status == "Completed" or pipeline_job.status == "Finished": # 4
                print("job completed")
                df_result = pf.get_details(pipeline_job)
                run_details = pf.runs.get_metrics(pipeline_job.name)
                print(df_result.head(10))
                print("done")
            else:
                raise Exception("Sorry, exiting job with failure..")

    if output_file is not None:
        with open(output_file, "w") as out_file:
            out_file.write(str(run_ids))
    print(str(run_ids))

def main():
    parser = argparse.ArgumentParser("prompt_bulk_run")
    parser.add_argument("--subscription_id", type=str, help="Azure subscription id")
    parser.add_argument(
        "--build_id",
        type=str,
        help="Unique identifier for build execution",
    )
    parser.add_argument(
        "--stage",
        type=str,
        help="execution and deployment environment. e.g. dev, prod, test",
    )
    parser.add_argument(
        "--data_purpose", type=str, help="data identified by purpose"
    )
    parser.add_argument(
        "--output_file", type=str, required=False, help="A file to save run ids"
    )
    parser.add_argument("--model_type", type=str, help="use case name", required=True)
    args = parser.parse_args()

    prepare_and_execute(
        args.subscription_id,
        args.build_id,
        args.model_type,
        args.stage,
        args.output_file,
        args.data_purpose,
    )


if __name__ ==  '__main__':
      main()
