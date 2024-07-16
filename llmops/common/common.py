"""Common utility functions for the promptflow package."""
import ast
import logging
import os
import time
import yaml
import json
from enum import Enum
from typing import Dict, Union

from promptflow.entities import Run

_FLOW_DAG_FILENAME = ("flow.dag.yml", "flow.dag.yaml")
_FLOW_FLEX_FILENAME = ("flow.flex.yml", "flow.flex.yaml")

REQUEST_TIMEOUT_MS = 3 * 60 * 1000

yaml_base_name = "config"


class FlowTypeOption(Enum):
    """Flow type options."""

    DAG_FLOW = 1
    CLASS_FLOW = 2
    FUNCTION_FLOW = 3
    NO_FLOW = 4


class ClientObjectWrapper:
    """Wrapper class for the MLClient object."""

    def __init__(self, pf=None, ml_client=None):
        """Initialize the ObjectWrapper class."""
        self.pf = pf
        self.ml_client = ml_client

    def get_property_value(self):
        """Get the property value."""
        if self.ml_client is not None:
            return self.ml_client
        elif self.pf is not None:
            return getattr(self.pf, "ml_client")
        else:
            raise ValueError("Neither 'pf' nor 'ml_client' is available")


def resolve_env_vars(base_path: str) -> Dict:
    """
    Resolve the environment variables from the config files.

    :return: The environment variables.
    :rtype: Dict
    """
    env_vars = {}
    yaml_file_path = os.path.join(base_path,  "environment", "env.yaml")
    if os.path.isfile(os.path.abspath(yaml_file_path)):
        with open(yaml_file_path, "r") as file:
            yaml_data = yaml.safe_load(file)
        for key, value in yaml_data.items():
            key = str(key).strip().upper()
            value = str(value).strip().upper()

            temp_val = os.environ.get(key, None)
            if temp_val is not None:
                env_vars[key] = os.environ.get(key, None)
            else:
                if (
                    isinstance(value, str)
                    and value.startswith('${')
                    and value.endswith('}')
                ):
                    value = value.replace('${', '').replace('}', '')
                    resolved_value = os.environ.get(value, None)
                    os.environ[key] = str(resolved_value)
                    env_vars[key] = str(resolved_value)
                elif value is None or len(value) == 0:
                    raise ValueError(f"{key} in env.yaml not resolved")
                else:
                    os.environ[key] = str(value)
                    env_vars[key] = str(value)
    else:
        env_vars = {}
        print("no values")
    return env_vars


def resolve_flow_type(
        base_path: str,
        flow_path: str) -> Union[FlowTypeOption, Dict]:
    """
    Resolve the flow type based on the flow folder files.

    :return: The selected flow type.
    :rtype: VariantSelectionOption
    """
    flow_type: FlowTypeOption = None
    safe_base_path = base_path or ""
    found_flex = False
    found_dag = False
    params_dict = {}
    for root, dirs, files in os.walk(os.path.join(safe_base_path, flow_path)):
        for file in files:
            if file in _FLOW_FLEX_FILENAME:
                found_flex = True
                flow_file_path = os.path.abspath(
                    os.path.join(safe_base_path, flow_path, file)
                    )
            elif file in _FLOW_DAG_FILENAME:
                found_dag = True
                flow_file_path = os.path.abspath(
                    os.path.join(safe_base_path, flow_path, file)
                    )

    if found_flex is False and found_dag is False:
        flow_type = FlowTypeOption.NO_FLOW
        params_dict = {}

    if found_flex is True and found_dag is False:
        with open(flow_file_path) as file:
            config = yaml.safe_load(file)

        entry_value = config["entry"]
        file_name, entry_name = entry_value.split(":")
        with open(os.path.abspath(os.path.join(
            safe_base_path, flow_path, file_name + ".py"))
        ) as file:
            source_code = file.read()
        tree = ast.parse(source_code)

        entry_object = None
        for node in ast.walk(tree):
            if (
                isinstance(node, (ast.FunctionDef, ast.ClassDef))
                and node.name == entry_name
            ):
                entry_object = node
                break
        if entry_object is None:
            raise ValueError(f"Entry '{entry_name}' not found in the module.")

        if isinstance(entry_object, ast.ClassDef):
            if os.path.isfile(os.path.abspath(os.path.join(
                safe_base_path, flow_path, "init.json"))
            ):
                with open(os.path.abspath(os.path.join(
                    safe_base_path, flow_path, "init.json"))
                ) as file:
                    init_data = json.load(file)

                for key, value in init_data.items():
                    # params_dict[key] = value
                    if isinstance(value, dict):
                        inner_params = {}
                        for sub_key, sub_value in value.items():
                            env_value = ""
                            if (
                                isinstance(sub_value, str)
                                and sub_value.startswith('${')
                                and sub_value.endswith('}')
                            ):
                                env_var_name = f"{key}_{sub_key}"

                                env_var_value = os.environ.get(
                                    env_var_name.upper()
                                    )
                                if env_var_value:
                                    env_value = env_var_value
                                else:
                                    env_value = sub_value
                            else:
                                env_value = sub_value
                            inner_params[sub_key] = env_value
                        params_dict[key] = inner_params
                    elif isinstance(value, str):
                        env_value = ""
                        if value.startswith('${') and value.endswith('}'):
                            env_var_value = os.environ.get(key.upper())

                            if env_var_value:
                                env_value = env_var_value
                            else:
                                env_value = value
                        else:
                            env_value = value

                        params_dict[key] = env_value
                    elif isinstance(value, int):
                        params_dict[key] = value

            flow_type = FlowTypeOption.CLASS_FLOW
        else:
            flow_type = FlowTypeOption.FUNCTION_FLOW

    if found_flex is False and found_dag is True:
        flow_type = FlowTypeOption.DAG_FLOW
        params_dict = {}

    return (flow_type, params_dict)


def wait_job_finish(job: Run, logger: logging.Logger):
    """
    Wait for job to complete/finish.

    :param job: The prompt flow run object.
    :type job: Run
    :param logger: The used logger.
    :type logger: logging.Logger
    :raises Exception: If job not finished after 3 attempts with 5 second wait.
    """
    max_tries = 3
    attempt = 0
    while attempt < max_tries:
        logger.info(
            "\nWaiting for job %s to finish (attempt: %s)...",
            job.name,
            str(attempt + 1),
        )
        time.sleep(5)
        if job.status in ["Completed", "Finished"]:
            return
        attempt = attempt + 1

    raise Exception("Sorry, exiting job with failure..")


def resolve_run_ids(run_id: str) -> list[str]:
    """
    Read run_id from string or from file.

    :param run_id: List of run IDs (example '["run_id_1", "run_id_2", ...]')
    OR path to file containing list of run IDs.
    :type run_id: str
    :return: List of run IDs.
    :rtype: List[str]
    """
    if os.path.isfile(run_id):
        with open(run_id, "r") as run_file:
            raw_runs_ids = run_file.read()
            run_ids = [] if raw_runs_ids is None else ast.literal_eval(
                raw_runs_ids
            )
    else:
        run_ids = [] if run_id is None or run_id is [] else ast.literal_eval(
            run_id
            )

    return run_ids
