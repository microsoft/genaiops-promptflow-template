"""Tools definitions for AutoGen."""
from autogen import AssistantAgent, UserProxyAgent
from autogen.agentchat import register_function
from connection_utils import ConnectionInfo
from typing_extensions import Annotated, Optional

tool_descriptions = {
    "web_tool": {
        "function": (
            "Worker that searches results from the internet. \
                Useful when you need to find short and succinct "
            "answers about a specific topic."
        ),
        "query": "The search query string.",
        "number_of_results": "The number of search results to return.",
    },
    "wikipedia_tool": {
        "function": (
            "Worker that search for page contents from Wikipedia. \
                Useful when you need to get holistic "
            "knowledge about people, places, companies, historical events, \
                or other subjects. You use it when you "
            "already have identified the entity name, usually after \
                searching for the entity name using web_tool."
        ),
        "query": "The single person name, entity, or concept to be searched.",
        "number_of_results": "The number of search results to return.",
    },
    "llm_tool": {
        "function": (
            "An agent expert in solving problems by analyzing and \
                extracting information from the given "
            "context. It should never be used to do calculations."
        ),
        "request": "The request to be answered.",
        "context": "Context with the relevant information to \
            answer the request.",
    },
    "math_tool": {
        "function": (
            "A tool that can solve math problems by computing \
                arithmetic expressions. It must be used "
            "whenever you need to do calculations or solve math problems. "
            "You can use it to solve simple or complex math problems."
        ),
        "problem_description": "The problem to be solved.",
        "context": "Context with the relevant information \
            to solve the problem.",
    },
}


def register_tools(agent):
    """Register tools for the agent."""
    for tool in tool_descriptions.keys():
        register_function(
            globals()[tool],
            caller=agent,
            executor=agent,
            description=tool_descriptions[tool]["function"],
        )


def llm_tool(
    request: Annotated[str, tool_descriptions["llm_tool"]["request"]],
    context: Optional[Annotated[
        str, tool_descriptions["llm_tool"]["context"]
    ]] = None,
) -> str:
    """Use an LLM to analyze and extract information from the \
        given context to answer the request."""
    connection_info = ConnectionInfo().connection_info

    try:
        llm_assistant = AssistantAgent(
            name="LLM_ASSISTANT",
            description=(
                "An agent expert in answering requests by analyzing and \
                    extracting information from the given context."
            ),
            system_message=(
                "Given a request and optionally some context with \
                    potentially relevant information to answer it, "
                "analyze the context and extract the information \
                    needed to answer the request. "
                "Then, create a sentence that answers the request. "
                "You must strictly limit your response to only \
                    what was asked in the request."
            ),
            code_execution_config=False,
            llm_config={
                "config_list": [
                    {
                        "model": connection_info["aoai_model_gpt35"],
                        "api_key": connection_info["aoai_api_key"],
                        "base_url": connection_info["aoai_base_url"],
                        "api_type": "azure",
                        "api_version": connection_info["aoai_api_version"],
                    }
                ],
                "timeout": 60,
                "temperature": 0.3,
                "cache_seed": None,
            },
        )
    except Exception as e:
        print("LLM_ASSISTANT error:", e)
        return ""

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


def web_tool(
    query: Annotated[str, tool_descriptions["web_tool"]["query"]],
    number_of_results: Optional[
        Annotated[int, tool_descriptions["web_tool"]["number_of_results"]]
    ] = 3,
) -> list:
    """Search results from the internet."""
    import requests
    from bs4 import BeautifulSoup

    connection_info = ConnectionInfo().connection_info

    headers = {"Ocp-Apim-Subscription-Key": connection_info["bing_api_key"]}
    params = {
        "q": query,
        "count": number_of_results,
        "offset": 0,
        "mkt": "en-US",
        "safesearch": "Strict",
        "textDecorations": False,
        "textFormat": "HTML",
    }
    response = requests.get(
        connection_info["bing_endpoint"], headers=headers, params=params
    )
    response.raise_for_status()
    results = response.json()

    search_results = []
    for i in range(len(results["webPages"]["value"])):
        title = results["webPages"]["value"][i]["name"]
        url = results["webPages"]["value"][i]["url"]
        snippet = results["webPages"]["value"][i]["snippet"]

        try:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                text = soup.get_text(separator=" ", strip=True)
                text = text[:5000]
            else:
                text = f"Failed to fetch content, \
                    status code: {response.status_code}"
        except Exception as e:
            text = f"Error fetching the page: {str(e)}"

        search_results.append(
            {"title": title, "url": url, "snippet": snippet, "content": text}
        )

    return llm_tool(query, search_results)


def wikipedia_tool(
    query: Annotated[str, tool_descriptions["wikipedia_tool"]["query"]],
    number_of_results: Optional[
        Annotated[
            int, tool_descriptions["wikipedia_tool"]["number_of_results"]
        ]
    ] = 3,
) -> list:
    """Search for page contents from Wikipedia."""
    import wikipedia

    wikipedia.set_lang("en")
    results = wikipedia.search(query, results=number_of_results)

    search_results = []

    for title in results:
        try:
            page = wikipedia.page(title)
            search_results.append(
                {"title": page.title, "url": page.url,
                 "content": page.content[:5000]}
            )
        except wikipedia.exceptions.DisambiguationError:
            continue
        except wikipedia.exceptions.PageError:
            continue
        except Exception as e:
            search_results.append(f"Error fetching the page: {str(e)}")

    return search_results


def math_tool(
    problem_description: Annotated[
        str, tool_descriptions["math_tool"]["problem_description"]
    ],
    context: Optional[
        Annotated[str, tool_descriptions["math_tool"]["context"]]
    ] = None,
) -> str:
    """Solve math problems by computing arithmetic expressions."""
    connection_info = ConnectionInfo().connection_info

    def is_termination_msg(content):
        have_content = content.get("content", None) is not None
        if have_content and "TERMINATE" in content["content"]:
            return True
        return False

    math_assistant = AssistantAgent(
        name="MATH_ASSISTANT",
        description="An agent expert in solving math \
            problems and math expressions.",
        system_message=(
            "Given a math problem and optionally some context with \
                relevant information to solve the problem, "
            "translate the math problem into an expression that can \
                be executed using Python's numexpr library. "
            "Then, use the available tool (evaluate_math_expression) \
                to solve the expression and return the result. "
            "Reply 'TERMINATE' in the end when everything is done."
        ),
        code_execution_config=False,
        is_termination_msg=is_termination_msg,
        llm_config={
            "config_list": [
                {
                    "model": connection_info["aoai_model_gpt4"],
                    "api_key": connection_info["aoai_api_key"],
                    "base_url": connection_info["aoai_base_url"],
                    "api_type": "azure",
                    "api_version": connection_info["aoai_api_version"],
                }
            ],
            "timeout": 60,
            "cache_seed": None,
        },
    )

    math_executor = UserProxyAgent(
        name="TOOL_EXECUTOR",
        description=(
            "An agent that acts as a proxy for the user and executes "
            "the suggested function calls from MATH_ASSISTANT."
        ),
        code_execution_config=False,
        is_termination_msg=is_termination_msg,
        human_input_mode="NEVER",
    )

    tool_descriptions = {
        "evaluate_math_expression": {
            "function": "Function to evaluate math expressions \
                        using Python's numexpr library.",
            "expression": "The expression to be evaluated. \
                          It should be a valid numerical expression.",
        }
    }

    @math_executor.register_for_execution()
    @math_assistant.register_for_llm(
        description=tool_descriptions["evaluate_math_expression"]["function"]
    )
    def evaluate_math_expression(
        expression: Annotated[
            str, tool_descriptions["evaluate_math_expression"]["expression"]
        ]
    ) -> str:
        import math
        import numexpr
        import re

        try:
            local_dict = {"pi": math.pi, "e": math.e}
            output = str(
                numexpr.evaluate(
                    expression.strip(),
                    global_dict={},  # restrict access to globals
                    local_dict=local_dict,  # add common mathematical functions
                )
            )
        except Exception as e:
            raise ValueError(
                f'Failed to evaluate "{expression}". Raised error: {repr(e)}. '
                "Please try again with a valid numerical expression."
            )

        return re.sub(r"^\[|\]$", "", output)

    message = f"""
    Problem:
    {problem_description}

    Context:
    {context}
    """
    math_assistant.clear_history()
    math_executor.clear_history()

    math_executor.initiate_chat(
        message=message, recipient=math_assistant,
        silent=True, clear_history=True
    )
    result = math_executor.last_message()["content"] \
        .split("TERMINATE")[0].strip()
    return result
