
from dotenv import load_dotenv 
load_dotenv()  

from prompt_experimentation.run_local import LocalFlowExecution

def main():
    data = "web_classification/data/data.jsonl"
    flow = "web_classification/flows/experiment"
    eval_flow = "web_classification/flows/evaluation"
    json_converter_flow = LocalFlowExecution(flow, eval_flow, data, {"url": "${data.url}"})
    json_converter_flow.process_local_flow()
    json_converter_flow.create_local_connections()
    run_ids = json_converter_flow.execute_experiment()

    json_converter_flow.execute_evaluation(run_ids,data,{
            "groundtruth": "${data.answer}",
            "prediction": "${run.outputs.category}"
            })

if __name__ == "__main__":
    main()