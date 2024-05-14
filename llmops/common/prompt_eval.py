"""
This module evaluates bulk-runs using evaluation flows.

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
--run_id: Run ids of runs to be evaluated (File or comma separated string)
--report_dir: The directory where the outputs and metrics will be stored.
"""

import argparse
import datetime
import json
import os
import pandas as pd

from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from promptflow.entities import Run
from promptflow.azure import PFClient
from typing import Optional

from llmops.common.common import resolve_run_ids, wait_job_finish
from llmops.common.experiment_cloud_config import ExperimentCloudConfig
from llmops.common.experiment import load_experiment
from llmops.common.logger import llmops_logger

logger = llmops_logger("prompt_eval")


def prepare_and_execute(
    run_id: str,
    exp_filename: Optional[str] = None,
    base_path: Optional[str] = None,
    subscription_id: Optional[str] = None,
    build_id: Optional[str] = None,
    env_name: Optional[str] = None,
    report_dir: Optional[str] = None,
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
    config = ExperimentCloudConfig(subscription_id=subscription_id, env_name=env_name)
    experiment = load_experiment(
        filename=exp_filename, base_path=base_path, env=config.environment_name
    )
    experiment_name = experiment.name

    run_ids = resolve_run_ids(run_id)
    if run_ids is None or len(run_ids) == 0:
        raise ValueError("No run ids found.")

    eval_flows = experiment.evaluators

    pf = PFClient(
        DefaultAzureCredential(),
        config.subscription_id,
        config.resource_group_name,
        config.workspace_name,
    )

    standard_flow_detail = experiment.get_flow_detail()
    default_variants = standard_flow_detail.default_variants

    eval_run_ids = []

    runs: dict[str, Run] = {}
    for run in run_ids:
        runs[run] = pf.runs.get(run)

    env_vars = {}
    all_eval_df = []
    all_eval_metrics = []

    for evaluator in eval_flows:
        logger.info(f"Starting evaluation of '{evaluator.name}'")

        dataframes = []
        metrics = []

        flow_name = evaluator.name

        evaluator_executed = False

        # Iterate over standard flow runs
        for flow_run in run_ids:
            logger.info(f"Preparing evaluation of run '{flow_run}'")

            # Get the evaluator mapping of the dataset used in the standard run
            # Skip the evaluation of this run if not found
            current_standard_run = runs[flow_run]
            run_data_id = current_standard_run.data
            if not run_data_id:
                raise ValueError(f"Run {flow_run} does not have a data reference.")

            # Get evaluation datasets by getting the datasets that reference the standard run
            run_data_name = run_data_id.split(":")[1]
            run_dataset = experiment.get_dataset(run_data_name)
            if not run_dataset:
                raise ValueError(
                    f"Run {flow_run} dataset {run_data_name} not found in experiment description."
                )
            dataset_mapping_list = evaluator.find_dataset_with_reference(
                run_dataset.name
            )
            if len(dataset_mapping_list) == 0:
                continue

            for dataset_mapping in dataset_mapping_list:
                logger.info(
                    f"Preparing evaluation of run {flow_run} using dataset {dataset_mapping.dataset.name}"
                )
                column_mapping = dataset_mapping.mappings
                dataset = dataset_mapping.dataset
                data_id = dataset.get_remote_source(pf.ml_client)

                evaluator_executed = True
                # Create run object
                if not experiment.runtime:
                    logger.info(
                        "Using automatic runtime and serverless compute for the prompt flow run"
                    )
                else:
                    logger.info(
                        f"Using runtime '{experiment.runtime}' for the prompt flow run"
                    )

                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                run_name = f"{experiment_name}_eval_{timestamp}"
                runtime_resources = (
                    None
                    if experiment.runtime
                    else {"instance_type": "Standard_E4ds_v4"}
                )

                run = Run(
                    flow=evaluator.path,
                    data=data_id,
                    run=current_standard_run,
                    name=run_name,
                    display_name=run_name,
                    environment_variables=env_vars,
                    column_mapping=column_mapping,
                    tags={} if not build_id else {"build_id": build_id},
                    runtime=experiment.runtime,
                    resources=runtime_resources,
                )
                run._experiment_name = experiment_name

                # Execute the run
                logger.info(
                    f"Starting prompt flow run '{run.name}' in Azure ML. This can take a few minutes.",
                )
                eval_job = pf.runs.create_or_update(run, stream=True)
                eval_run_ids.append(eval_job.name)
                wait_job_finish(eval_job, logger)
                df_result = pf.get_details(eval_job)
                metric_variant = pf.get_metrics(eval_job)

                if (
                    current_standard_run.properties.get(
                        "azureml.promptflow.node_variant", None
                    )
                    is not None
                ):
                    variant_id = current_standard_run.properties[
                        "azureml.promptflow.node_variant"
                    ]
                    start_index = variant_id.find("{") + 1
                    end_index = variant_id.find("}")
                    variant_value = variant_id[start_index:end_index].split(".")

                    df_result[variant_value[0]] = variant_value[1]
                    metric_variant[variant_value[0]] = variant_value[1]
                    df_result["dataset"] = data_id
                    metric_variant["dataset"] = data_id

                    for key, val in default_variants.items():
                        if key == variant_value[0]:
                            pass
                        else:
                            df_result[key] = val
                            metric_variant[key] = val

                dataframes.append(df_result)
                metrics.append(metric_variant)

                logger.info(json.dumps(metrics, indent=4))
                logger.info(df_result.head(10))

        if evaluator_executed and report_dir:
            if not os.path.exists(report_dir):
                os.makedirs(report_dir)

            combined_results_df = pd.concat(dataframes, ignore_index=True)
            combined_metrics_df = pd.DataFrame(metrics)
            combined_results_df["flow_name"] = flow_name
            combined_metrics_df["flow_name"] = flow_name
            combined_results_df["exp_run"] = flow_run
            combined_metrics_df["exp_run"] = flow_run

            combined_results_df.to_csv(f"{report_dir}/{run_data_name}_result.csv")
            combined_metrics_df.to_csv(f"{report_dir}/{run_data_name}_metrics.csv")

            styled_df = combined_results_df.to_html(index=False)

            with open(f"{report_dir}/{run_data_name}_result.html", "w") as c_results:
                c_results.write(styled_df)

            html_table_metrics = combined_metrics_df.to_html(index=False)
            with open(f"{report_dir}/{run_data_name}_metrics.html", "w") as c_metrics:
                c_metrics.write(html_table_metrics)

            all_eval_df.append(combined_results_df)
            all_eval_metrics.append(combined_metrics_df)

    if len(all_eval_df) > 0:
        final_results_df = pd.concat(all_eval_df, ignore_index=True)
        final_metrics_df = pd.concat(all_eval_metrics, ignore_index=True)
        final_results_df["stage"] = env_name
        final_results_df["experiment_name"] = experiment_name
        final_results_df["build"] = build_id

        final_results_df.to_csv(f"{report_dir}/{experiment_name}_result.csv")
        final_metrics_df.to_csv(f"{report_dir}/{experiment_name}_metrics.csv")

        styled_df = final_results_df.to_html(index=False)
        with open(f"{report_dir}/{experiment_name}_result.html", "w") as f_results:
            f_results.write(styled_df)

        html_table_metrics = final_metrics_df.to_html(index=False)
        with open(f"{report_dir}/{experiment_name}_metrics.html", "w") as f_metrics:
            f_metrics.write(html_table_metrics)


def main():
    """
    Run the main evaluation loop by executing evaluation flows.

    Returns:
        None
    """
    parser = argparse.ArgumentParser("prompt_evaluation")
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
        "--run_id",
        type=str,
        required=True,
        help="Run ids of runs to be evaluated (File or comma separated string)",
    )
    parser.add_argument(
        "--report_dir",
        type=str,
        default="./reports",
        help="A folder to save evaluation results and metrics",
    )

    args = parser.parse_args()

    prepare_and_execute(
        args.run_id,
        args.file,
        args.base_path,
        args.subscription_id,
        args.build_id,
        args.env_name,
        args.report_dir,
    )


if __name__ == "__main__":
    # Load variables from .env file into the environment
    load_dotenv(override=True)

    main()
