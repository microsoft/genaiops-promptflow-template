"""
This module creates a AML job and schedule it for the data pipeline.
"""
from datetime import datetime
from azure.ai.ml.dsl import pipeline
from azure.identity import DefaultAzureCredential
from azure.ai.ml import command, UserIdentityConfiguration
from azure.ai.ml import Output
from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    JobSchedule,
    CronTrigger
)
import os
import argparse
import json

pipeline_components = []

()

"""
This function defines a AML pipeline for data preparation in Named Entity Recognition (NER) tasks.
The pipeline is identified by its name and description, and consists of a data preparation job.

The data preparation job is the first component in the pipeline components list.
The output of the data preparation job is a target directory, which is returned by the pipeline.

Decorator:
@pipeline: A decorator to declare this function as a pipeline.
It takes two arguments - name and description of the pipeline.

Returns:
A dictionary with the target directory as the output of the data preparation job.
"""


@pipeline(
    name="ner_data_prep_test",
    description="data prep pipeline",
)
def ner_data_prep_pipeline(
):
    prep_data_job = pipeline_components[0](
    )

    return {
        "target_dir": prep_data_job.outputs.target_dir
    }


"""
This function executes a data preparation component for a data pipeline.
The data component is identified by its name, display name,
and description, and is associated with a specific environment, storage account,
source and target containers, source blob, assets, and custom compute.

Args:
--name: The name of the data component.
This argument is required to specify the name of the data component.
--display_name: The display name of the data component.
This argument is required to specify the display name of the data component.
--description: The description of the data component.
This argument is required to provide a description of the data component.
--data_pipeline_code_dir: The directory of the data pipeline code.
This argument is required to specify the directory of the data pipeline code.
--environment: The environment for the data component.
This argument is required to specify the environment for the data component.
--storage_account: The storage account in Azure.
This argument is required to specify the storage account in Azure.
--source_container_name: The name of the source container in the storage account.
This argument is required to specify the source container in the storage account.
--target_container_name: The name of the target container in the storage account.
This argument is required to specify the target container in the storage account.
--source_blob: The name of the source blob in the source container.
This argument is required to specify the source blob in the source container.
--assets: The assets in the target container.
This argument is required to specify the assets in the target container.
--custom_compute: The custom compute for the data component.
This argument is required to specify the custom compute for the data component.
"""


def get_prep_data_component(
        name,
        display_name,
        description,
        data_pipeline_code_dir,
        environment,
        storage_account,
        source_container_name,
        target_container_name,
        source_blob,
        assets,
        custom_compute
):
    data_pipeline_code_dir = os.path.join(os.getcwd(), data_pipeline_code_dir)

    # Initialize an empty list to store components
    prep_data_components = []
    asset_str = ":".join(map(str, assets))

    prep_data_component = command(
        name=name,
        display_name=display_name,
        description=description,
        inputs={},
        outputs=dict(
            target_dir=Output(type="uri_folder", mode="rw_mount"),
        ),
        code=data_pipeline_code_dir,
        command=f"""python prep_data.py \
                --storage_account {storage_account} \
                --source_container_name {source_container_name} \
                --target_container_name {target_container_name} \
                --source_blob {source_blob} \
                --assets_str {asset_str}
                """,
        environment=environment,
        compute=custom_compute,
        identity=UserIdentityConfiguration()
    )
    prep_data_components.append(prep_data_component)

    return prep_data_components


"""
This function creates and returns an Azure Machine Learning (AML) client.
The AML client is used to interact with Azure Machine Learning services.

Args:
--subscription_id: The Azure subscription ID.
This argument is required for identifying the Azure subscription.
--resource_group_name: The name of the resource group in Azure.
This argument is required to specify the resource group in Azure.
--workspace_name: The name of the workspace in Azure Machine Learning.
This argument is required to specify the workspace in Azure Machine Learning.
"""


def get_aml_client(
        subscription_id,
        resource_group_name,
        workspace_name,
):
    aml_client = MLClient(
        DefaultAzureCredential(),
        subscription_id=subscription_id,
        resource_group_name=resource_group_name,
        workspace_name=workspace_name,
    )

    return aml_client


"""
This function creates a pipeline job with a data component.
The pipeline job is associated with a specific component name, display name,
description, data pipeline, code directory, environment, storage account
source and target containers, source blob, assets, and custom compute.

Args:
--component_name: The name of the data component.
This argument is required to specify the name of the data component.
--component_display_name: The display name of the data component.
This argument is required to specify the display name of the data component.
--component_description: The description of the data component.
This argument is required to provide a description of the data component.
--data_pipeline_code_dir: The directory of the data pipeline code.
This argument is required to specify the directory of the data pipeline code.
--aml_env_name: The name of the Azure Machine Learning environment.
This argument is required to specify the Azure Machine Learning environment.
--storage_account: The storage account in Azure.
This argument is required to specify the storage account in Azure.
--source_container_name: The name of the source container in the storage account.
This argument is required to specify the source container in the storage account.
--target_container_name: The name of the target container in the storage account.
This argument is required to specify the target container in the storage account.
--source_blob: The name of the source blob in the source container.
This argument is required to specify the source blob in the source container.
--assets: The assets in the target container.
This argument is required to specify the assets in the target container.
--custom_compute: The custom compute for the data component.
This argument is required to specify the custom compute for the data component.
"""


def create_pipeline_job(
        component_name,
        component_display_name,
        component_description,
        data_pipeline_code_dir,
        aml_env_name,
        storage_account,
        source_container_name,
        target_container_name,
        source_blob,
        assets,
        custom_compute
):
    prep_data_component = get_prep_data_component(
        name=component_name,
        display_name=component_display_name,
        description=component_description,
        data_pipeline_code_dir=data_pipeline_code_dir,
        environment=aml_env_name,
        storage_account=storage_account,
        source_container_name=source_container_name,
        target_container_name=target_container_name,
        source_blob=source_blob,
        assets=assets,
        custom_compute=custom_compute
    )

    pipeline_components.extend(prep_data_component)

    pipeline_job = ner_data_prep_pipeline()

    return pipeline_job


"""
This function schedules a pipeline job.
The schedule is identified by its name, cron expression, and timezone,
and is associated with a specific job and Azure Machine Learning client.

Args:
--schedule_name: The name of the schedule.
This argument is required to specify the name of the schedule.
--schedule_cron_expression: The cron expression for the schedule.
This argument is required to specify the cron expression for the schedule.
--schedule_timezone: The timezone for the schedule.
This argument is required to specify the timezone for the schedule.
--job: The job for the schedule.
This argument is required to specify the job for the schedule.
--aml_client: The Azure Machine Learning client.
This argument is required to interact with Azure Machine Learning services.
"""


def schedule_pipeline_job(
        schedule_name,
        schedule_cron_expression,
        schedule_timezone,
        job,
        aml_client,
):
    schedule_start_time = datetime.utcnow()
    cron_trigger = CronTrigger(
        expression=schedule_cron_expression,
        start_time=schedule_start_time,
        time_zone=schedule_timezone
    )

    job_schedule = JobSchedule(
        name=schedule_name, trigger=cron_trigger, create_job=job
    )

    aml_client.schedules.begin_create_or_update(
        schedule=job_schedule
    ).result()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--subscription_id",
        type=str,
        help="Azure subscription id",
        required=True,
    )
    parser.add_argument(
        "--resource_group_name",
        type=str,
        help="Azure resource group",
        required=True,
    )
    parser.add_argument(
        "--workspace_name",
        type=str,
        help="Azure ML workspace",
        required=True,
    )
    parser.add_argument(
        "--aml_env_name",
        type=str,
        help="Azure environment name",
        required=True,
    )
    parser.add_argument(
        "--config_path_root_dir",
        type=str,
        help="Root dir for config file",
        required=True,
    )

    args = parser.parse_args()

    subscription_id = args.subscription_id
    resource_group_name = args.resource_group_name
    workspace_name = args.workspace_name
    aml_env_name = args.aml_env_name
    config_path_root_dir = args.config_path_root_dir

    config_path = os.path.join(os.getcwd(), f"{config_path_root_dir}/configs/dataops_config.json")
    config = json.load(open(config_path))

    component_config = config['DATA_PREP_COMPONENT']
    component_name = component_config['COMPONENT_NAME']
    component_display_name = component_config['COMPONENT_DISPLAY_NAME']
    component_description = component_config['COMPONENT_DESCRIPTION']

    storage_config = config['STORAGE']
    storage_account = storage_config['STORAGE_ACCOUNT']
    source_container_name = storage_config['SOURCE_CONTAINER']
    source_blob = storage_config['SOURCE_BLOB']
    target_container_name = storage_config['TARGET_CONTAINER']

    path_config = config['PATH']
    data_pipeline_code_dir = path_config['DATA_PIPELINE_CODE_DIR']

    schedule_config = config['SCHEDULE']
    schedule_name = schedule_config['NAME']
    schedule_cron_expression = schedule_config['CRON_EXPRESSION']
    schedule_timezone = schedule_config['TIMEZONE']

    data_asset_configs = config['DATA_ASSETS']
    assets = []
    for data_asset_config in data_asset_configs:
        assets.append(data_asset_config['PATH'])

    custom_compute = config["COMPUTE_NAME"]

    aml_client = get_aml_client(
        subscription_id,
        resource_group_name,
        workspace_name,
    )

    job = create_pipeline_job(
        component_name,
        component_display_name,
        component_description,
        data_pipeline_code_dir,
        aml_env_name,
        storage_account,
        source_container_name,
        target_container_name,
        source_blob,
        assets,
        custom_compute
    )

    schedule_pipeline_job(
        schedule_name,
        schedule_cron_expression,
        schedule_timezone,
        job,
        aml_client
    )


if __name__ == "__main__":
    main()
