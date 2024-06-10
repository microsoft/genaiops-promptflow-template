"""
This module evaluates bulk-runs using evaluation flows.

Args:
--file: The name of the experiment file. Default is 'experiment.yaml'.
--base_path: Base path of the use case. Where flows, data,
and experiment.yaml are expected to be found.
--subscription_id: The Azure subscription ID. If this argument is not
specified, the SUBSCRIPTION_ID environment variable is expected to be provided.
--build_id: The unique identifier for build execution.
This argument is not required but will be added as a run tag if specified.
--env_name: The environment name for execution and deployment. This argument
is not required but will be used to read experiment overlay files if specified.
--run_id: Run ids of runs to be evaluated (File or comma separated string)
--report_dir: The directory where the outputs and metrics will be stored.
"""

import argparse
import os
import yaml
from dotenv import load_dotenv
from pathlib import Path
from promptflow.client import PFClient
from typing import Optional

from llmops.common.common import FlowTypeOption
from promptflow._sdk.operations._flow_operations import FlowOperations
from llmops.common.common import resolve_flow_type
from llmops.common.experiment_cloud_config import ExperimentCloudConfig
from llmops.common.experiment import load_experiment
from llmops.common.logger import llmops_logger

logger = llmops_logger("prompt_eval")


def find_connections(data, key, connections):
    '''Find the value of a key in a nested dictionary'''
    if isinstance(data, dict):
        if key in data:
            connections.append(data[key])
        for value in data.values():
            find_connections(value, key, connections)
    elif isinstance(data, list):
        for item in data:
            find_connections(item, key, connections)


def prepare_and_execute(
    exp_filename: Optional[str] = None,
    base_path: Optional[str] = None,
    env_name: Optional[str] = None
):
    """
    Run the evaluation loop by executing evaluation flows.

    reads latest evaluation data assets
    executes evaluation flow against each provided bulk-run
    executes the flow creating a new evaluation job
    saves the results in both csv and html format

    Returns:
        None
    """
    config = ExperimentCloudConfig(subscription_id="None", env_name=env_name)
    experiment = load_experiment(
        filename=exp_filename, base_path=base_path, env=config.environment_name
    )

    print(config.workspace_name)
    pf = PFClient()
    flow_type, params_dict = resolve_flow_type(
        experiment.base_path, experiment.flow
    )

    standard_flow_detail = experiment.get_flow_detail(flow_type)

    if flow_type == FlowTypeOption.CLASS_FLOW:
        flow_path = standard_flow_detail.flow_path
        flow_ops = FlowOperations(pf)
        with open(os.path.join(flow_path, "flow.flex.yaml"), 'r') as file:
            data = yaml.safe_load(file)

        # Check for the 'init' element
        init_element = data.get('init', {})
        if not init_element:
            init_element = data.get('sample', {}).get('init', {})

        # Find connection recursively
        connections = []
        find_connections(init_element, 'connection', connections)

        if connections is not None:
            print(f"Connection value found: {connections}")
            flow_ops._migrate_connections(
                connections,
                Path(
                    os.path.join(
                        experiment.base_path,
                        "docker",
                        "connections"
                        )
                    )
                )
        else:
            print("No connection element found within init element.")


def main():
    """
    Run the main evaluation loop by executing evaluation flows.

    Returns:
        None
    """
    parser = argparse.ArgumentParser("connection_migration")
    parser.add_argument(
        "--file",
        type=str,
        help="The experiment file. Default is 'experiment.yaml'",
        required=False,
        default="experiment.yaml",
    )

    parser.add_argument(
        "--base_path",
        type=str,
        help="Base path of the use case",
        required=True,
    )
    parser.add_argument(
        "--env_name",
        type=str,
        help="environment name(dev, test, prod) for execution and deployment",
        default=None,
    )

    args = parser.parse_args()

    prepare_and_execute(
        args.file,
        args.base_path,
        args.env_name,
    )


if __name__ == "__main__":
    # Load variables from .env file into the environment
    load_dotenv(override=True)

    main()
