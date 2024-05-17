from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest
from llmops.common.prompt_eval import prepare_and_execute

THIS_PATH = Path(__file__).parent
RESOURCE_PATH = THIS_PATH / "resources"


@pytest.fixture(scope="module", autouse=True)
def _set_required_env_vars():
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("SUBSCRIPTION_ID", "TEST_SUBSCRIPTION_ID")
    monkeypatch.setenv("RESOURCE_GROUP_NAME", "TEST_RESOURCE_GROUP_NAME")
    monkeypatch.setenv("WORKSPACE_NAME", "TEST_WORKSPACE_NAME")


def get_mocked_source(name, version):
    source = Mock()
    source.name = name
    source.version = version
    return source


def test_run_multiple_evaluation_flows():
    with patch("llmops.common.prompt_eval.wait_job_finish"), patch(
        "llmops.common.prompt_eval.PFClient"
    ) as mock_pf_client:
        # Mock the PFClient
        pf_client_instance = Mock()
        mock_pf_client.return_value = pf_client_instance

        # Mock the available remote datasets
        ds_names = ["ds1", "ds2", "ds3", "ds4"]
        ds_versions = ["3", "5", "42", "11"]

        pf_client_instance.ml_client.data.get.side_effect = lambda name, label: {
            ds_names[0]: get_mocked_source(ds_names[0], ds_versions[0]),
            ds_names[1]: get_mocked_source(ds_names[1], ds_versions[1]),
            ds_names[2]: get_mocked_source(ds_names[2], ds_versions[2]),
            ds_names[3]: get_mocked_source(ds_names[3], ds_versions[3]),
        }.get(name)

        standard_run_source_0 = f"azureml:{ds_names[0]}:{ds_versions[0]}"
        standard_run_source_1 = f"azureml:{ds_names[1]}:{ds_versions[1]}"
        evaluation_run_source_0 = f"azureml:{ds_names[2]}:{ds_versions[2]}"
        evaluation_run_source_1 = f"azureml:{ds_names[3]}:{ds_versions[3]}"

        # Mock the standard run
        run_names = ["run_id_0", "run_id_1"]
        standard_run_instance_0 = Mock()
        standard_run_instance_0.data = standard_run_source_0
        standard_run_instance_0.name = run_names[0]
        standard_run_instance_0.tags = []
        standard_run_instance_0.properties.get.return_value = None
        standard_run_instance_1 = Mock()
        standard_run_instance_1.data = standard_run_source_1
        standard_run_instance_1.name = run_names[1]
        standard_run_instance_1.tags = {}
        standard_run_instance_1.properties.get.return_value = None

        pf_client_instance.runs.get.side_effect = lambda run_id: {
            run_names[0]: standard_run_instance_0,
            run_names[1]: standard_run_instance_1,
        }.get(run_id)

        # Mock the run details and metrics
        pf_client_instance.get_metrics.return_value = {}
        pf_client_instance.get_details.return_value = pd.DataFrame()

        # Start the run
        prepare_and_execute(
            run_id="['run_id_0', 'run_id_1']",
            base_path=str(RESOURCE_PATH),
        )

        # Get the argument of each time pf_client.runs.create_or_update is called
        created_runs = pf_client_instance.runs.create_or_update

        # Expect 4 created runs
        # Two for the "eval1" evaluator, one using ds1_source and one using ds3_source
        # Two for the "eval2" evaluator, one using ds4_source and one using ds2_source

        # Expected run arguments
        expected_run = [
            standard_run_instance_0,
            standard_run_instance_1,
            standard_run_instance_0,
            standard_run_instance_1,
        ]
        expected_data = [
            standard_run_source_0,
            evaluation_run_source_0,
            evaluation_run_source_1,
            standard_run_source_1,
        ]
        expected_column_mappings = [
            {"ds1_input": "ds1_mapping", "ds1_extra": "ds1_extra_mapping"},
            {"ds2_extra": "ds2_extra_mapping"},
            {},
            {"ds2_input": "ds2_diff_mapping"},
        ]

        assert created_runs.call_count == len(expected_run)

        # created_runs.call_args_list is triple nested,
        # first index: select the call of pf_client_instance.runs.create_or_update [0, 5]
        # second index: select the argument of pf_client_instance.runs.create_or_update [0 (run), 1 (stream)]
        # third index: select the first element of the tuple [0]
        for i, call_args in enumerate(created_runs.call_args_list):
            run = call_args[0][0]
            assert run.run == expected_run[i]
            assert run.data == expected_data[i]
            assert run.column_mapping == expected_column_mappings[i]
            assert run.environment_variables == {}


def test_run_single_evaluation_flow():
    with patch("llmops.common.prompt_eval.wait_job_finish"), patch(
        "llmops.common.prompt_eval.PFClient"
    ) as mock_pf_client:
        # Mock the PFClient
        pf_client_instance = Mock()
        mock_pf_client.return_value = pf_client_instance

        # Mock the available remote datasets
        ds_names = ["ds1", "ds4"]
        ds_versions = ["3", "11"]

        pf_client_instance.ml_client.data.get.side_effect = lambda name, label: {
            ds_names[0]: get_mocked_source(ds_names[0], ds_versions[0]),
            ds_names[1]: get_mocked_source(ds_names[1], ds_versions[1]),
        }.get(name)

        standard_run_source_0 = f"azureml:{ds_names[0]}:{ds_versions[0]}"
        evaluation_run_source_0 = f"azureml:{ds_names[1]}:{ds_versions[1]}"

        # Mock the standard run
        run_names = ["run_id_0"]
        standard_run_instance_0 = Mock()
        standard_run_instance_0.data = standard_run_source_0
        standard_run_instance_0.name = run_names[0]
        standard_run_instance_0.properties.get.return_value = None

        pf_client_instance.runs.get.side_effect = lambda run_id: {
            run_names[0]: standard_run_instance_0
        }.get(run_id)

        # Mock the run details and metrics
        pf_client_instance.get_metrics.return_value = {}
        pf_client_instance.get_details.return_value = pd.DataFrame()

        # Start the run
        prepare_and_execute(
            run_id="['run_id_0']",
            base_path=str(RESOURCE_PATH),
        )

        # Get the argument of each time pf_client.runs.create_or_update is called
        created_runs = pf_client_instance.runs.create_or_update

        # Expect 2 created runs
        # One for the "eval1" evaluator using ds1_source and one for the "eval2" evaluator using ds4_source

        # Expected run arguments
        expected_run = [standard_run_instance_0, standard_run_instance_0]
        expected_data = [standard_run_source_0, evaluation_run_source_0]
        expected_column_mappings = [
            {"ds1_input": "ds1_mapping", "ds1_extra": "ds1_extra_mapping"},
            {},
        ]

        assert created_runs.call_count == len(expected_run)

        # created_runs.call_args_list is triple nested,
        # first index: select the call of pf_client_instance.runs.create_or_update [0, 5]
        # second index: select the argument of pf_client_instance.runs.create_or_update [0 (run), 1 (stream)]
        # third index: select the first element of the tuple [0]
        for i, call_args in enumerate(created_runs.call_args_list):
            run = call_args[0][0]
            assert run.run == expected_run[i]
            assert run.data == expected_data[i]
            assert run.column_mapping == expected_column_mappings[i]
            assert run.environment_variables == {}
