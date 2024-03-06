from dotenv import load_dotenv 
load_dotenv()  

from prompt_experimentation.run_local import LocalFlowExecution

def main():
    data = "../named_entity_recognition/data/data.jsonl"
    flow = "../named_entity_recognition/flows/standard"
    eval_flow = "../named_entity_recognition/flows/evaluation"
    named_entity_flow = LocalFlowExecution(flow, eval_flow, data, {"text": "${data.text}", "entity_type": "${data.entity_type}"})
    named_entity_flow.process_local_flow()
    #named_entity_flow.create_local_connections()
    run_ids = named_entity_flow.execute_experiment()

    named_entity_flow.execute_evaluation(run_ids,data,{
                "ground_truth": "${data.results}",
                "entities": "${run.outputs.entities}",
            })

if __name__ == "__main__":
    main()