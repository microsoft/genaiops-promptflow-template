
from promptflow import tool

from autogen import UserProxyAgent, AssistantAgent
from connection_utils import CustomConnection, ConnectionInfo
from tools import register_tools
import concurrent.futures
import json

# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need
@tool
def worker_tool(connection: CustomConnection, plan: str) -> str:

    connection_info = {
        "aoai_model_gpt35": connection.configs["aoai_model_gpt35"],
        "aoai_model_gpt4": connection.configs["aoai_model_gpt4"],
        "aoai_api_key": connection.secrets["aoai_api_key"],
        "aoai_base_url": connection.configs["aoai_base_url"],
        "aoai_api_version": connection.configs["aoai_api_version"],
        "bing_api_key": connection.secrets["bing_api_key"],
        "bing_endpoint": connection.configs["bing_endpoint"]
    }

    ConnectionInfo().connection_info = connection_info

    config_list_gpt35 = [
        {
            "model": connection.configs["aoai_model_gpt35"],
            "api_key": connection.secrets["aoai_api_key"],
            "base_url": connection.configs["aoai_base_url"],
            "api_type": "azure",
            "api_version": connection.configs["aoai_api_version"]
        }
    ]

    executor = UserProxyAgent(
        name="EXECUTOR",
        description="""
        An agent that acts as a proxy for the user and executes the suggested function calls from PLANNER.
        """,
        code_execution_config=False,
        llm_config={
            "config_list": config_list_gpt35,
            "timeout": 60,
            "cache_seed": None
        },
        human_input_mode="NEVER"
    )

    register_tools(executor)

    def execute_plan_parallel(plan, agent):
        def has_unresolved_dependencies(item, resolved_ids):
            # Check if item's arguments have unresolved #E references
            try:
                args = json.loads(item['function']['arguments'])
            except json.JSONDecodeError:
                # If arguments are not JSON, consider there are no dependencies
                return False
            
            for arg in args.values():
                # Check if any argument contains a reference not yet resolved
                if isinstance(arg, str) and any(ref_id for ref_id in plan_ids if ref_id not in resolved_ids and ref_id in arg):
                    return True
            return False
        
        def llm_tool(request, context):
    
            llm_assistant = AssistantAgent(
                name="LLM_ASSISTANT",
                description="""
                An agent expert in answering requests by analyzing and extracting information from the given context.
                """,
                system_message="""
                Given a request and optionally some context with potentially relevant information to answer it, analyze the context and extract the information needed to answer the request.
                Then, create a sentence  that answers the request.
                You must strictly limit your response to only what was asked in the request.
                """,
                code_execution_config=False,
                llm_config={
                    "config_list": config_list_gpt35,
                    "timeout": 60,
                    "temperature": 0.3,
                    "cache_seed": None
                }
            )

            llm_assistant.clear_history()

            message = f"""
            Request:
            {request}

            Context:
            {context}
            """
            try:
                reply = llm_assistant.generate_reply(messages=[{"content": message, "role": "user"}])
                return reply
            except Exception as e:
                return f"Error: {str(e)}"
        
        def substitute_dependency(id, original_argument_value, dependency_value):
            instruction = """
            Extract the entity name or fact from the dependency value in a way that makes sense to use it to substitute the variable #E in the original argument value.
            Do not include any other text in your response, other than the entity name or fact extracted.
            """
            
            context = f"""
            original argument value:
            {original_argument_value}

            dependency value:
            {dependency_value}

            extracted fact or entity:

            """

            values_str = ""
            for item in plan:
                if item.get("id") == id:
                    arguments_str = item["function"]["arguments"]
                    arguments_dict = json.loads(arguments_str)
                    values_str = ", ".join([str(value) for value in arguments_dict.values()])

            # return llm_tool(instruction, context) + ", " + values_str
            return llm_tool(instruction, context)

        plan_ids = {item['id']: item for item in plan}
        results = {}
        resolved_ids = set()
        futures = {}

        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit initial tasks without unresolved dependencies
            for item_id, item in plan_ids.items():
                if not has_unresolved_dependencies(item, resolved_ids):
                    arguments = item['function']['arguments']
                    print(item['function']['name'], arguments)
                    future = executor.submit(agent.execute_function, {'name': item['function']['name'], 'arguments': arguments})
                    futures[item_id] = future

            # Process tasks as they complete
            while futures:
                # Wait for at least one future to complete
                done, _ = concurrent.futures.wait(futures.values(), return_when=concurrent.futures.FIRST_COMPLETED)
                
                for future in done:
                    # Find the item_id corresponding to this future
                    item_id = next((id for id, f in futures.items() if f == future), None)
                    if item_id:
                        _, result = future.result()
                        results[item_id] = result
                        resolved_ids.add(item_id)
                        # Remove the completed task
                        del futures[item_id]

                        # Submit new tasks whose dependencies are now resolved
                        for next_item_id, next_item in plan_ids.items():
                            if next_item_id not in resolved_ids and next_item_id not in futures:
                                if not has_unresolved_dependencies(next_item, resolved_ids):
                                    # Replace dependencies in arguments with actual results
                                    updated_arguments = json.loads(next_item['function']['arguments'])
                                    for arg_key, arg_value in updated_arguments.items():
                                        if isinstance(arg_value, str):
                                            for res_id, res in results.items():
                                                if arg_key == "context":
                                                    arg_value = arg_value.replace(res_id, res['content'])
                                                else:
                                                    arg_value = arg_value.replace(res_id, substitute_dependency(res_id, arg_value, res['content']))
                                                updated_arguments[arg_key] = arg_value
                                    print(next_item['function']['name'], json.dumps(updated_arguments))
                                    future = executor.submit(agent.execute_function, {'name': next_item['function']['name'], 'arguments': json.dumps(updated_arguments)})
                                    futures[next_item_id] = future

        # Generate result string
        result_str = '\n'.join([f"{key} = {value['content']}" for key, value in results.items()])
        return result_str
    
    plan = json.loads(plan)
    executor_relpy = execute_plan_parallel(plan['Functions'], executor)

    return executor_relpy