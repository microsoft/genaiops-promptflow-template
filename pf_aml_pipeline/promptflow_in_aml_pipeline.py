import argparse
import datetime
from typing import Optional
from dotenv import load_dotenv


from azure.ai.ml import Input, MLClient, Output, command, dsl, load_component
from azure.ai.ml.constants import AssetTypes, InputOutputModes
from azure.identity import DefaultAzureCredential
from llmops.common.experiment_cloud_config import ExperimentCloudConfig
from llmops.common.config_utils import LLMOpsConfig
from llmops.common.experiment import load_experiment
from llmops.common.logger import llmops_logger

logger = llmops_logger("promptflow_in_aml_pipeline")

pipeline_components = []

def create_dynamic_evaluation_pipeline(
    pipeline_name,
    input_data_path,
):
    """
    Construct evaluation pipeline definition dynamically for a specific app and evaluator.

    Args:
        pipeline_name (str): Name of the pipeline.
    """

    @dsl.pipeline(
        name=pipeline_name,
        input_data_path=input_data_path,
    )
    def evaluation_pipeline(name: str, input_data_path: str):

        preprocess_input_path = Input(
            path=input_data_path,
            type=AssetTypes.URI_FILE,
            mode=InputOutputModes.RO_MOUNT,
        )

        preprocess = pipeline_components[0](
            input_data_path=preprocess_input_path, max_records=2
        )

        experiment = pipeline_components[1](
            data=preprocess.outputs.output_data_path,
            url="${data.url}",
        )

        postprocess = pipeline_components[2](
            input_data_path=experiment.outputs.flow_outputs,
        )

    return evaluation_pipeline


def build_pipeline(pipeline_name: str, flow_path: str, input_data_path: str):
    """
    Constructs an Azure Machine Learning pipeline. It encapsulates the process of defining pipeline inputs,
    loading pipeline components from YAMLs, configuring component environments settings, configuring pipeline settings etc.

    Args:
        pipeline_name (str): Name of the pipeline.

    Returns:
        PipelineJob: Azure Machine Learning pipeline job.
    """
    preprocess_component = command(
        name="./components/preprocess",
        display_name="Data preparation for Promptflow in a pipeline experiment",
        description="Reads the input data and prepares it for the Promptflow experiment",
        inputs={
            "input_data_path": Input(path="string", type="uri_file", mode="ro_mount"),
            "max_records": Input(type="number"),
        },
        outputs={
            "output_data_path": Output(type="uri_file", mode="rw_mount"),
        },
        # The source folder of the component
        code="./pf_aml_pipeline/components/",
        command="""python preprocess.py \
                --input_data_path "${{inputs.input_data_path}}" \
                --max_records "${{inputs.max_records}}" \
                --output_data_path "${{outputs.output_data_path}}" \
                """,
        environment="azureml:AzureML-sklearn-1.0-ubuntu20.04-py38-cpu:1",  # TODO FIXME
    )
    # This step loads the promptflow in the pipeline as a component
    evaluation_promptflow_component = load_component(
        flow_path,
    )
    postprocess_component = command(
        name="postprocess",
        display_name="Post processing for Promptflow in a pipeline experiment",
        description="Reads the output of the Promptflow experiment and does some post processing.",
        inputs={
            "input_data_path": Input(type="uri_folder", mode="rw_mount"),
        },
        # The source folder of the component
        code="./pf_aml_pipeline/components/",
        command="""python postprocess.py  \
                --input_data_path "${{inputs.input_data_path}}" \
                """,
        environment="azureml:AzureML-sklearn-1.0-ubuntu20.04-py38-cpu:1",
    )
    pipeline_components.append(preprocess_component)
    pipeline_components.append(evaluation_promptflow_component)
    pipeline_components.append(postprocess_component)

    pipeline_definition = create_dynamic_evaluation_pipeline(
        pipeline_name=pipeline_name,
        input_data_path=input_data_path,
    )

    return pipeline_definition


def prepare_and_execute(
    exp_filename: Optional[str] = None,
    base_path: Optional[str] = None,
    subscription_id: Optional[str] = None,
    env_name: Optional[str] = None,
):
    """
    Run the experimentation loop by executing standard flows.

    reads latest experiment data assets.
    identifies all variants across all nodes.
    executes the flow creating a new job using
    unique variant combination across nodes.
    saves the results in both csv and html format.
    saves the job ids in text file for later use.

    Returns:
        None
    """
    config = ExperimentCloudConfig(subscription_id=subscription_id, env_name=env_name)
    llmops_config = LLMOpsConfig(flow_name=base_path, environment=env_name)
    
    experiment = load_experiment(
        base_path=base_path,
        base_experiment_config=llmops_config.base_experiment_config,
        overlay_experiment_config=llmops_config.overlay_experiment_config,
        env=config.environment_name
    )

    flow_detail = experiment.get_flow_detail()

    logger.info(f"Running experiment {experiment.name}")
    for mapped_dataset in experiment.datasets:
        logger.info(f"Using dataset {mapped_dataset.dataset.source}")
        dataset = mapped_dataset.dataset

        ml_client = MLClient(
            DefaultAzureCredential(),
            config.subscription_id,
            config.resource_group_name,
            config.workspace_name
        )

        experiment_name = f"{experiment.name}_{env_name}"
        input_data_uri_file = ml_client.data.get(name=dataset.name, label="latest")

        flow_path = f"{flow_detail.flow_path}/flow.dag.yaml"
        build_pipeline("mypipeline", flow_path, input_data_uri_file)

        pipeline_definition = build_pipeline(
            pipeline_name="mypipeline",
            flow_path=flow_path,
            input_data_path=input_data_uri_file,
        )

        pipeline_job = pipeline_definition(name="mypipeline", input_data_path=input_data_uri_file)
        pipeline_job.settings.default_compute = config.compute_target
        # Execute the ML Pipeline
        job = ml_client.jobs.create_or_update(
            pipeline_job,
            experiment_name=experiment_name,
        )

        ml_client.jobs.stream(name=job.name)


def main():
    """
    main() function to run experiment or evaluations.

    Returns:
        None
    """
    parser = argparse.ArgumentParser("prompt_bulk_run")
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

    args = parser.parse_args()

    prepare_and_execute(
        args.file,
        args.base_path,
        args.subscription_id,
        args.env_name,
    )


if __name__ == "__main__":
    # Load variables from .env file into the environment
    load_dotenv(override=True)

    main()