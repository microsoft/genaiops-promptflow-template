"""
This module creates a AML job and schedule it for the data pipeline.
"""
from datetime import datetime
from azure.ai.ml.dsl import pipeline
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential
from azure.ai.ml import command
from azure.ai.ml import Input, Output
from azure.ai.ml import Input, Output
from azure.ai.ml.entities import Data
from azure.ai.ml import MLClient
from azure.ai.ml.constants import AssetTypes
from azure.ai.ml.entities import (
    JobSchedule,
    CronTrigger,
    RecurrenceTrigger,
    RecurrencePattern,
)
import os
import argparse
import json

pipeline_components = []

()
@pipeline(
    name="ner_data_prep",
    compute="serverless",
    description="data prep pipeline",
)
def ner_data_prep_pipeline(
    # raw_data_dir
):
    prep_data_job = pipeline_components[0](
        # raw_data_dir=raw_data_dir
    )

    return {
        "target_dir": prep_data_job.outputs.target_dir
    }

def get_prep_data_component(
        name,
        display_name,
        description,
        data_pipeline_code_dir,
        environment,
        storage_account,
        storage_key,
        source_container_name,
        target_container_name,
        source_blob,
        assets
):
    data_pipeline_code_dir = os.path.join(os.getcwd(), data_pipeline_code_dir)

    # Initialize an empty list to store components
    prep_data_components = []  

    prep_data_component = command(
        name=name,
        display_name=display_name,
        description=description,
        inputs={ },
        outputs=dict(
            target_dir=Output(type="uri_folder", mode="rw_mount"),
        ),
        code=data_pipeline_code_dir,
        command=f"""python prep_data.py \
                --storage_account {storage_account} \
                --source_container_name {source_container_name} \
                --target_container_name {target_container_name} \
                --source_blob {source_blob} \
                --exp_blob {assets[0]} \
                --eval_blob {assets[1]} \
                --storage_key {storage_key}
                """,
        environment=environment,
    )
    prep_data_components.append(prep_data_component)

    return prep_data_components


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

def create_pipeline_job(
        component_name,
        component_display_name,
        component_description,
        data_pipeline_code_dir,
        aml_env_name,
        storage_account,
        storage_key,
        source_container_name,
        target_container_name,
        source_blob,
        assets
):

    prep_data_component = get_prep_data_component(
        name = component_name,
        display_name = component_display_name,
        description = component_description,
        data_pipeline_code_dir = data_pipeline_code_dir,
        environment = aml_env_name,
        storage_account = storage_account,
        storage_key = storage_key,
        source_container_name = source_container_name,
        target_container_name = target_container_name,
        source_blob = source_blob,
        assets = assets
    )

    pipeline_components.extend(prep_data_component)

    pipeline_job = ner_data_prep_pipeline( )

    return pipeline_job

def schedule_pipeline_job(
        schedule_name,
        schedule_cron_expression,
        schedule_timezone,
        job,
        aml_client,
):
    schedule_start_time = datetime.utcnow()
    cron_trigger = CronTrigger(
        expression = schedule_cron_expression,
        start_time = schedule_start_time,
        time_zone = schedule_timezone
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
    parser.add_argument(
        "--storage_key",
        type=str,
        help="SAS token for storage account",
        required=True,
    )

    args = parser.parse_args()

    subscription_id = args.subscription_id
    resource_group_name = args.resource_group_name
    workspace_name = args.workspace_name
    aml_env_name = args.aml_env_name
    config_path_root_dir = args.config_path_root_dir
    storage_key = args.storage_key

    config_path = os.path.join(os.getcwd(), f"{config_path_root_dir}/configs/dataops_config.json")
    config = json.load(open(config_path))

    component_config = config['DATA_PREP_COMPONENT']
    component_name = component_config['COMPONENT_NAME']
    component_display_name = component_config['COMPONENT_DISPLAY_NAME']
    component_description = component_config['COMPONENT_DESCRIPTION']

    storage_config = config['STORAGE']
    storage_account = storage_config['STORAGE_ACCOUNT']
    source_container_name = storage_config['SOURCE_STORAGE_ACCOUNT_CONTAINER']
    source_blob = storage_config['SOURCE_BLOB']
    target_container_name = storage_config['TARGET_STORAGE_ACCOUNT_CONTAINER']

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
            storage_key,
            source_container_name,
            target_container_name,
            source_blob,
            assets
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