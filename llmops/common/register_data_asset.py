"""
This module executes experiment jobs/bulk-runs using standard flows.

Args:
--subscription_id: The Azure subscription ID.
This argument is required for identifying the Azure subscription.
--file: The name of the experiment file. Default is 'experiment.yaml'.
--base_path: Base path of the use case. Where flows, data,
and experiment.yaml are expected to be found.
--env_name: The environment name for execution and deployment.
This argument is required to specify the environment (dev, test, prod)
for execution or deployment.
"""

import argparse
import hashlib
from dotenv import load_dotenv
from typing import Optional

from azure.ai.ml import MLClient
from azure.ai.ml.entities import Data as AMLData
from azure.ai.ml.constants import AssetTypes as AMLAssetTypes
from azure.identity import DefaultAzureCredential

from llmops.config import SERVICE_TYPE
from azure.ai.resources.client import AIClient
from azure.ai.resources.entities import Data as StudioData
from azure.ai.resources.constants import AssetTypes as StudioAssetTypes

from llmops.common.experiment_cloud_config import ExperimentCloudConfig
from llmops.common.experiment import load_experiment
from llmops.common.logger import llmops_logger


logger = llmops_logger("register_data_asset")


def generate_file_hash(file_path):
    """
    Generate hash of a file.

    Returns:
        hash as string
    """
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        file_content = file.read()
        sha256.update(file_content)

    return sha256.hexdigest()


def register_data_asset(
    base_path: str,
    exp_filename: Optional[str] = None,
    subscription_id: Optional[str] = None,
    env_name: Optional[str] = None,
):
    """Register data assets in Azure ML."""
    config = ExperimentCloudConfig(
        subscription_id=subscription_id, env_name=env_name
    )

    experiment = load_experiment(
        filename=exp_filename, base_path=base_path, env=config.environment_name
    )

    if SERVICE_TYPE == "AISTUDIO":
        ml_client = AIClient(
            subscription_id=config.subscription_id,
            resource_group_name=config.resource_group_name,
            project_name=config.workspace_name,
            credential=DefaultAzureCredential(),
        )
    else:
        ml_client = MLClient(
            DefaultAzureCredential(),
            config.subscription_id,
            config.resource_group_name,
            config.workspace_name,
        )

    # Get all used datasets
    all_datasets = {ds.dataset.name: ds.dataset for ds in experiment.datasets}

    for evaluator in experiment.evaluators:
        all_datasets.update(
            {ds.dataset.name: ds.dataset for ds in evaluator.datasets}
        )

    # Register local dataset as remote datasets in Azure ML
    for ds in all_datasets.values():
        local_data_path = ds.get_local_source(base_path=base_path)
        if local_data_path:
            logger.info(f"Registering dataset: {ds.name}")

            data_hash = generate_file_hash(local_data_path)
            logger.info(f"Hash of the folder: {data_hash}")

            if SERVICE_TYPE == "AISTUDIO":
                aml_dataset = StudioData(
                    path=local_data_path,
                    type=StudioAssetTypes.FILE,
                    description=ds.description,
                    name=ds.name,
                    tags={"data_hash": data_hash},
                )
            else:
                aml_dataset = AMLData(
                    path=local_data_path,
                    type=AMLAssetTypes.URI_FILE,
                    description=ds.description,
                    name=ds.name,
                    tags={"data_hash": data_hash},
                )

            try:
                data_info = ml_client.data.get(name=ds.name, label="latest")
                m_hash = dict(data_info.tags).get("data_hash")
                if m_hash is not None:
                    if m_hash != data_hash:
                        logger.info(
                            f"Updating dataset. Old hash: {m_hash};"
                            f" New hash: {data_hash}"
                        )
                        ml_client.data.create_or_update(aml_dataset)
                else:
                    logger.info(f"Updating dataset. New hash: {data_hash}")
                    ml_client.data.create_or_update(aml_dataset)
            except Exception:
                logger.info(f"Updating dataset. New hash: {data_hash}")
                ml_client.data.create_or_update(aml_dataset)

            aml_dataset = ml_client.data.get(name=ds.name, label="latest")

            logger.info(aml_dataset.version)
            logger.info(aml_dataset.path)


def main():
    """Entry main function to register data assets."""
    parser = argparse.ArgumentParser("register data assets")
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
        help="Subscription ID",
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
        help="environment name(dev, test, prod) for execution and deployment",
        default=None,
    )

    args = parser.parse_args()

    register_data_asset(
        args.base_path,
        args.file,
        args.subscription_id,
        args.env_name
    )


if __name__ == "__main__":
    # Load variables from .env file into the environment
    load_dotenv(override=True)

    main()
