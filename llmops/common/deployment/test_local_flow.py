"""
This module executes test on build server for local container endpoint.

Args:
--base_path: The base path of the flow use case.
This argument is required to specify the name of the flow for execution.
"""

import argparse
import json
import requests
import time
from llmops.common.logger import llmops_logger

logger = llmops_logger("test local container endpoint")

parser = argparse.ArgumentParser("test local container endpoint")


parser.add_argument("--base_path", type=str, help="flow to test", required=True)


args = parser.parse_args()

flow_name = args.base_path

with open(f"./{flow_name}/sample-request.json", "r") as file:
    json_data = json.load(file)

url = "http://0.0.0.0:8080/score"

headers = {"Content-Type": "application/json"}

max_retries = 3
retry_delay = 2
for attempt in range(max_retries):
    try:
        response = requests.post(
            url, data=json.dumps(json_data), headers=headers, timeout=30
        )

        if response.status_code == 200:
            logger.info("POST request successful!")
            # Print the response content
            logger.info("Response:", response.json())
        else:
            logger.info("POST request failed with status code:", response.status_code)
    except (requests.exceptions.RequestException, ConnectionResetError) as e:
        logger.info(f"Error occurred: {e}")
        time.sleep(retry_delay)
