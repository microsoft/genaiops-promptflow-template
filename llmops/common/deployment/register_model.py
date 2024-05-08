"""
This module registers a flow in AML workspace model registry.

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
--output_file: A file path to save model version. This argument is not required
but will be used to save the model version to file if specified.
"""

import argparse
import os
import hashlib
from azure.ai.ml import MLClient
from azure.ai.ml.entities import Model
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from typing import Optional

from llmops.common.logger import llmops_logger
from llmops.common.experiment_cloud_config import ExperimentCloudConfig
from llmops.common.experiment import load_experiment

logger = llmops_logger("register_flow")


def hash_folder(folder_path):
    """
    Generate hash for entire folder.

    Returns:
        hash as string
    """
    sha256 = hashlib.sha256()

    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, "rb") as f:
                file_content = f.read()
                sha256.update(file_content)

    return sha256.hexdigest()


def register_model(
    exp_filename: Optional[str] = None,
    base_path: Optional[str] = None,
    env_name: Optional[str] = None,
    subscription_id: Optional[str] = None,
    build_id: Optional[str] = None,
    output_file: Optional[str] = None,
):
    config = ExperimentCloudConfig(subscription_id=subscription_id, env_name=env_name)
    experiment = load_experiment(
        filename=exp_filename, base_path=base_path, env=config.environment_name
    )
    experiment_name = experiment.name
    model_name = f"{experiment_name}_{env_name}"

    logger.info(f"Model name: {model_name}")

    ml_client = MLClient(
        DefaultAzureCredential(),
        config.subscription_id,
        config.resource_group_name,
        config.workspace_name,
    )

    model_path = experiment.get_flow_detail().flow_path
    model_hash = hash_folder(model_path)
    model_tags = {"model_hash": model_hash}
    if build_id:
        model_tags["build_id"] = build_id
    print("Hash of the folder:", model_hash)

    model = Model(
        name=model_name,
        path=model_path,
        stage="Production",
        description=(f"{experiment_name} model registered for prompt flow deployment"),
        properties={"azureml.promptflow.source_flow_id": model_path},
        tags=model_tags,
    )

    try:
        model_info = ml_client.models.get(name=model_name, label="latest")
        m_hash = dict(model_info.tags).get("model_hash")
        if m_hash is not None:
            if m_hash != model_hash:
                ml_client.models.create_or_update(model)
        else:
            ml_client.models.create_or_update(model)
    except Exception:
        ml_client.models.create_or_update(model)

    model_info = ml_client.models.get(name=model_name, label="latest")

    if output_file is not None:
        with open(output_file, "w") as out_file:
            out_file.write(str(model_info.version))


def main():
    parser = argparse.ArgumentParser("register Flow")
    parser.add_argument(
        "--file",
        type=str,
        help="The experiment file. Default is 'experiment.yaml'",
        required=False,
        default="experiment.yaml",
    )
    parser.add_argument(
        "--subscription_id",
        type=str,
        help="Subscription ID, overrides the SUBSCRIPTION_ID environment variable",
        default=None,
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
        help="environment name(dev, test, prod) for execution and deployment, overrides the ENV_NAME environment variable",
        default=None,
    )
    parser.add_argument(
        "--build_id",
        type=str,
        help="Unique identifier for build execution",
        default=None,
    )
    parser.add_argument(
        "--output_file", type=str, required=False, help="A file to save model version"
    )

    args = parser.parse_args()

    register_model(
        args.file,
        args.base_path,
        args.env_name,
        args.subscription_id,
        args.build_id,
        args.output_file,
    )


if __name__ == "__main__":
    # Load variables from .env file into the environment
    load_dotenv(override=True)

    main()
