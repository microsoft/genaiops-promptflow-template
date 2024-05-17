import json
import yaml
import datetime
import os
import pandas as pd


from promptflow.entities import Run
from promptflow.entities import AzureOpenAIConnection
from promptflow import PFClient

def are_dictionaries_similar(dict1, old_runs):
    for old_run in old_runs:
        set1 = {frozenset(dict(old_run).items()) }
        set2 = {frozenset(dict1.items()) }
        if set1 == set2:
            return True
    
    return False

def find_dictionary_by_value(key, value, list_of_dictionaries):
    for element in list_of_dictionaries:
        if element[key] == value:
            return element

def column_widths(column):
    max_length = max(column.astype(str).apply(len))
    return f'width: {max_length}em;'

class LocalFlowExecution:
    def __init__(self,
                exp_flow_path,
                eval_flow_path,
                data_path,
                column_mapping,
                connections_config
            ):

        self.exp_flow_path = exp_flow_path
        self.eval_flow_path = eval_flow_path
        self.data_path = data_path
        self.column_mapping = column_mapping
        self.connections_config = connections_config

        self.local_pf_client = PFClient()

    def process_local_flow(self):

        all_variants = []
        all_llm_nodes = set()
        all_connection_nodes = []
        default_variants = {}
        llm_connections = []
        connections = {}

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
                    
                connection_node  ={}
                connection_node["node_name"] = node_name
                connection_node["variant_id"] = variant_name
                connection_node["connection_name"] = variant_data["node"]["connection"]
                connection_node["deployment_name"] = variant_data["node"]["inputs"]["deployment_name"]
                connection_node["provider"] = variant_data["node"]["provider"]
                all_connection_nodes.append(connection_node)
                    
                all_llm_nodes.add(node_name)
            all_variants.append(node_variant_mapping)

        for nodes in yaml_data["nodes"]:
            node_variant_mapping = {}
            if nodes.get("type",{}) == 'llm':
                all_llm_nodes.add(nodes['name'])
                    
                connection_node  ={}
                connection_node["node_name"] = nodes["name"]
                connection_node["variant_id"] = ""
                connection_node["connection_name"] = nodes["connection"]
                connection_node["provider"] = nodes["provider"]
                connection_node["deployment_name"] = nodes["inputs"]["deployment_name"]
                all_connection_nodes.append(connection_node)

        
        for llm_con in all_connection_nodes:
            connections[llm_con["node_name"]] = {
                "connection": llm_con["connection_name"],
                "deployment_name": llm_con["deployment_name"]
            }
            print(all_connection_nodes)
            llm_connection = {}
            connection_config = find_dictionary_by_value('connection', llm_con["connection_name"], self.connections_config)
            print(connection_config)
            llm_connection["name"] = llm_con["connection_name"]
            llm_connection["provider"] = llm_con["provider"]
            llm_connection["api_key"] = connection_config["api_key"]
            llm_connection["api_base"] = connection_config["api_base"]
            llm_connection["api_type"] = connection_config["api_type"]
            llm_connection["api_version"] = connection_config["api_version"]
            llm_connections.append(llm_connection)

        self.all_variants = all_variants
        self.all_llm_nodes = all_llm_nodes
        self.all_connection_nodes = all_connection_nodes
        self.default_variants = default_variants
        self.llm_connections = llm_connections
        self.connections = connections    

    def create_local_connections(self):
        for local_connection in self.llm_connections:
            if local_connection["provider"] == "AzureOpenAI":
                connection = AzureOpenAIConnection(
                    name=local_connection["name"],
                    api_key=local_connection["api_key"],
                    api_base=local_connection["api_base"],
                    api_type=local_connection["api_type"],
                    api_version=local_connection["api_version"],
                )
                conn = self.local_pf_client.connections.create_or_update(connection)
                print(f"successfully created connection..{conn}")

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
                        base_run = self.local_pf_client.run(flow=self.exp_flow_path, 
                            data=self.data_path,
                            column_mapping=self.column_mapping,
                            variant=variant_string,
                            connections=self.connections,
                            name=f"{os.environ['experiment_name']}_{node_id}_{variant_id}_{timestamp}",
                            display_name=f"{os.environ['experiment_name']}_{node_id}_{variant_id}_{timestamp}", 
                            stream=True
                        )
                        run_ids.append(base_run.name)

                        df_result = None
                        
                        if base_run.status == "Completed" or base_run.status == "Finished": # 4
                                print("job completed")
                                df_result = self.local_pf_client.get_details(base_run)
                                run_details = self.local_pf_client.runs.get_metrics(base_run.name)
                                print(df_result.head(10))
                                print("done")
                        else:
                            raise Exception("Sorry, exiting job with failure..")
        else:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            base_run = self.local_pf_client.run( 
                flow=self.exp_flow_path,
                data=self.data_path,
                column_mapping=self.column_mapping,
                name=f"{os.environ['experiment_name']}_{timestamp}",
                display_name=f"{os.environ['experiment_name']}_{timestamp}", 
                stream=True
            )
            run_ids.append(base_run.name)

            df_result = None

            if base_run.status == "Completed" or base_run.status == "Finished": # 4
                print("job completed")
                df_result = self.local_pf_client.get_details(base_run)
                run_details = self.local_pf_client.runs.get_metrics(base_run.name)
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
            my_run = self.local_pf_client.runs.get(flow_run)

            eval_job = self.local_pf_client.run(
                flow=self.eval_flow_path,
                data=data_path, 
                run=my_run, 
                column_mapping=col_mapping,
                stream=True, 
            )
            df_result = None
            print(my_run.properties)
            
            if eval_job.status == "Completed" or eval_job.status == "Finished": # 4
                print(eval_job.status)
                df_result = self.local_pf_client.get_details(eval_job)
                metric_variant = self.local_pf_client.get_metrics(eval_job)

                if my_run.properties.get('node_variant', None) is not None:
                    variant_id = my_run.properties['node_variant']
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
