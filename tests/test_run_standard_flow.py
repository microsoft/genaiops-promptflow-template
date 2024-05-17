import random
import string
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from llmops.common.prompt_pipeline import VariantsSelector, prepare_and_execute

THIS_PATH = Path(__file__).parent
RESOURCE_PATH = THIS_PATH / "resources"


@pytest.fixture(scope="module", autouse=True)
def _set_required_env_vars():
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("SUBSCRIPTION_ID", "TEST_SUBSCRIPTION_ID")
    monkeypatch.setenv("RESOURCE_GROUP_NAME", "TEST_RESOURCE_GROUP_NAME")
    monkeypatch.setenv("WORKSPACE_NAME", "TEST_WORKSPACE_NAME")


def random_string():
    return "".join(random.choices(string.ascii_lowercase, k=10))


def get_mocked_source(name, version):
    source = Mock()
    source.name = name
    source.version = version
    return source


def test_variant_selector():
    random_node = random_string()
    random_variant = random_string()
    selected_variant = random_string()
    selected_node = random_string()

    variant_selector = VariantsSelector.from_args("*")
    assert variant_selector.is_variant_enabled(random_node, random_variant)

    variant_selector = VariantsSelector.from_args("all")
    assert variant_selector.is_variant_enabled(random_node, random_variant)

    # TO DO check that this is the intended behavior
    variant_selector = VariantsSelector.from_args("default")
    assert variant_selector.is_variant_enabled(random_node, random_variant)

    variant_selector = VariantsSelector.from_args("defaults")
    assert variant_selector.is_variant_enabled(random_node, random_variant)

    variant_selector = VariantsSelector.from_args(f"{selected_node}.{selected_variant}")
    assert variant_selector.is_variant_enabled(selected_node, selected_variant)
    assert not variant_selector.is_variant_enabled(random_node, random_variant)


def test_run_standard_flow_all():
    variant_selector = VariantsSelector.from_args("*")
    with patch("llmops.common.prompt_pipeline.wait_job_finish"), patch(
        "llmops.common.prompt_pipeline.PFClient"
    ) as mock_pf_client:
        # Mock the PFClient
        pf_client_instance = Mock()
        mock_pf_client.return_value = pf_client_instance

        ds1_name = "ds1"
        ds1_version = "3"
        ds2_name = "ds2"
        ds2_version = "5"
        source_1_remote_name = f"azureml:{ds1_name}:{ds1_version}"
        source_2_remote_name = f"azureml:{ds2_name}:{ds2_version}"

        pf_client_instance.ml_client.data.get.side_effect = lambda name, label: {
            ds1_name: get_mocked_source(ds1_name, ds1_version),
            ds2_name: get_mocked_source(ds2_name, ds2_version),
        }.get(name)

        # Start the run
        prepare_and_execute(
            variants_selector=variant_selector,
            base_path=str(RESOURCE_PATH),
        )

        # Get the argument of each time pf_client.runs.create_or_update is called
        created_runs = pf_client_instance.runs.create_or_update

        # Expect 6 created runs
        # {node_var_0.var_0; node_var_1.var_3; ds1}
        # {node_var_0.var_1; node_var_1.var_3; ds1}
        # {node_var_0.var_0; node_var_1.var_4; ds1}
        # {node_var_0.var_0; node_var_1.var_3; ds2}
        # {node_var_0.var_1; node_var_1.var_3; ds2}
        # {node_var_0.var_0; node_var_1.var_4; ds2}

        # Expected run arguments
        expected_variants = [
            "${node_var_0.var_0}",
            "${node_var_0.var_1}",
            "${node_var_1.var_4}",
            "${node_var_0.var_0}",
            "${node_var_0.var_1}",
            "${node_var_1.var_4}",
        ]
        expected_data = [
            source_1_remote_name,
            source_1_remote_name,
            source_1_remote_name,
            source_2_remote_name,
            source_2_remote_name,
            source_2_remote_name,
        ]
        expected_column_mappings = [
            {"ds1_input": "ds1_mapping"},
            {"ds1_input": "ds1_mapping"},
            {"ds1_input": "ds1_mapping"},
            {"ds2_input": "ds2_mapping"},
            {"ds2_input": "ds2_mapping"},
            {"ds2_input": "ds2_mapping"},
        ]

        assert created_runs.call_count == len(expected_variants)

        # created_runs.call_args_list is triple nested,
        # first index: select the call of pf_client_instance.runs.create_or_update [0, 5]
        # second index: select the argument of pf_client_instance.runs.create_or_update [0 (run), 1 (stream)]
        # third index: select the first element of the tuple [0]
        for i, call_args in enumerate(created_runs.call_args_list):
            run = call_args[0][0]
            assert run.variant == expected_variants[i]
            assert run.data == expected_data[i]
            assert run.column_mapping == expected_column_mappings[i]
            assert run.environment_variables == {"key1": "value1"}


def test_run_standard_flow_default():
    variant_selector = VariantsSelector.from_args("default")
    with patch("llmops.common.prompt_pipeline.wait_job_finish"), patch(
        "llmops.common.prompt_pipeline.PFClient"
    ) as mock_pf_client:
        # Mock the PFClient
        pf_client_instance = Mock()
        mock_pf_client.return_value = pf_client_instance

        ds1_name = "ds1"
        ds1_version = "3"
        ds2_name = "ds2"
        ds2_version = "5"
        source_1_remote_name = f"azureml:{ds1_name}:{ds1_version}"
        source_2_remote_name = f"azureml:{ds2_name}:{ds2_version}"

        pf_client_instance.ml_client.data.get.side_effect = lambda name, label: {
            ds1_name: get_mocked_source(ds1_name, ds1_version),
            ds2_name: get_mocked_source(ds2_name, ds2_version),
        }.get(name)

        # Start the run
        prepare_and_execute(
            variants_selector=variant_selector,
            base_path=str(RESOURCE_PATH),
        )

        # Get the argument of each time pf_client.runs.create_or_update is called
        created_runs = pf_client_instance.runs.create_or_update

        # Expect 2 created runs
        # {node_var_0.var_0; node_var_1.var_3; ds1}
        # {node_var_0.var_1; node_var_1.var_3; ds2}

        # Expected run arguments
        expected_data = [
            source_1_remote_name,
            source_2_remote_name,
        ]
        expected_column_mappings = [
            {"ds1_input": "ds1_mapping"},
            {"ds2_input": "ds2_mapping"},
        ]

        assert created_runs.call_count == len(expected_data)
        for i, call_args in enumerate(created_runs.call_args_list):
            run = call_args[0][0]
            assert run.variant is None  # Run will select the default variant
            assert run.data == expected_data[i]
            assert run.column_mapping == expected_column_mappings[i]
            assert run.environment_variables == {"key1": "value1"}


def test_run_standard_flow_custom():
    variant_selector = VariantsSelector.from_args("node_var_0.var_1, node_var_1.var_4")
    with patch("llmops.common.prompt_pipeline.wait_job_finish"), patch(
        "llmops.common.prompt_pipeline.PFClient"
    ) as mock_pf_client:
        # Mock the PFClient
        pf_client_instance = Mock()
        mock_pf_client.return_value = pf_client_instance

        ds1_name = "ds1"
        ds1_version = "3"
        ds2_name = "ds2"
        ds2_version = "5"
        source_1_remote_name = f"azureml:{ds1_name}:{ds1_version}"
        source_2_remote_name = f"azureml:{ds2_name}:{ds2_version}"

        pf_client_instance.ml_client.data.get.side_effect = lambda name, label: {
            ds1_name: get_mocked_source(ds1_name, ds1_version),
            ds2_name: get_mocked_source(ds2_name, ds2_version),
        }.get(name)

        # Start the run
        prepare_and_execute(
            variants_selector=variant_selector,
            base_path=str(RESOURCE_PATH),
        )

        # Get the argument of each time pf_client.runs.create_or_update is called
        created_runs = pf_client_instance.runs.create_or_update

        # Expect 4 created runs
        # {node_var_0.var_1; node_var_1.var_3; ds1}
        # {node_var_0.var_0; node_var_1.var_4; ds1}
        # {node_var_0.var_1; node_var_1.var_3; ds2}
        # {node_var_0.var_0; node_var_1.var_4; ds2}

        # Expected run arguments
        expected_variants = [
            "${node_var_0.var_1}",
            "${node_var_1.var_4}",
            "${node_var_0.var_1}",
            "${node_var_1.var_4}",
        ]
        expected_data = [
            source_1_remote_name,
            source_1_remote_name,
            source_2_remote_name,
            source_2_remote_name,
        ]
        expected_column_mappings = [
            {"ds1_input": "ds1_mapping"},
            {"ds1_input": "ds1_mapping"},
            {"ds2_input": "ds2_mapping"},
            {"ds2_input": "ds2_mapping"},
        ]

        assert created_runs.call_count == len(expected_variants)
        for i, call_args in enumerate(created_runs.call_args_list):
            run = call_args[0][0]
            assert run.variant == expected_variants[i]
            assert run.data == expected_data[i]
            assert run.column_mapping == expected_column_mappings[i]
            assert run.environment_variables == {"key1": "value1"}
