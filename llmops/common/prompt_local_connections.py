"""
This module evaluates bulk-runs using evaluation flows.

Args:
--env_name: The environment name for execution/deployment.
This argument is required to specify the environment (dev, test, prod)
--base_path: The base path of the flow use case.
This argument is required to specify the name of the flow for execution.
--connection_details: JSON string describing the details of
local pf connection.
"""

import argparse

from dotenv import load_dotenv
from llmops.common.common import resolve_flow_type

from llmops.common.experiment import load_experiment
from llmops.common.logger import llmops_logger
from llmops.common.create_connections import create_pf_connections


logger = llmops_logger("prompt_aoai_connection")


def prepare_and_execute(
    base_path,
    env_name,
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
    logger.info(f"Using environment '{env_name}'")

    experiment = load_experiment(
        filename="experiment.yaml", base_path=base_path, env=env_name
    )

    flow_type, params_dict = resolve_flow_type(
        experiment.base_path, experiment.flow)

    print(params_dict)
    print(experiment.connections)

    create_pf_connections(
        "",
        "experiment.yaml",
        base_path,
        env_name
    )


def main():
    """
    Create local Azure OpenAI connection objects.

    Returns:
        None
    """
    parser = argparse.ArgumentParser("aoai_pf_connection")

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

    prepare_and_execute(args.base_path, args.env_name)


if __name__ == "__main__":
    # Load variables from .env file into the environment
    load_dotenv(override=True)

    main()
