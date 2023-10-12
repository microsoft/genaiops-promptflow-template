

from prompt_experimentation.run_on_azure import AzureFlowExecution

def main():
    data = "flows/web_classification/data/data.jsonl"
    flow = "flows/web_classification/flows/experiment"
    eval_flow = "flows/web_classification/flows/evaluation"
    web_classification_flow = AzureFlowExecution(flow, eval_flow, data, {"url": "${data.url}"})
    web_classification_flow.process_azure_flow()
    run_ids = web_classification_flow.execute_experiment()

    web_classification_flow.execute_evaluation(run_ids,data,{
            "groundtruth": "${data.answer}",
            "prediction": "${run.outputs.category}"
            })

if __name__ == "__main__":
    main()