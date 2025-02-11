"""Executor node of the plan_and_execute flow."""

import concurrent.futures
import json
from promptflow.core import tool
from autogen import UserProxyAgent, AssistantAgent
from connection_utils import CustomConnection, ConnectionInfo
from tools import register_tools


def prepare_connection_info(connection):
    """Prepare the connection info for the agents."""
    return {
        "aoai_model_gpt35": connection.configs["aoai_model_gpt35"],
        "aoai_model_gpt4": connection.configs["aoai_model_gpt4"],
        "aoai_api_key": connection.secrets["aoai_api_key"],
        "aoai_base_url": connection.configs["aoai_base_url"],
        "aoai_api_version": connection.configs["aoai_api_version"],
        "bing_api_key": connection.secrets["bing_api_key"],
        "bing_endpoint": connection.configs["bing_endpoint"],
    }


def prepare_executor(connection_info):
    """Prepare the executor agent."""
    config_list_gpt35 = [
        {
            "model": connection_info["aoai_model_gpt35"],
            "api_key": connection_info["aoai_api_key"],
            "base_url": connection_info["aoai_base_url"],
            "api_type": "azure",
            "api_version": connection_info["aoai_api_version"],
        }
    ]
    executor = UserProxyAgent(
        name="EXECUTOR",
        description=(
            "An agent that acts as a proxy for the user and executes the "
            "suggested function calls from PLANNER."
        ),
        code_execution_config=False,
        llm_config={
            "config_list": config_list_gpt35,
            "timeout": 60,
            "cache_seed": None,
        },
        human_input_mode="NEVER",
    )
    return executor, config_list_gpt35


def llm_tool(request, context, config_list_gpt35):
    """Define the LLM agent."""
    llm_assistant = AssistantAgent(
        name="LLM_ASSISTANT",
        description=(
            "An agent expert in answering requests by analyzing and "
            "extracting information from the given context."
        ),
        system_message=(
            "Given a request and optionally some context with potentially "
            "relevant information to answer it, analyze the context and "
            "extract the information needed to answer the request. Then, "
            "create a sentence that answers the request. You must strictly "
            "limit your response to only what was asked in the request."
        ),
        code_execution_config=False,
        llm_config={
            "config_list": config_list_gpt35,
            "timeout": 60,
            "temperature": 0.3,
            "cache_seed": None,
        },
    )

    llm_assistant.clear_history()

    message = f"""
    Request:
    {request}

    Context:
    {context}
    """
    try:
        reply = llm_assistant.generate_reply(
            messages=[{"content": message, "role": "user"}]
        )
        return reply
    except Exception as e:
        return f"Error: {str(e)}"


def substitute_dependency(
    id, original_argument_value, dependency_value, config_list_gpt35
):
    """Substitute dependencies in the execution plan."""
    instruction = (
        "Extract the entity name or fact from the dependency value in a way "
        "that makes sense to use it to substitute the variable #E in the "
        "original argument value. Do not include any other text in your "
        "response, other than the entity name or fact extracted."
    )

    context = f"""
    original argument value:
    {original_argument_value}

    dependency value:
    {dependency_value}

    extracted fact or entity:

    """

    return llm_tool(instruction, context, config_list_gpt35)


def has_unresolved_dependencies(item, resolved_ids, plan_ids):
    """Check for unresolved dependencies in a plan step."""
    try:
        args = json.loads(item["function"]["arguments"])
    except json.JSONDecodeError:
        return False

    for arg in args.values():
        if isinstance(arg, str) and any(
            ref_id
            for ref_id in plan_ids
            if ref_id not in resolved_ids and ref_id in arg
        ):
            return True
    return False


def submit_task(item_id, item, thread_executor, executor_agent, futures):
    """Submit a task for execution."""
    arguments = item["function"]["arguments"]
    future = thread_executor.submit(
        executor_agent.execute_function,
        {"name": item["function"]["name"], "arguments": arguments},
    )
    futures[item_id] = future


def process_done_future(
    future,
    futures,
    results,
    resolved_ids,
    plan_ids,
    thread_executor,
    executor_agent,
    config_list_gpt35,
):
    """Process a completed future and trigger the submission of ready tasks."""
    item_id = next((id for id, f in futures.items() if f == future), None)
    if item_id:
        _, result = future.result()
        results[item_id] = result
        resolved_ids.add(item_id)
        del futures[item_id]
        submit_ready_tasks(
            plan_ids,
            resolved_ids,
            futures,
            results,
            thread_executor,
            executor_agent,
            config_list_gpt35,
        )


def submit_ready_tasks(
    plan_ids,
    resolved_ids,
    futures,
    results,
    thread_executor,
    executor_agent,
    config_list_gpt35,
):
    """Submit plan tasks that have all dependencies resolved
    and are ready to be executed."""
    for next_item_id, next_item in plan_ids.items():
        if (
            next_item_id not in resolved_ids
            and next_item_id not in futures
            and not has_unresolved_dependencies(
                next_item, resolved_ids, plan_ids
                )
        ):
            update_and_submit_task(
                next_item_id,
                next_item,
                thread_executor,
                executor_agent,
                futures,
                results,
                config_list_gpt35,
            )


def update_and_submit_task(
    item_id, item, thread_executor, executor_agent,
    futures, results, config_list_gpt35
):
    """Update the arguments of a task with dependency results
    and submit it for execution."""
    updated_arguments = json.loads(item["function"]["arguments"])
    for arg_key, arg_value in updated_arguments.items():
        if isinstance(arg_value, str):
            for res_id, res in results.items():
                if arg_key == "context":
                    arg_value = arg_value.replace(res_id, res["content"])
                else:
                    arg_value = arg_value.replace(
                        res_id,
                        substitute_dependency(
                            res_id, arg_value, res["content"],
                            config_list_gpt35
                        ),
                    )
                updated_arguments[arg_key] = arg_value
    future = thread_executor.submit(
        executor_agent.execute_function,
        {"name": item["function"]["name"],
         "arguments": json.dumps(updated_arguments)},
    )
    futures[item_id] = future


def execute_plan_parallel(plan, executor_agent, config_list_gpt35):
    """Execute the plan in parallel."""
    plan_ids = {item["id"]: item for item in plan}
    results = {}
    resolved_ids = set()
    futures = {}

    with concurrent.futures.ThreadPoolExecutor() as thread_executor:
        for item_id, item in plan_ids.items():
            if not has_unresolved_dependencies(item, resolved_ids, plan_ids):
                submit_task(
                    item_id, item, thread_executor,
                    executor_agent, futures
                )

        while futures:
            done, _ = concurrent.futures.wait(
                futures.values(),
                return_when=concurrent.futures.FIRST_COMPLETED
            )
            for future in done:
                process_done_future(
                    future,
                    futures,
                    results,
                    resolved_ids,
                    plan_ids,
                    thread_executor,
                    executor_agent,
                    config_list_gpt35,
                )

    result_str = "\n".join(
        [f"{key} = {value['content']}" for key, value in results.items()]
    )
    return result_str


@tool
def worker_tool(connection: CustomConnection, plan: str) -> str:
    """Execute the plan generated by the planner node."""
    connection_info = prepare_connection_info(connection)
    ConnectionInfo().connection_info = connection_info

    executor, config_list_gpt35 = prepare_executor(connection_info)
    register_tools(executor)

    plan = json.loads(plan)
    executor_reply = execute_plan_parallel(
        plan["Functions"], executor, config_list_gpt35
    )
    number_of_steps = len(plan["Plan"])

    return {
        "executor_reply": executor_reply, "number_of_steps": number_of_steps
    }
