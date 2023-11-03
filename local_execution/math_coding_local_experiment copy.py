
from dotenv import load_dotenv 
load_dotenv()  

from prompt_experimentation.run_local import LocalFlowExecution

def main():
    data = "math_coding/data/test_data.jsonl"
    flow = "math_coding/flows/math_standard_flow"
    eval_flow = "math_coding/flows/math_evaluation_flow"
    math_coding_flow = LocalFlowExecution(flow, eval_flow, data, {"math_question": "${data.question}"})
    math_coding_flow.process_local_flow()
    math_coding_flow.create_local_connections()
    run_ids = math_coding_flow.execute_experiment()

    math_coding_flow.execute_evaluation(run_ids,data,{
            "groundtruth": "${data.groundtruth}",
            "prediction": "${run.outputs.answer}"
            })

if __name__ == "__main__":
    main()