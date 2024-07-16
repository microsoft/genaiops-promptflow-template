
"""Create connections for local run."""

from llmops.common.common import resolve_flow_type
# from llmops.common.experiment_cloud_config import ExperimentCloudConfig
from llmops.common.experiment import load_experiment
from promptflow.entities import (
    AzureOpenAIConnection,
    OpenAIConnection,
    CognitiveSearchConnection,
    CustomConnection,
    FormRecognizerConnection,
    SerpConnection,
    AzureContentSafetyConnection

)
from promptflow.client import PFClient

import os
from typing import Any, Dict

CONNECTION_CLASSES: Dict[str, Any] = {
    "azureopenaiconnection": AzureOpenAIConnection,
    "openaiconnection": OpenAIConnection,
    "cognitivesearchconnection": CognitiveSearchConnection,
    "customconnection": CustomConnection,
    "formrecognizerconnection": FormRecognizerConnection,
    "serpconnection": SerpConnection,
    "azurecontentsafetyconnection": AzureContentSafetyConnection,
}


def create_pf_connections(
            exp_filename, base_path, env_name
        ):
    """Create local connections for local run."""
    # config = ExperimentCloudConfig(
    #     subscription_id=subscription_id, env_name=env_name)
    experiment = load_experiment(
        filename=exp_filename, base_path=base_path, env=env_name
    )

    flow_type, params_dict = resolve_flow_type(
        experiment.base_path, experiment.flow)

    pf = PFClient()

    for connection_details in experiment.connections:
        connection_type = connection_details.connection_type.lower()

        if connection_type in CONNECTION_CLASSES:
            connection_class = CONNECTION_CLASSES[connection_type]

            connection_properties = {}
            secret_properties = {}
            config_properties = {}
            if connection_type == "customconnection":
                for property_name, property_value in (
                    connection_details.configs.items()
                ):
                    config_properties[property_name] = (
                        _get_valid_connection_values
                        (
                            connection_details.name, str(property_value)
                        )
                    )
                for property_name, property_value in (
                    connection_details.secrets.items()
                ):
                    secret_properties[property_name] = (
                        _get_valid_connection_values
                        (
                            connection_details.name, str(property_value)
                        )
                    )
                connection_properties["name"] = connection_details.name
                connection = connection_class(
                    **connection_properties,
                    configs=config_properties,
                    secrets=secret_properties
                )
            else:
                for property_name, property_value in (
                    connection_details.connection_properties.items()
                ):
                    if property_name.lower() != "connection_type":
                        connection_properties[property_name] = (
                            _get_valid_connection_values
                            (
                                connection_details.name, str(property_value)
                            )
                        )
                    # Create connection object with populated properties
                connection_properties["name"] = connection_details.name
                connection = connection_class(**connection_properties)

            try:
                pf.connections.create_or_update(connection)
                pass
            except Exception as e:
                print(f"Error creating connection: {e}")
                raise e


def _get_valid_connection_values(con_name, con_property):
    """Get valid connection values."""
    if con_property.startswith('${') and con_property.endswith('}'):
        con_property = con_property.replace('${', '').replace('}', '')

        env_var_value = os.environ.get(f"{con_name}_{con_property}".upper())
        if env_var_value:
            return env_var_value
        else:
            raise ValueError(
                f"Environment variable {con_name}_{con_property} not found"
            )
    else:
        return con_property
