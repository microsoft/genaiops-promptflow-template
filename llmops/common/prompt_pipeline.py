"""
Execute experiment jobs/bulk-runs using standard flows.

This function executes experiment jobs or bulk-runs using
predefined standard flows.

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
--output_file: A file path to save run IDs. This argument is not required
but will be used to save the run IDs to file if specified.
--report_dir: The directory where the outputs and metrics will be stored.
--save_output: Flag to save the outputs in files.
If provided, the outputs will be saved in files.
--save_metric: Flag to save the metrics in files.
If provided, the metrics will be saved in files.
"""

import argparse
import datetime
import os
import pandas as pd
from azure.identity import DefaultAzureCredential
from promptflow.entities import Run
from promptflow.azure import PFClient
from dotenv import load_dotenv
from typing import Optional

from llmops.common.common import wait_job_finish
from llmops.common.experiment_cloud_config import ExperimentCloudConfig
from llmops.common.experiment import load_experiment
from llmops.common.logger import llmops_logger

logger = llmops_logger("prompt_pipeline")


def check_dictionary_contained(ref_dict, dict_list):
    for candidate_dict in dict_list:
        set1 = {frozenset(dict(candidate_dict).items())}
        set2 = {frozenset(ref_dict.items())}
        if set1 == set2:
            return True
    return False


def prepare_and_execute(
    exp_filename: Optional[str],
    base_path: Optional[str],
    subscription_id: Optional[str],
    report_dir: Optional[str],
    build_id: Optional[str],
    env_name: Optional[str],
    output_file: Optional[str],
    save_output: Optional[bool],
    save_metric: Optional[bool],
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
    experiment = load_experiment(
        filename=exp_filename, base_path=base_path, env=config.environment_name
    )

    pf = PFClient(
        DefaultAzureCredential(),
        config.subscription_id,
        config.resource_group_name,
        config.workspace_name,
    )

    flow_detail = experiment.get_flow_detail()
    run_ids = []
    past_runs = []
    all_df = []
    all_metrics = []

    logger.info("Running experiment %s", experiment.name)
    for mapped_dataset in experiment.datasets:
        logger.info("Using dataset %s", mapped_dataset.dataset.source)
        dataset = mapped_dataset.dataset
        column_mapping = mapped_dataset.mappings

        env_vars = {"key1": "value1"}
        dataframes = []
        metrics = []

        if len(flow_detail.all_variants) != 0:
            logger.info("Start processing %d variants", len(flow_detail.all_variants))
            for variant in flow_detail.all_variants:
                for variant_id, node_id in variant.items():
                    logger.info(
                        "Creating run for node '%s' variant '%s'", node_id, variant_id
                    )
                    variant_string = f"${{{node_id}.{variant_id}}}"
                    get_current_defaults = {
                        key: value
                        for key, value in flow_detail.default_variants.items()
                        if key != node_id or value != variant_id
                    }
                    get_current_defaults[node_id] = variant_id
                    get_current_defaults["dataset"] = dataset.name

                    # This check validates that we are not running the same combination of variants more than once
                    if not check_dictionary_contained(get_current_defaults, past_runs):
                        past_runs.append(get_current_defaults)

                        # Create run object
                        if not experiment.runtime:
                            logger.info(
                                "Using automatic runtime and serverless compute for the prompt flow run"
                            )
                        else:
                            logger.info(
                                "Using runtime '%s' for the prompt flow run",
                                experiment.runtime,
                            )

                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        run_name = (
                            f"{experiment.name}_{variant_id}_{timestamp}_{dataset.name}"
                        )
                        runtime_resources = (
                            None
                            if experiment.runtime
                            else {"instance_type": "Standard_E4ds_v4"}
                        )
                        run = Run(
                            flow=flow_detail.flow_path,
                            data=dataset.get_remote_name(pf.ml_client),
                            variant=variant_string,
                            name=run_name,
                            display_name=run_name,
                            environment_variables=env_vars,
                            column_mapping=column_mapping,
                            tags={} if not build_id else {"build_id": build_id},
                            resources=runtime_resources,
                            runtime=experiment.runtime,
                        )
                        run._experiment_name = experiment.name

                        # Execute the run
                        logger.info(
                            "Starting prompt flow run '%s' in Azure ML. This can take a few minutes.",
                            run.name,
                        )
                        job = pf.runs.create_or_update(run, stream=True)
                        run_ids.append(job.name)
                        wait_job_finish(job, logger)

                        df_result = pf.get_details(job)
                        logger.info(
                            "Run %s completed with status %s", job.name, job.status
                        )
                        logger.info("Results:\n%s", df_result.head(10))
                        logger.info("Finished processing default variant\n")

                        if save_output:
                            dataframes.append(df_result)
                        if save_metric:
                            metric_variant = df_result
                            metric_variant[variant_id] = variant_string
                            metric_variant["dataset"] = dataset.name
                            metrics.append(metric_variant)
            logger.info("Finished processing all variants")
        else:
            logger.info("Start processing default variant")

            # Create run object
            if not experiment.runtime:
                logger.info(
                    "Using automatic runtime and serverless compute for the prompt flow run"
                )
            else:
                logger.info(
                    "Using runtime '%s' for the prompt flow run", experiment.runtime
                )

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            run_name = f"{experiment.name}_{timestamp}_{dataset.name}"
            runtime_resources = (
                None if experiment.runtime else {"instance_type": "Standard_E4ds_v4"}
            )
            run = Run(
                flow=flow_detail.flow_path,
                data=dataset.get_remote_name(pf.ml_client),
                name=run_name,
                display_name=run_name,
                environment_variables=env_vars,
                column_mapping=column_mapping,
                tags={} if not build_id else {"build_id": build_id},
                resources=runtime_resources,
                runtime=experiment.runtime,
            )
            run._experiment_name = experiment.name

            # Execute the run
            logger.info(
                "Starting prompt flow run '%s' in Azure ML. This can take a few minutes.",
                run.name,
            )
            pf.ml_client
            job = pf.runs.create_or_update(run, stream=True)
            run_ids.append(job.name)
            wait_job_finish(job, logger)
            df_result = pf.get_details(job)
            logger.info("Run %s completed with status %s", job.name, job.status)
            logger.info("Results:\n%s", df_result.head(10))
            logger.info("Finished processing default variant\n")

            if save_output:
                dataframes.append(df_result)
            if save_metric:
                metric_variant = df_result
                metric_variant["dataset"] = dataset.name
                metrics.append(metric_variant)

        # Save outputs and metrics per dataset
        if (save_output or save_metric) and not os.path.exists(report_dir):
            os.makedirs(report_dir)

        if save_output:
            combined_results_df = pd.concat(dataframes, ignore_index=True)
            combined_results_df.to_csv(f"{report_dir}/{dataset.name}_result.csv")
            styled_df = combined_results_df.to_html(index=False)
            with open(f"{report_dir}/{dataset.name}_result.html", "w") as c_results:
                c_results.write(styled_df)
            all_df.append(combined_results_df)
        if save_metric:
            combined_metrics_df = pd.DataFrame(metrics)
            combined_metrics_df.to_csv(f"{report_dir}/{dataset.name}_metrics.csv")

            html_table_metrics = combined_metrics_df.to_html(index=False)

            with open(f"{report_dir}/{dataset.name}_metrics.html", "w") as full_metric:
                full_metric.write(html_table_metrics)
            all_metrics.append(combined_metrics_df)

    # Write to file run ids
    if output_file is not None:
        with open(output_file, "w") as out_file:
            out_file.write(str(run_ids))
    logger.info(str(run_ids))

    # Save outputs and metrics for experiment
    if save_output:
        final_results_df = pd.concat(all_df, ignore_index=True)
        final_results_df["stage"] = env_name
        final_results_df["experiment_name"] = experiment.name
        final_results_df["build"] = build_id
        final_results_df.to_csv(f"./{report_dir}/{experiment.name}_result.csv")
        styled_df = final_results_df.to_html(index=False)
        with open(f"{report_dir}/{experiment.name}_result.html", "w") as results:
            results.write(styled_df)
        logger.info(f"Saved the results in files in {report_dir} folder")

    if save_metric:
        final_metrics_df = pd.concat(all_metrics, ignore_index=True)
        final_metrics_df.to_csv(f"./{report_dir}/{experiment.name}_metrics.csv")
        html_table_metrics = final_metrics_df.to_html(index=False)
        with open(f"{report_dir}/{experiment.name}_metrics.html", "w") as f_metrics:
            f_metrics.write(html_table_metrics)

        logger.info(f"Saved the metrics in files in {report_dir} folder")


def main():
    """
    Run experimentation loop by executing standard Prompt Flows.

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
    parser.add_argument(
        "--build_id",
        type=str,
        help="Unique identifier for build execution",
        default=None,
    )
    parser.add_argument(
        "--report_dir",
        type=str,
        default="./reports",
        help="A folder to save evaluation results and metrics",
    )
    parser.add_argument(
        "--output_file", type=str, required=False, help="A file to save run ids"
    )
    parser.add_argument(
        "--save_output",
        help="Save the outputs to report dir",
        required=False,
        action="store_true",
    )
    parser.add_argument(
        "--save_metric",
        help="Save the metrics to report dir",
        required=False,
        action="store_true",
    )
    args = parser.parse_args()

    prepare_and_execute(
        args.file,
        args.base_path,
        args.subscription_id,
        args.report_dir,
        args.build_id,
        args.env_name,
        args.output_file,
        args.save_output,
        args.save_metric,
    )


if __name__ == "__main__":
    # Load variables from .env file into the environment
    load_dotenv(override=True)

    main()
