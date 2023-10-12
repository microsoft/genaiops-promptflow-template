

from prompt_experimentation.run_on_azure import AzureFlowExecution

def main():
    data = "flows/named_entity_recognition/data/data.jsonl"
    flow = "flows/named_entity_recognition/flows/standard"
    eval_flow = "flows/named_entity_recognition/flows/evaluation"
    named_entity_flow = AzureFlowExecution(flow, eval_flow, data, {"text": "${data.text}", "entity_type": "${data.entity_type}"})
    named_entity_flow.process_azure_flow()
    run_ids = named_entity_flow.execute_experiment()

    named_entity_flow.execute_evaluation(run_ids,data,{
                "ground_truth": "${data.results}",
                "entities": "${run.outputs.entities}"
            })

if __name__ == "__main__":
    main()