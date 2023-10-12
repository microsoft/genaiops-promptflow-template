import json
import yaml
import datetime
import ast
from promptflow.entities import Run
from azure.identity import DefaultAzureCredential
from promptflow.azure import PFClient
import argparse
from promptflow.entities import AzureOpenAIConnection
import pandas as pd

def prepare_and_execute(subscription_id,
        resource_group_name,
        workspace_name,
        runtime,
        build_id,
        standard_flow_path,
        eval_flow_path,
        stage,
        experiment_name,
        data_config_path,
        run_id,
        data_purpose,
        data_mapping_config
    ):

    eval_flows = eval_flow_path.split(",")

    pf = PFClient(DefaultAzureCredential(),subscription_id,resource_group_name,workspace_name)

    standard_flow = standard_flow_path
    dataset_name = []
    config_file = open(data_config_path)
    data_config = json.load(config_file)
    for elem in data_config['datasets']:
        if 'DATA_PURPOSE' in elem and 'ENV_NAME' in elem:
            if stage == elem['ENV_NAME'] and data_purpose == elem['DATA_PURPOSE']:
                data_name = elem["DATASET_NAME"]
                related_data = elem["RELATED_EXP_DATASET"]
                data = pf.ml_client.data.get(name=data_name,label='latest')
                data_id = f"azureml:{data.name}:{data.version}" # added
                dataset_name.append({
                    "data_id": data_id,
                    "ref_data":  related_data
                })

    print(dataset_name) # added
    standard_flow_file = f"{standard_flow}/flow.dag.yaml"

    with open(standard_flow_file, "r") as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)

    default_variants = []
    for node_name, node_data in yaml_data.get("node_variants", {}).items():
        node_variant_mapping = {}
        default_variant = node_data['default_variant_id']
        node_variant_mapping[node_name] = default_variant
        default_variants.append(node_variant_mapping)

    mapping_file = open(data_mapping_config)
    mapping_config = json.load(mapping_file)
    eval_config_node = mapping_config['evaluation']

    all_eval_df = []
    all_eval_metrics = []

    run_ids = ast.literal_eval(run_id)

    for flow in eval_flows:
        dataframes = []
        metrics = []

        flow_name = (flow.split('/')[-1]).strip()
        mapping_node = eval_config_node[flow_name]
        for flow_run in run_ids:
            my_run = pf.runs.get(flow_run)
            run_data_id = my_run.data.replace("azureml:", "")
            run_data_id = run_data_id.split(":")[0]
            for data_item in dataset_name:
                data_n = data_item['data_id']
                ref_data = data_item['ref_data']
                if ref_data == run_data_id:
                    data_id = data_n
                    break


            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            print(flow)

            eval_run = Run(
                flow=flow.strip(),
                data=data_id, 
                run=my_run, 
                column_mapping=mapping_node, 
                runtime=runtime,
                name=f"{experiment_name}_eval_{timestamp}",
                display_name=f"{experiment_name}_eval_{timestamp}",
                tags={"build_id": build_id},
            )
            eval_run._experiment_name = experiment_name
            eval_job = pf.runs.create_or_update(eval_run, stream=True)
            df_result = None
                
            if eval_job.status == "Completed" or eval_job.status == "Finished": # 4
                print(eval_job.status)
                df_result = pf.get_details(eval_job)
                metric_variant = pf.get_metrics(eval_job)

                if my_run.properties.get('azureml.promptflow.node_variant', None) is not None:
                    variant_id = my_run.properties['azureml.promptflow.node_variant']
                    start_index = variant_id.find('{') + 1
                    end_index = variant_id.find('}')
                    variant_value = variant_id[start_index:end_index].split(".")
                        
                    df_result[variant_value[0]] = variant_value[1]
                    metric_variant[variant_value[0]] = variant_value[1]
                    df_result["dataset"] = data_id
                    metric_variant["dataset"] = data_id

                    for var in default_variants:
                        for key in var.keys():
                            if key == variant_value[0]:
                                pass
                            else:
                                df_result[key] = var[key]
                                metric_variant[key] = var[key]
                    
                dataframes.append(df_result)
                metrics.append(metric_variant)
                
                print(json.dumps(metrics, indent=4))
                print(df_result.head(10))

            else:
                raise Exception("Sorry, exiting job with failure..")

        combined_results_df = pd.concat(dataframes, ignore_index=True)
        combined_metrics_df = pd.DataFrame(metrics)
        combined_results_df["flow_name"] =  flow_name
        combined_metrics_df["flow_name"] =  flow_name
        combined_results_df["exp_run"] =  flow_run
        combined_metrics_df["exp_run"] =  flow_run

        combined_results_df.to_csv(f"./reports/{run_data_id}_result.csv")
        combined_metrics_df.to_csv(f"./reports/{run_data_id}_metrics.csv")
            
        styled_df = combined_results_df.to_html(index=False)

        with open(f'reports/{run_data_id}_result.html', 'w') as f:
            f.write(styled_df)
            
        html_table_metrics = combined_metrics_df.to_html(index=False)
        with open(f'reports/{run_data_id}_metrics.html', 'w') as f:
            f.write(html_table_metrics)

        all_eval_df.append(combined_results_df) 
        all_eval_metrics.append(combined_metrics_df)
        
    final_results_df = pd.concat(all_eval_df, ignore_index=True)
    final_metrics_df = pd.concat(all_eval_metrics, ignore_index=True)
    final_results_df["stage"] = stage
    final_results_df["experiment_name"] = experiment_name
    final_results_df["build"] = build_id

    final_results_df.to_csv(f"./reports/{experiment_name}_result.csv")
    final_metrics_df.to_csv(f"./reports/{experiment_name}_metrics.csv")
            
    styled_df = final_results_df.to_html(index=False)
    with open(f'reports/{experiment_name}_result.html', 'w') as f:
        f.write(styled_df)
            
    html_table_metrics = final_metrics_df.to_html(index=False)
    with open(f'reports/{experiment_name}_metrics.html', 'w') as f:
        f.write(html_table_metrics)


def column_widths(column):
    max_length = max(column.astype(str).apply(len))
    return f'width: {max_length}em;'

def main():
    parser = argparse.ArgumentParser("prompt_exprimentation")
    parser.add_argument("--subscription_id", type=str, help="Azure subscription id")
    parser.add_argument(
        "--resource_group_name", type=str, help="Azure Machine learning resource group"
    )
    parser.add_argument(
        "--workspace_name", type=str, help="Azure Machine learning Workspace name"
    )
    parser.add_argument(
        "--runtime_name", type=str, help="prompt flow runtime time"
    )
    parser.add_argument(
        "--build_id",
        type=str,
        help="Unique identifier for Azure DevOps pipeline run",
    )
    parser.add_argument(
        "--stage",
        type=str,
        help="execution and deployment environment. e.g. dev, prod, test",
    )
    parser.add_argument(
        "--experiment_name", type=str, help="Job execution experiment name"
    )
    parser.add_argument(
        "--standard_flow_path", type=str, help="Job execution experiment name"
    )
    parser.add_argument(
        "--eval_flow_path", type=str, help="Job execution experiment name"
    )

    parser.add_argument("--data_purpose", type=str, help="data to be registered identified by purpose", required=True)

    parser.add_argument("--data_config_path", type=str, required=True, help="data config path")
    parser.add_argument("--run_id", type=str, required=True, help="run ids")
    parser.add_argument("--data_mapping_config", type=str, required=True, help="data mapping config")

    args = parser.parse_args()

    prepare_and_execute(
        args.subscription_id,
        args.resource_group_name,
        args.workspace_name,
        args.runtime_name,
        args.build_id,
        args.standard_flow_path,
        args.eval_flow_path,
        args.stage,
        args.experiment_name,
        args.data_config_path,
        args.run_id,
        args.data_purpose,
        args.data_mapping_config
    )


if __name__ ==  '__main__':
      main()
