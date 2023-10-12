
import json
import yaml
import datetime
import os
import pandas as pd


from promptflow.entities import Run
from azure.identity import DefaultAzureCredential
from azure.ai.ml import MLClient
from promptflow.azure import PFClient 


def are_dictionaries_similar(dict1, old_runs):
    for old_run in old_runs:
        set1 = {frozenset(dict(old_run).items()) }
        set2 = {frozenset(dict1.items()) }
        if set1 == set2:
            return True
    
    return False

def column_widths(column):
    max_length = max(column.astype(str).apply(len))
    return f'width: {max_length}em;'

class AzureFlowExecution:
    def __init__(self,
                exp_flow_path,
                eval_flow_path,
                data_path,
                column_mapping
            ):
        self.subscription_id  = os.environ["subscription_id"]
        self.resource_group_name = os.environ["resource_group_name"]
        self.workspace_name = os.environ["workspace_name"]
        self.runtime_name = os.environ["runtime_name"]
        self.exp_flow_path = exp_flow_path
        self.eval_flow_path = eval_flow_path
        self.data_path  =  data_path
        self.column_mapping = column_mapping
        
        self.azure_pf_client = PFClient(DefaultAzureCredential(), os.environ['subscription_id'], os.environ['resource_group_name'],os.environ['workspace_name'])


    def process_azure_flow(self):
        all_variants = []
        all_llm_nodes = set()
        default_variants = {}

        flow_file = f"{self.exp_flow_path}/flow.dag.yaml"

        with open(flow_file, "r") as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)

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

        self.all_variants = all_variants
        self.all_llm_nodes = all_llm_nodes
        self.default_variants = default_variants

    def execute_experiment(self):
        run_ids = []
        past_runs = []
        if len(self.all_variants) != 0:
            for variant in self.all_variants:
                for variant_id, node_id in variant.items():
                    variant_string = f"${{{node_id}.{variant_id}}}" 
                    print(variant_string)
                    get_current_defaults = {key: value for key, value in self.default_variants.items() if key != node_id or value != variant_id}
                    get_current_defaults[node_id] = variant_id
                    if len(past_runs) == 0 or are_dictionaries_similar(get_current_defaults, past_runs) == False: 
                        past_runs.append(get_current_defaults)
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        
                        base_run = self.azure_pf_client.run(flow=self.exp_flow_path, 
                                data=self.data_path,
                                column_mapping=self.column_mapping,
                                variant=variant_string,
                                runtime=os.environ['runtime_name'],
                                name=f"{os.environ['experiment_name']}_{node_id}_{variant_id}_{timestamp}",
                                display_name=f"{os.environ['experiment_name']}_{node_id}_{variant_id}_{timestamp}", 

                                stream=True
                            )
                        run_ids.append(base_run.name)
                        base_run.run = base_run.name
                        base_run.variant = variant_string
                        df_result = None
                        
                        if base_run.status == "Completed" or base_run.status == "Finished": # 4
                                print("job completed")

                                df_result = self.azure_pf_client.get_details(base_run)
                                run_details = self.azure_pf_client.runs.get_metrics(base_run.name)
                                print(df_result.head(10))
                                print("done")
                        else:
                            raise Exception("Sorry, exiting job with failure..")
        else:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            base_run = self.azure_pf_client.run( 
                flow=self.exp_flow_path,
                data=self.data_path,
                column_mapping=self.column_mapping,
                runtime=os.environ['runtime_name'],
                name=f"{os.environ['experiment_name']}_{timestamp}",
                display_name=f"{os.environ['experiment_name']}_{timestamp}", 
                stream=True
            )
            run_ids.append(base_run.name)

            df_result = None

            if base_run.status == "Completed" or base_run.status == "Finished": # 4
                print("job completed")
                df_result = self.azure_pf_client.get_details(base_run)
                run_details = self.azure_pf_client.runs.get_metrics(base_run.name)
                print(df_result.head(10))
                print(run_details)
                print("done")
            else:
                raise Exception("Sorry, exiting job with failure..")

            print(str(run_ids))
            self.run_ids = run_ids
        return run_ids


    def execute_evaluation(self, run_ids, data_path, col_mapping):

        dataframes = []
        metrics = []

        for flow_run in run_ids:
            print(flow_run)
            my_run = self.azure_pf_client.runs.get(flow_run)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            eval_job = self.azure_pf_client.run(
                flow=self.eval_flow_path,
                data=data_path, 
                run=my_run, 
                column_mapping=col_mapping,
                runtime=os.environ['runtime_name'],
                name=f"{os.environ['experiment_name']}_eval_{timestamp}",
                display_name=f"{os.environ['experiment_name']}_eval_{timestamp}",
                stream=True, 
            )
            df_result = None
            print(my_run.properties)
            
            if eval_job.status == "Completed" or eval_job.status == "Finished": # 4
                print(eval_job.status)
                df_result = self.azure_pf_client.get_details(eval_job)
                metric_variant = self.azure_pf_client.get_metrics(eval_job)

                if my_run.properties.get('azureml.promptflow.node_variant', None) is not None:
                    variant_id = my_run.properties['azureml.promptflow.node_variant']
                    start_index = variant_id.find('{') + 1
                    end_index = variant_id.find('}')
                    variant_value = variant_id[start_index:end_index].split(".")
                        
                    df_result[variant_value[0]] = variant_value[1]
                    metric_variant[variant_value[0]] = variant_value[1]

                    for key, value in dict(self.default_variants).items():
                        if key == variant_value[0]:
                            pass
                        else:
                            df_result[key] = value
                            metric_variant[key] = value
                    
                dataframes.append(df_result)
                metrics.append(metric_variant)
                
                print(json.dumps(metrics, indent=4))
                print(df_result.head(10))

            else:
                raise Exception("Sorry, exiting job with failure..")

        combined_results_df = pd.concat(dataframes, ignore_index=True)
        combined_metrics_df = pd.DataFrame(metrics)

        print(combined_results_df)
        print(combined_metrics_df)  



