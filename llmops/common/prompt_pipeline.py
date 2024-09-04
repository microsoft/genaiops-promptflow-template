"""
Execute experiment jobs/bulk-runs using standard flows.

This function executes experiment jobs or bulk-runs using
predefined standard flows.

Args:
--file: The name of the experiment file. Default is 'experiment.yaml'.
--variants: Variants to run. (* for all, defaults, or comma separated list)
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

Example for running the script with variants
(using web_classification experiment):

# Run only the default variants
python -m llmops.common.prompt_pipeline
    --base_path ./web_classification --variants defaults

# Run all variants
python -m llmops.common.prompt_pipeline
    --base_path ./web_classification --variants all
OR
python -m llmops.common.prompt_pipeline
    --base_path ./web_classification --variants *

# Run specific variants
python -m llmops.common.prompt_pipeline --base_path ./web_classification
    --variants variant_0,variant_1
OR
python -m llmops.common.prompt_pipeline
    --base_path ./web_classification
    --variants summarize_text_content.variant_0

"""

import argparse
import datetime
import os
import pandas as pd
from dotenv import load_dotenv
from enum import Enum
from typing import Optional

from llmops.common.common import (
    resolve_flow_type,
    resolve_env_vars,
    ClientObjectWrapper as ObjectWrapper,
)
from llmops.common.experiment_cloud_config import ExperimentCloudConfig
from llmops.common.experiment import load_experiment
from llmops.common.logger import llmops_logger
from llmops.common.create_connections import create_pf_connections
from llmops.common.common import FlowTypeOption
from llmops.config import EXECUTION_TYPE
from promptflow.client import PFClient as PFClientLocal
from promptflow.azure import PFClient as PFClientAzure
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential

logger = llmops_logger("prompt_pipeline")


def check_dictionary_contained(ref_dict, dict_list):
    """Check if a dictionary is contained in a list of dictionaries."""
    for candidate_dict in dict_list:
        set1 = {frozenset(dict(candidate_dict).items())}
        set2 = {frozenset(ref_dict.items())}
        if set1 == set2:
            return True
    return False


class VariantsSelector:
    """Selects the variants to run. Options are default, all or custom."""

    class VariantSelectionOption(Enum):
        """provide enum options for variant selection."""

        DEFAULTS_ONLY = 1
        ALL = 2
        CUSTOM = 3

    def __init__(
        self,
        selector: VariantSelectionOption,
        selected_variants: Optional[list[str]] = None,
    ):
        """Store for variants and option."""
        self._selector = selector
        self._selected_variants = selected_variants or []

    @property
    def defaults_only(self) -> bool:
        """Compare if default variant is selected."""
        return self._selector == self.VariantSelectionOption.DEFAULTS_ONLY

    def is_variant_enabled(self, node: str, variant: str) -> bool:
        """Check if the variant is enabled."""
        if self._selector in [
            VariantsSelector.VariantSelectionOption.DEFAULTS_ONLY,
            VariantsSelector.VariantSelectionOption.ALL,
        ]:
            return True

        for selected_variant in self._selected_variants:
            if selected_variant in (variant, f"{node}.{variant}"):
                return True
        return False

    @classmethod
    def from_args(cls, variants: str):
        """Parse the variants from the command line arguments."""
        variants = variants.strip().lower()
        if variants in ["*", "all"]:
            return cls(cls.VariantSelectionOption.ALL)
        if variants in ["defaults", "default"]:
            return cls(cls.VariantSelectionOption.DEFAULTS_ONLY)
        return cls(
            cls.VariantSelectionOption.CUSTOM,
            [v.strip() for v in variants.split(",")]
        )


def prepare_and_execute(
    variants_selector: VariantsSelector,
    exp_filename: Optional[str] = None,
    base_path: Optional[str] = None,
    subscription_id: Optional[str] = None,
    report_dir: Optional[str] = None,
    build_id: Optional[str] = None,
    env_name: Optional[str] = None,
    output_file: Optional[str] = None,
    save_output: Optional[bool] = None,
    save_metric: Optional[bool] = None,
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
    config = ExperimentCloudConfig(
        subscription_id=subscription_id, env_name=env_name)
    experiment = load_experiment(
        filename=exp_filename, base_path=base_path, env=config.environment_name
    )

    flow_type, params_dict = resolve_flow_type(
        experiment.base_path, experiment.flow)

    ml_client = None
    wrapper = None
    if EXECUTION_TYPE == "LOCAL":
        logger.info("Creating promptflow connections for local execution.")
        pf = PFClientLocal()
        create_pf_connections(
            exp_filename,
            base_path,
            env_name
        )
        wrapper = ObjectWrapper(pf=pf)
    else:

        ml_client = MLClient(
            subscription_id=config.subscription_id,
            resource_group_name=config.resource_group_name,
            workspace_name=config.workspace_name,
            credential=DefaultAzureCredential(),
        )

        pf = PFClientAzure(
            credential=DefaultAzureCredential(),
            subscription_id=config.subscription_id,
            workspace_name=config.workspace_name,
            resource_group_name=config.resource_group_name
        )
        if ml_client is not None:
            wrapper = ObjectWrapper(pf=pf, ml_client=ml_client)
        else:
            wrapper = ObjectWrapper(pf=pf)

    flow_detail = experiment.get_flow_detail(flow_type)
    print(flow_detail.flow_path)
    run_ids = []
    past_runs = []
    all_df = []
    all_metrics = []

    env_vars = {}
    env_vars = resolve_env_vars(experiment.base_path, logger)

    logger.info(f"Running experiment {experiment.name}")
    for mapped_dataset in experiment.datasets:
        logger.info(f"Using dataset {mapped_dataset.dataset.source}")
        dataset = mapped_dataset.dataset
        column_mapping = mapped_dataset.mappings

        dataframes = []
        metrics = []

        if (len(flow_detail.all_variants) != 0 and
                not variants_selector.defaults_only):
            logger.info(
                f"Start processing {len(flow_detail.all_variants)} variants"
                )
            for variant in flow_detail.all_variants:
                for variant_id, node_id in variant.items():
                    if not variants_selector.is_variant_enabled(
                        node_id, variant_id
                    ):
                        continue
                    logger.info(
                        f"Creating run for node '{node_id}' '{variant_id}'"
                    )
                    variant_string = f"${{{node_id}.{variant_id}}}"
                    get_current_defaults = {
                        key: value
                        for key, value in flow_detail.default_variants.items()
                        if key != node_id or value != variant_id
                    }
                    get_current_defaults[node_id] = variant_id
                    get_current_defaults["dataset"] = dataset.name

                    # This validates that we are not running the same
                    # combination of variants more than once
                    if not check_dictionary_contained(
                        get_current_defaults, past_runs
                    ):
                        past_runs.append(get_current_defaults)

                        # Create run object
                        if not experiment.runtime:
                            logger.info(
                                "Using automatic runtime and compute for run"
                            )
                        else:
                            logger.info(
                                f"Using runtime '{experiment.runtime}'"
                            )

                        timestamp = datetime.datetime.now().strftime(
                            "%Y%m%d_%H%M%S"
                        )
                        run_name = (
                            f"{experiment.name}_"
                            f"{variant_id}_"
                            f"{timestamp}_"
                            f"{dataset.name}"
                        )
                        runtime_resources = (
                            None
                            if experiment.runtime
                            else {"instance_type": "Standard_E4ds_v4"}
                        )

                        if (flow_type == FlowTypeOption.DAG_FLOW or
                                flow_type == FlowTypeOption.FUNCTION_FLOW):
                            run = pf.run(
                                flow=flow_detail.flow_path,
                                data=(
                                    dataset.get_local_source(base_path)
                                    if EXECUTION_TYPE == "LOCAL"
                                    else dataset.get_remote_source(
                                        wrapper.get_property_value()
                                    )
                                ),
                                variant=variant_string,
                                name=run_name,
                                display_name=run_name,
                                environment_variables=env_vars,
                                column_mapping=column_mapping,
                                tags={} if not build_id else {
                                    "build_id": build_id
                                },
                                resources=runtime_resources,
                                runtime=experiment.runtime,
                                stream=True,
                            )
                        elif flow_type == FlowTypeOption.CLASS_FLOW:
                            run = pf.run(
                                flow=flow_detail.flow_path,
                                data=(
                                    dataset.get_local_source(base_path)
                                    if EXECUTION_TYPE == "LOCAL"
                                    else dataset.get_remote_source(
                                        wrapper.get_property_value()
                                    )
                                ),
                                variant=variant_string,
                                name=run_name,
                                display_name=run_name,
                                environment_variables=env_vars,
                                column_mapping=column_mapping,
                                tags={} if not build_id else {
                                    "build_id": build_id
                                },
                                resources=runtime_resources,
                                runtime=experiment.runtime,
                                init=params_dict,
                                stream=True,
                            )
                        else:
                            raise ValueError("Invalid flow type")
                        run._experiment_name = experiment.name

                        # Execute the run
                        logger.info(
                            f"Starting run '{run.name}'. This can take time.",
                        )
                        df_result = pf.get_details(run=run)
                        run_ids.append(str(run.name))
                        # wait_job_finish(job, logger)

                        # df_result = pf.get_details(job)
                        logger.info(
                            f"Run {run.name} status {run.status}",
                        )
                        logger.info(f"Results:\n{df_result.head(10)}")
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
                    "Using automatic runtime and compute for run"
                )
            else:
                logger.info(
                    f"Using runtime '{experiment.runtime}'"
                )

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            run_name = f"{experiment.name}_{timestamp}_{dataset.name}"
            runtime_resources = (
                None if experiment.runtime else {
                    "instance_type": "Standard_E4ds_v4"
                }
            )

            if (flow_type == FlowTypeOption.DAG_FLOW or
                    flow_type == FlowTypeOption.FUNCTION_FLOW):
                run = pf.run(
                    flow=flow_detail.flow_path,
                    data=(
                        dataset.get_local_source(base_path)
                        if EXECUTION_TYPE == "LOCAL"
                        else dataset.get_remote_source(
                            wrapper.get_property_value()
                            )
                    ),
                    name=run_name,
                    display_name=run_name,
                    environment_variables=env_vars,
                    column_mapping=column_mapping,
                    tags={} if not build_id else {"build_id": build_id},
                    resources=runtime_resources,
                    runtime=experiment.runtime,
                    stream=True,
                )
            elif flow_type == FlowTypeOption.CLASS_FLOW:
                run = pf.run(
                    flow=flow_detail.flow_path,
                    data=(
                        dataset.get_local_source(base_path)
                        if EXECUTION_TYPE == "LOCAL"
                        else dataset.get_remote_source(
                                wrapper.get_property_value()
                            )
                    ),
                    name=run_name,
                    display_name=run_name,
                    environment_variables=env_vars,
                    column_mapping=column_mapping,
                    tags={} if not build_id else {"build_id": build_id},
                    resources=runtime_resources,
                    runtime=experiment.runtime,
                    init=params_dict,
                    stream=True,
                )
            run._experiment_name = experiment.name
            print(run)

            # Execute the run
            logger.info(
                f"Starting run '{run.name}' in Azure ML. This can take time.",
            )

            df_result = pf.get_details(run=run)
            run_ids.append(str(run.name))
            logger.info(f"Run {run.name} completed with status {run.status}")
            logger.info(
                f"Results:\n{df_result.head(10)}",
            )
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
            combined_results_df.to_csv(
                f"{report_dir}/{dataset.name}_result.csv"
            )
            styled_df = combined_results_df.to_html(index=False)
            with open(
                f"{report_dir}/{dataset.name}_result.html", "w"
            ) as c_results:
                c_results.write(styled_df)
            all_df.append(combined_results_df)
        if save_metric:
            combined_metrics_df = pd.DataFrame(metrics)
            combined_metrics_df.to_csv(
                f"{report_dir}/{dataset.name}_metrics.csv"
            )

            html_table_metrics = combined_metrics_df.to_html(index=False)

            with open(
                f"{report_dir}/{dataset.name}_metrics.html", "w"
            ) as full_metric:
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
        with open(
            f"{report_dir}/{experiment.name}_result.html", "w"
        ) as results:
            results.write(styled_df)
        logger.info(f"Saved the results in files in {report_dir} folder")

    if save_metric:
        final_metrics_df = pd.concat(all_metrics, ignore_index=True)
        final_metrics_df.to_csv(
            f"./{report_dir}/{experiment.name}_metrics.csv"
        )
        html_table_metrics = final_metrics_df.to_html(index=False)
        with open(
            f"{report_dir}/{experiment.name}_metrics.html", "w"
        ) as f_metrics:
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
        "--variants",
        type=str,
        help="Variants to run. (* for all, defaults, or comma separated list)",
        default="*",
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
        "--output_file", type=str, required=False, help="save run ids"
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
        VariantsSelector.from_args(args.variants),
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
