
from dotenv import load_dotenv 
load_dotenv()  

from local_execution.prompt_experimentation.run_local import LocalFlowExecution
from llmops.common.config_utils import LLMOpsConfig

def main():
    config = LLMOpsConfig("math_coding")
    connections_config = config.connections    
    data = "web_classification/data/data.jsonl"
    flow = "web_classification/flows/experiment"
    eval_flow = "web_classification/flows/evaluation"
    web_classification_flow = LocalFlowExecution(flow, eval_flow, data, {"url": "${data.url}"}, connections_config)
    web_classification_flow.process_local_flow()
    web_classification_flow.create_local_connections()
    run_ids = web_classification_flow.execute_experiment()

    web_classification_flow.execute_evaluation(run_ids,data,{
            "groundtruth": "${data.answer}",
            "prediction": "${run.outputs.category}"
            })

if __name__ == "__main__":
    main()