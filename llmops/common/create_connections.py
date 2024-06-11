
"""Create connections for local run."""

from llmops.common.common import resolve_flow_type
from llmops.common.experiment_cloud_config import ExperimentCloudConfig
from llmops.common.experiment import load_experiment
from llmops.config import EXECUTION_TYPE

from azure.identity import DefaultAzureCredential
from promptflow.entities import AzureOpenAIConnection
from promptflow.client import PFClient as PFClientLocal
from promptflow.azure import PFClient as PFClientAzure

import os


def create_pf_connections(
            subscription_id, exp_filename, base_path, env_name
        ):
    """Create local connections for local run."""
    config = ExperimentCloudConfig(
        subscription_id=subscription_id, env_name=env_name)
    experiment = load_experiment(
        filename=exp_filename, base_path=base_path, env=env_name
    )

    flow_type, params_dict = resolve_flow_type(
        experiment.base_path, experiment.flow)

    print(params_dict)

    pf = PFClientLocal()

    for connection_details in experiment.connections:
        if connection_details.connection_type.lower() == (
            "azureopenaiconnection"
        ):
            connection = AzureOpenAIConnection(
                name=connection_details.name,
                api_key=_get_valid_connection_values(
                    connection_details.name,
                    connection_details.api_key
                ),
                api_base=_get_valid_connection_values(
                    connection_details.name,
                    connection_details.api_endpoint
                ),
                api_type=_get_valid_connection_values(
                    connection_details.name,
                    connection_details.api_type
                ),
                api_version=_get_valid_connection_values(
                    connection_details.name,
                    connection_details.api_version
                ),
            )

            pf.connections.create_or_update(connection)


def _get_valid_connection_values(con_name, con_property):
    """Get valid connection values."""
    if con_property.startswith('${') and con_property.endswith('}'):
        con_property = con_property.replace('${', '').replace('}', '')

        env_var_value = os.environ.get(f"{con_name}_{con_property}")

        if env_var_value:
            return env_var_value
        else:
            return con_property
    else:
        return con_property
