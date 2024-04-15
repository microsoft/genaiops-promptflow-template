from dotenv import load_dotenv 
load_dotenv()  

from prompt_experimentation.run_local import LocalFlowExecution

def main():
    data = "set_chatbot/data/data.jsonl"
    flow = "set_chatbot/flows/standard"
    eval_flow = "set_chatbot/flows/evaluation"
    named_entity_flow = LocalFlowExecution(flow, eval_flow, data, {"query": "${data.question}", "chat_history": "${data.chat_history}"})
    named_entity_flow.process_local_flow()
    named_entity_flow.create_local_connections()
    run_ids = named_entity_flow.execute_experiment()

    named_entity_flow.execute_evaluation(run_ids,data,{
                "ground_truth": "${data.truth}",
                "answer": "${run.outputs.reply}",
            })

if __name__ == "__main__":
    main()