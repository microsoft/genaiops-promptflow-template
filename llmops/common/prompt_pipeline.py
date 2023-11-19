
import argparse
import datetime
import json
import os
import time
import yaml
import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.ai.ml import MLClient
from promptflow.entities import Run
from promptflow.azure import PFClient



def are_dictionaries_similar(dict1, old_runs):
    for old_run in old_runs:
        set1 = {frozenset(dict(old_run).items())}
        set2 = {frozenset(dict1.items())}
        if set1 == set2:
            return True

    return False


def prepare_and_execute(
    subscription_id,
    build_id,
    flow_to_execute,
    stage,
    output_file,
    data_purpose,
    save_output,
    save_metric,
):
    main_config = open(f"{flow_to_execute}/config.json")
    model_config = json.load(main_config)

    for obj in model_config["envs"]:
        if obj.get("ENV_NAME") == stage:
            config = obj
            break

    resource_group_name = config["RESOURCE_GROUP_NAME"]
    workspace_name = config["WORKSPACE_NAME"]
    data_mapping_config = f"{flow_to_execute}/configs/mapping_config.json"
    standard_flow_path = config["STANDARD_FLOW_PATH"]
    data_config_path = f"{flow_to_execute}/configs/data_config.json"

    runtime= config["RUNTIME_NAME"]
    experiment_name = f"{flow_to_execute}_{stage}"

    ml_client = MLClient(
        DefaultAzureCredential(), subscription_id, resource_group_name, workspace_name
    )

    pf = PFClient(
        DefaultAzureCredential(), subscription_id, resource_group_name, workspace_name
    )
    print(data_mapping_config)
    flow = f"{flow_to_execute}/{standard_flow_path}"
    dataset_name = []
    config_file = open(data_config_path)
    data_config = json.load(config_file)
    for elem in data_config["datasets"]:
        if "DATA_PURPOSE" in elem and "ENV_NAME" in elem:
            if stage == elem["ENV_NAME"] and data_purpose == elem["DATA_PURPOSE"]:
                data_name = elem["DATASET_NAME"]
                data = ml_client.data.get(name=data_name, label="latest")
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
        default_variant = node_data["default_variant_id"]
        default_variants[node_name] = default_variant
        for variant_name, variant_data in variants.items():
            node_variant_mapping[variant_name] = node_name
            all_llm_nodes.add(node_name)
        all_variants.append(node_variant_mapping)

    for nodes in yaml_data["nodes"]:
        node_variant_mapping = {}
        if nodes.get("type", {}) == "llm":
            all_llm_nodes.add(nodes["name"])

    mapping_file = open(data_mapping_config)
    mapping_config = json.load(mapping_file)
    exp_config_node = mapping_config["experiment"]

    run_ids = []
    past_runs = []
    all_eval_df = []
    all_eval_metrics = []

    for data_id in dataset_name:
        data_ref = data_id.replace("azureml:", "")
        data_ref = data_ref.split(":")[0]
        dataframes = []
        metrics = []

        if len(all_variants) != 0:
            for variant in all_variants:
                for variant_id, node_id in variant.items():
                    variant_string = f"${{{node_id}.{variant_id}}}"
                    print(variant_string)

                    get_current_defaults = {
                        key: value
                        for key, value in default_variants.items()
                        if key != node_id or value != variant_id
                    }
                    get_current_defaults[node_id] = variant_id
                    get_current_defaults["dataset"] = data_ref
                    print(get_current_defaults)

                    if (
                        len(past_runs) == 0
                        or are_dictionaries_similar(get_current_defaults, past_runs)
                        == False
                    ):
                        past_runs.append(get_current_defaults)
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        run = Run(
                            flow=flow,
                            data=data_id,
                            runtime=runtime,
                            # un-comment the resources line and comment the line related to runtime to enable automatic runtime. COMPUTE_RUNTIME
                            #resources={"instance_type": "Standard_E4ds_v4"},
                            variant=variant_string,
                            name=f"{experiment_name}_{variant_id}_{timestamp}_{data_ref}",
                            display_name=f"{experiment_name}_{variant_id}_{timestamp}_{data_ref}",
                            environment_variables={"key1": "value1"},
                            column_mapping=exp_config_node,
                            tags={"build_id": build_id},
                        )

                        pipeline_job = pf.runs.create_or_update(run, stream=True)
                        run_ids.append(pipeline_job.name)
                        df_result = None
                        time.sleep(15)
                        if (
                            pipeline_job.status == "Completed"
                            or pipeline_job.status == "Finished"
                        ):
                            print("job completed")
                            df_result = pf.get_details(pipeline_job)
                            if save_output:
                                dataframes.append(df_result)
                            if save_metric:
                                metric_variant = pf.get_metrics(pipeline_job)
                                metric_variant[variant_id] = variant_string
                                metric_variant["dataset"] = data_id
                                metrics.append(metric_variant)
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
                # un-comment the resources line and comment the line related to runtime to enable automatic runtime. COMPUTE_RUNTIME
                #resources={"instance_type": "Standard_E4ds_v4"},
                name=f"{experiment_name}_{timestamp}_{data_ref}",
                display_name=f"{experiment_name}_{timestamp}_{data_ref}",
                environment_variables={"key1": "value1"},
                column_mapping=exp_config_node,
                tags={"build_id": build_id},
            )
            run._experiment_name = experiment_name
            pipeline_job = pf.runs.create_or_update(run, stream=True)
            run_ids.append(pipeline_job.name)
            time.sleep(15)
            df_result = None
            if (
                pipeline_job.status == "Completed" or pipeline_job.status == "Finished"
            ):  # 4
                print("job completed")
                df_result = pf.get_details(pipeline_job)
                if save_output:
                    dataframes.append(df_result)
                if save_metric:
                    metric_variant = pf.get_metrics(pipeline_job)
                    metric_variant["dataset"] = data_id
                    metrics.append(metric_variant)
                print(df_result.head(10))
            else:
                raise Exception("Sorry, exiting job with failure..")

        if (save_output or save_metric) and not os.path.exists("./reports"):
            os.makedirs("./reports")

        if save_output:
            combined_results_df = pd.concat(dataframes, ignore_index=True)
            combined_results_df.to_csv(f"./reports/{data_ref}_result.csv")
            styled_df = combined_results_df.to_html(index=False)
            with open(f"reports/{data_ref}_result.html", "w") as combined_results:
                combined_results.write(styled_df)
            all_eval_df.append(combined_results_df)
        if save_metric:
            combined_metrics_df = pd.DataFrame(metrics)
            combined_metrics_df.to_csv(f"./reports/{data_ref}_metrics.csv")
            html_table_metrics = combined_metrics_df.to_html(index=False)
            with open(f"reports/{data_ref}_metrics.html", "w") as combined_metrics:
                combined_metrics.write(html_table_metrics)
            all_eval_metrics.append(combined_metrics_df)

    if output_file is not None:
        with open(output_file, "w") as out_file:
            out_file.write(str(run_ids))
    print(str(run_ids))

    if save_output:
        final_results_df = pd.concat(all_eval_df, ignore_index=True)
        final_results_df["stage"] = stage
        final_results_df["experiment_name"] = experiment_name
        final_results_df["build"] = build_id
        final_results_df.to_csv(f"./reports/{experiment_name}_result.csv")
        styled_df = final_results_df.to_html(index=False)
        with open(f"reports/{experiment_name}_result.html", "w") as final_results:
            final_results.write(styled_df)
        print("Saved the results in files in reports folder")
    if save_metric:
        final_metrics_df = pd.concat(all_eval_metrics, ignore_index=True)
        final_metrics_df.to_csv(f"./reports/{experiment_name}_metrics.csv")
        html_table_metrics = final_metrics_df.to_html(index=False)
        with open(f"reports/{experiment_name}_metrics.html", "w") as final_metrics:
            final_metrics.write(html_table_metrics)
        print("Saved the metrics in files in reports folder")

def main():
    parser = argparse.ArgumentParser("prompt_bulk_run")
    parser.add_argument(
        "--subscription_id",
        type=str,
        help="Azure subscription id",
        required=True,
    )
    parser.add_argument(
        "--build_id",
        type=str,
        help="Unique identifier for build execution",
        required=True,
    )
    parser.add_argument(
        "--env_name",
        type=str,
        help="environment name (dev, test, prod) for execution and deployment",
        required=True,
    )
    parser.add_argument(
        "--data_purpose", type=str, help="data identified by purpose", required=True
    )
    parser.add_argument(
        "--output_file", type=str, required=True, help="A file to save run ids"
    )
    parser.add_argument(
        "--flow_to_execute", type=str, help="flow use case name", required=True
    )
    parser.add_argument(
        "--save_output", help="Save the outputs in files", required=False, action='store_true'
    )
    parser.add_argument(
        "--save_metric", help="Save the metrics in files", required=False, action='store_true'
    )
    args = parser.parse_args()

    prepare_and_execute(
        args.subscription_id,
        args.build_id,
        args.flow_to_execute,
        args.env_name,
        args.output_file,
        args.data_purpose,
        args.save_output,
        args.save_metric,
    )


if __name__ == "__main__":
    main()
