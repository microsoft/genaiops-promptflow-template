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
from dotenv import load_dotenv
from typing import Optional
import inspect
import importlib

from azure.identity import DefaultAzureCredential

from llmops.common.common import (
    FlowTypeOption,
    ClientObjectWrapper as ObjectWrapper
)
from llmops.common.common import (
    resolve_run_ids,
    resolve_flow_type,
    resolve_env_vars
)
from llmops.common.experiment_cloud_config import ExperimentCloudConfig
from llmops.common.experiment import load_experiment
from llmops.common.logger import llmops_logger
from llmops.common.create_connections import create_pf_connections
from llmops.config import EXECUTION_TYPE
from promptflow.client import PFClient as PFClientLocal
from promptflow.azure import PFClient as PFClientAzure
from promptflow._sdk.entities import Run
from azure.ai.ml import MLClient

logger = llmops_logger("prompt_eval")

files_to_check = [
    'flow.flex.yaml',
    'flow.flex.yml',
    'flow.dag.yaml',
    'flow.dag.yml'
]


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
    config = ExperimentCloudConfig(subscription_id=subscription_id,
                                   env_name=env_name
                                   )
    experiment = load_experiment(
        filename=exp_filename, base_path=base_path, env=config.environment_name
    )
    experiment_name = experiment.name

    run_ids = resolve_run_ids(run_id)

    eval_flows = experiment.evaluators

    flow_type, params_dict = resolve_flow_type(experiment.base_path,
                                               experiment.flow
                                               )

    wrapper = None
    ml_client = None
    if EXECUTION_TYPE == "LOCAL":
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

        wrapper = ObjectWrapper(pf=pf, ml_client=ml_client)
        print(wrapper)

    standard_flow_detail = experiment.get_flow_detail(flow_type)
    default_variants = standard_flow_detail.default_variants

    eval_run_ids = []

    runs: dict[str, Run] = {}
    for run in run_ids:
        runs[run] = pf.runs.get(run)

    if report_dir:
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)

    all_eval_df = []
    all_eval_metrics = []

    for evaluator in eval_flows:
        logger.info(f"Starting evaluation of '{evaluator.name}'")

        flow_type, params_dict = resolve_flow_type(evaluator.path, "")

        env_vars = resolve_env_vars(experiment.base_path, logger)

        dataframes = []
        metrics = []

        flow_name = evaluator.name

        evaluator_executed = False

        # Iterate over standard flow runs
        for flow_run in run_ids:
            logger.info(f"Preparing evaluation of run '{flow_run}'")

            # Get the evaluator mapping of the dataset used
            # in the standard run
            # Skip the evaluation of this run if not found
            current_standard_run = runs[flow_run]
            run_data_id = current_standard_run.data
            print(run_data_id)
            if not run_data_id:
                raise ValueError(f"Run {flow_run}has no data reference.")

            # Get evaluation datasets by getting the datasets
            # that reference the standard run
            if EXECUTION_TYPE == "AZURE":
                run_data_name = run_data_id.split(":")[1]
                run_dataset = experiment.get_dataset(run_data_name)
            else:
                run_data_name = os.path.sep.join(run_data_id.split(
                    os.path.sep)[-2:]
                    )
                print(run_data_name)
                for ds in experiment.datasets:
                    print(ds.dataset.source)
                    if ds.dataset.source == run_data_name:
                        run_dataset = experiment.get_dataset(
                            ds.dataset.name
                            )
                        break
                    else:
                        run_dataset = None

            if not run_dataset:
                raise ValueError(
                    f"Run {flow_run} dataset {run_data_name}"
                    f" not found in experiment description."
                )
            dataset_mapping_list = evaluator.find_dataset_with_reference(
                run_dataset.name
            )
            if len(dataset_mapping_list) == 0:
                continue

            for dataset_mapping in dataset_mapping_list:
                logger.info(
                        f"Preparing evaluation of run {flow_run} "
                        f"using dataset {dataset_mapping.dataset.name}"
                )
                column_mapping = dataset_mapping.mappings
                dataset = dataset_mapping.dataset
                data_id = (
                    dataset.get_local_source(base_path)
                    if EXECUTION_TYPE == "LOCAL"
                    else dataset.get_remote_source(pf.ml_client)
                    )

                evaluator_executed = True
                # Create run object
                if not experiment.runtime:
                    logger.info(
                        "Using automatic runtime and serverless compute"
                    )
                else:
                    logger.info(
                        f"Using runtime '{experiment.runtime}' for runn"
                    )

                timestamp = datetime.datetime.now().strftime(
                    "%Y%m%d_%H%M%S"
                    )
                run_name = f"{experiment_name}_eval_{timestamp}"
                runtime_resources = (
                    None
                    if experiment.runtime
                    else {"instance_type": "Standard_E4ds_v4"}
                )
                # Check if any of the files exist in the directory
                files_found = [
                    file for file in files_to_check
                    if os.path.isfile(
                        os.path.join(evaluator.path, file)
                    )]

                if files_found:
                    if flow_type == FlowTypeOption.DAG_FLOW \
                            or flow_type == FlowTypeOption.FUNCTION_FLOW:
                        run = pf.run(
                            flow=evaluator.path,
                            data=data_id,
                            run=current_standard_run,
                            name=run_name,
                            display_name=run_name,
                            environment_variables=env_vars,
                            column_mapping=column_mapping,
                            tags={} if not build_id else {
                                "build_id": build_id
                                },
                            runtime=experiment.runtime,
                            resources=runtime_resources,
                            stream=True,
                        )
                    elif flow_type == FlowTypeOption.CLASS_FLOW:
                        run = pf.run(
                            flow=evaluator.path,
                            data=data_id,
                            run=current_standard_run,
                            name=run_name,
                            display_name=run_name,
                            environment_variables=env_vars,
                            column_mapping=column_mapping,
                            tags={} if not build_id else {
                                "build_id": build_id
                                },
                            runtime=experiment.runtime,
                            resources=runtime_resources,
                            init=params_dict,
                            stream=True,
                        )
                    else:
                        raise ValueError("Invalid flow type")

                run._experiment_name = experiment_name

                # Execute the run
                logger.info(
                    f"Starting run '{run.name}'. This can take a long time.",
                )

                eval_run_ids.append(run.name)

                df_result = pf.get_details(run=run)
                metric_variant = pf.get_metrics(run)

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
                    variant_value = (
                        variant_id[start_index:end_index].split(".")
                    )
                    print(data_id)
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

            combined_results_df.to_csv(
                f"{report_dir}/{run_dataset.name}_result.csv"
                )
            combined_metrics_df.to_csv(
                f"{report_dir}/{run_dataset.name}_metrics.csv"
                )

            styled_df = combined_results_df.to_html(index=False)

            with open(
                f"{report_dir}/{run_dataset.name}_result.html", "w"
            ) as c_results:
                c_results.write(styled_df)

            html_table_metrics = combined_metrics_df.to_html(index=False)
            with open(
                f"{report_dir}/{run_dataset.name}_metrics.html", "w"
            ) as c_metrics:
                c_metrics.write(html_table_metrics)

            all_eval_df.append(combined_results_df)
            all_eval_metrics.append(combined_metrics_df)

        if flow_type == FlowTypeOption.NO_FLOW:
            service_path = evaluator.path

            service_module = None
            for file in os.listdir(service_path):
                if (
                    file.endswith('.py') and
                    file.lower().startswith('eval_')
                ):
                    module_name = file[:-3]
                    flow_components = service_path.split('/')
                    flow_formatted = '.'.join(flow_components)
                    module_path = (
                        f'{flow_formatted}.'
                        f'{module_name}'
                    )
                    import sys
                    dependent_modules_dir = os.path.join(
                        experiment.base_path, experiment.flow
                        )
                    sys.path.append(dependent_modules_dir)

                    service_module = importlib.import_module(
                        module_path
                        )

                    module_names = dir(service_module)

                    # Filter names to get functions defined in module
                    function_names = [
                        name for name in module_names
                        if inspect.isfunction
                        (
                            getattr(
                                service_module,
                                name
                                )
                            )
                        ]

                    for function_name in function_names:
                        if (
                            function_name.lower().startswith('eval_')
                        ):
                            service_function = getattr(
                                service_module,
                                function_name
                                )
                            for ds in evaluator.datasets:
                                timestamp = datetime.datetime.now().strftime(
                                    "%Y%m%d_%H%M%S"
                                    )
                                if EXECUTION_TYPE == "LOCAL":
                                    result = service_function(
                                        f"{experiment_name}_eval_{timestamp}",
                                        os.path.join(
                                            experiment.base_path,
                                            ds.dataset.source
                                        ),
                                        ds.mappings,
                                        f"{report_dir}/"
                                    )
                                else:
                                    result = service_function(
                                        f"{experiment_name}_eval_{timestamp}",
                                        os.path.join(
                                            experiment.base_path,
                                            ds.dataset.source
                                        ),
                                        ds.mappings,
                                        f"{report_dir}/",
                                        {
                                            "subscription_id": (
                                                config.subscription_id
                                            ),
                                            "resource_group_name": (
                                                config.resource_group_name
                                            ),
                                            "project_name": (
                                                config.workspace_name
                                            ),
                                        }
                                    )

                                print(result)

    if len(all_eval_df) > 0:
        final_results_df = pd.concat(all_eval_df, ignore_index=True)
        final_metrics_df = pd.concat(all_eval_metrics, ignore_index=True)
        final_results_df["stage"] = env_name
        final_results_df["experiment_name"] = experiment_name
        final_results_df["build"] = build_id

        final_results_df.to_csv(f"{report_dir}/{experiment_name}_result.csv")
        final_metrics_df.to_csv(f"{report_dir}/{experiment_name}_metrics.csv")

        styled_df = final_results_df.to_html(index=False)
        with open(
            f"{report_dir}/{experiment_name}_result.html", "w"
        ) as f_results:
            f_results.write(styled_df)

        html_table_metrics = final_metrics_df.to_html(index=False)
        with open(
            f"{report_dir}/{experiment_name}_metrics.html", "w"
        ) as f_metrics:
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
        help="Subscription ID, overrides the SUBSCRIPTION_ID env var",
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
        "--run_id",
        type=str,
        required=True,
        help="Run ids (File or comma separated string)",
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
