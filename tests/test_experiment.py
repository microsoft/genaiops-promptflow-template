from unittest.mock import Mock

import os
from pathlib import Path
from typing import Any, List
import copy

import pytest
from llmops.common.experiment import (
    Dataset,
    Evaluator,
    Experiment,
    MappedDataset,
    _create_datasets_and_default_mappings,
    _create_eval_datasets_and_default_mappings,
    _create_evaluators,
    _load_base_experiment,
    _apply_overlay,
    load_experiment,
)

THIS_PATH = Path(__file__).parent
RESOURCE_PATH = THIS_PATH / "resources"


def check_lists_equal(actual: List[Any], expected: List[Any]):
    assert len(actual) == len(expected)
    assert all(any(a == e for a in actual) for e in expected)
    assert all(any(a == e for e in expected) for a in actual)


def test_create_datasets_and_default_mappings():
    # Prepare inputs
    g_name = "groundedness"
    g_version = "9"
    g_source = f"azureml:groundedness:{g_version}"
    g_mappings = {"claim": "claim_mapping"}
    g_dataset = Dataset(g_name, g_source, None, None)

    r_name = "recall"
    r_source = "recall_source"
    r_description = "recall_description"
    r_mappings = {"input": "input_mapping", "gt": "gt_mapping"}
    r_dataset = Dataset(r_name, r_source, r_description, None)

    raw_datasets = [
        {"name": g_name, "source": g_source, "mappings": g_mappings},
        {
            "name": r_name,
            "source": r_source,
            "description": r_description,
            "mappings": r_mappings,
        },
    ]

    # Prepare expected outputs
    expected_datasets = {g_name: g_dataset, r_name: r_dataset}
    expected_mapped_datasets = [
        MappedDataset(g_mappings, g_dataset),
        MappedDataset(r_mappings, r_dataset),
    ]

    # Check outputs
    [datasets, mapped_datasets] = _create_datasets_and_default_mappings(raw_datasets)
    assert datasets == expected_datasets
    check_lists_equal(mapped_datasets, expected_mapped_datasets)

    assert not datasets[g_name].is_eval()
    assert not datasets[g_name].get_local_source()

    assert not datasets[r_name].is_eval()
    assert datasets[r_name].get_local_source() == os.path.join("data", r_source)

    # Test get_remote_source
    g_latest_remote_version = "7"

    def mock_data_get(name: str, version: str = None, label: str = None):
        if name == g_name:
            if version == g_version:
                return Mock()
            raise Exception()
        if name == r_name:
            if label == "latest":
                g_remote_ds = Mock()
                g_remote_ds.version = g_latest_remote_version
                return g_remote_ds
            raise Exception()
        raise Exception()

    mock_ml_client = Mock()
    mock_ml_client.data.get.side_effect = mock_data_get

    assert datasets[g_name].get_remote_source(mock_ml_client) == g_source
    assert datasets[r_name].get_remote_source(mock_ml_client) == f"azureml:{r_name}:7"


@pytest.mark.parametrize(
    ("raw_datasets", "error"),
    [
        ([{}], "Dataset 'None' config missing parameter: name"),
        (
            [
                {
                    "name": "groundedness",
                }
            ],
            "Dataset 'groundedness' config missing parameter: source",
        ),
        (
            [
                {
                    "name": "groundedness",
                    "source": "groundedness_source",
                }
            ],
            "Dataset 'groundedness' config missing parameter: mappings",
        ),
        (
            [
                {
                    "name": "groundedness",
                    "source": "groundedness_source",
                    "mappings": [],
                    "reference": "recall",
                }
            ],
            "Unexpected parameter found in dataset 'groundedness' description: reference",
        ),
    ],
)
def test_create_datasets_and_default_mappings_missing_parameters(
    raw_datasets: List[dict], error: str
):
    # Check that datasets with missing parameters raise an exception
    with pytest.raises(ValueError, match=error):
        _create_datasets_and_default_mappings(raw_datasets)


def test_create_eval_datasets_and_default_mappings():
    # Prepare inputs

    # Evaluation datasets
    g_name = "groundedness"
    g_source = "azureml:groundedness:1"
    g_reference = "groundedness_ref"
    g_mappings = {"claim": "claim_mapping"}
    g_dataset = Dataset(g_name, g_source, None, g_reference)

    r_name = "recall"
    r_source = "recall_source"
    r_description = "recall_description"
    r_reference = "recall_ref"
    r_mappings = {"input": "input_mapping", "gt": "gt_mapping"}
    r_dataset = Dataset(r_name, r_source, r_description, r_reference)

    a_name = "accuracy"
    a_source = "accuracy_source"
    a_mappings = {"text": "text_mapping"}
    a_dataset = Dataset(a_name, a_source, None, None)

    # Reference datasets
    g_ref_source = "groundedness_ref_source"
    g_ref_dataset = Dataset(g_reference, g_ref_source, None, None)

    r_ref_source = "recall_ref_source"
    r_ref_dataset = Dataset(r_reference, r_ref_source, None, None)

    existing_datasets = {
        g_reference: g_ref_dataset,
        r_reference: r_ref_dataset,
        a_name: a_dataset,
    }

    raw_eval_datasets = [
        {
            "name": g_name,
            "source": g_source,
            "reference": g_reference,
            "mappings": g_mappings,
        },
        {
            "name": r_name,
            "source": r_source,
            "description": r_description,
            "reference": r_reference,
            "mappings": r_mappings,
        },
        {
            "name": a_name,
            "mappings": a_mappings,
        },
    ]

    # Prepare expected outputs
    expected_mapped_datasets = [
        MappedDataset(g_mappings, g_dataset),
        MappedDataset(r_mappings, r_dataset),
        MappedDataset(a_mappings, a_dataset),
    ]

    # Check outputs
    mapped_datasets = _create_eval_datasets_and_default_mappings(
        raw_eval_datasets, existing_datasets
    )
    check_lists_equal(mapped_datasets, expected_mapped_datasets)

    assert mapped_datasets[0].dataset.is_eval()
    assert not mapped_datasets[0].dataset.get_local_source()

    assert mapped_datasets[1].dataset.is_eval()
    assert mapped_datasets[1].dataset.get_local_source() == os.path.join(
        "data", r_source
    )

    assert not mapped_datasets[2].dataset.is_eval()
    assert mapped_datasets[2].dataset.get_local_source(
        base_path="path"
    ) == os.path.join("path", "data", a_source)


@pytest.mark.parametrize(
    ("raw_datasets", "datasets", "error"),
    [
        ([{}], {}, "Dataset 'None' config missing parameter: name"),
        (
            [{"name": "groundedness"}],
            {},
            "Dataset 'groundedness' config missing parameter: mappings",
        ),
        (
            [
                {
                    "name": "groundedness",
                    "mappings": {},
                }
            ],
            {},
            "Dataset 'groundedness' config missing parameter: source",
        ),
        (
            [
                {
                    "name": "groundedness",
                    "source": "groundedness_source",
                    "mappings": {},
                }
            ],
            {},
            "Dataset 'groundedness' config missing parameter: reference",
        ),
        (
            [
                {
                    "name": "groundedness",
                    "source": "groundedness_source_2",
                    "mappings": {},
                }
            ],
            {
                "groundedness": Dataset(
                    "groundedness", "groundedness_source", None, None
                )
            },
            "Dataset 'groundedness' config is referencing an existing dataset so it doesn't support parameter: source",
        ),
        (
            [
                {
                    "name": "groundedness",
                    "reference": "groundedness_ref",
                    "mappings": {},
                }
            ],
            {
                "groundedness": Dataset(
                    "groundedness", "groundedness_source", None, None
                )
            },
            "Dataset 'groundedness' config is referencing an existing dataset so it doesn't support parameter: reference",
        ),
        (
            [
                {
                    "name": "groundedness",
                    "source": "groundedness_source",
                    "reference": "groundedness_ref",
                    "mappings": {},
                }
            ],
            {},
            "Referenced dataset 'groundedness_ref' not defined",
        ),
    ],
)
def test_create_eval_datasets_and_default_mappings_missing_parameters(
    raw_datasets: List[dict], datasets: dict[str:Dataset], error: str
):
    # Check that datasets with missing parameters raise an exception
    with pytest.raises(ValueError, match=error):
        _create_eval_datasets_and_default_mappings(raw_datasets, datasets)


def test_create_evaluators():
    # Prepare inputs
    g_eval_name = "groundedness_eval"
    g_eval_flow = "groundedness_eval_flow"
    r_eval_name = "recall_eval"

    g_ds_name = "groundedness"
    g_ds_source = "groundedness_source"
    g_ds_mappings = {"claim": "claim_mapping"}
    g_ds_reference = "groundedness_reference"
    g_ds_dataset = Dataset(g_ds_name, g_ds_source, None, g_ds_reference)

    g_ds_ref_source = "groundedness_ref_source"
    g_ds_ref_dataset = Dataset(g_ds_reference, g_ds_ref_source, None, None)

    r_ds_name = "recall"
    r_ds_source = "recall_source"
    r_ds_mappings = {"input": "input_mapping", "gt": "gt_mapping"}
    r_ds_dataset = Dataset(r_ds_name, r_ds_source, None, None)

    existing_datasets = {g_ds_reference: g_ds_ref_dataset, r_ds_name: r_ds_dataset}

    raw_evaluators = [
        {
            "name": g_eval_name,
            "flow": g_eval_flow,
            "datasets": [
                {
                    "name": g_ds_name,
                    "source": g_ds_source,
                    "reference": g_ds_reference,
                    "mappings": g_ds_mappings,
                }
            ],
        },
        {
            "name": r_eval_name,
            "datasets": [
                {
                    "name": r_ds_dataset.name,
                    "mappings": r_ds_mappings,
                }
            ],
        },
    ]

    # Test with base_path
    base_path = "/path/to/flow/"

    # Prepare expected outputs
    expected_evaluators = [
        Evaluator(
            g_eval_name,
            [MappedDataset(g_ds_mappings, g_ds_dataset)],
            os.path.join(base_path, "flows", g_eval_flow),
        ),
        Evaluator(
            r_eval_name,
            [MappedDataset(r_ds_mappings, r_ds_dataset)],
            os.path.join(base_path, "flows", r_eval_name),
        ),
    ]

    # Check outputs
    evaluators = _create_evaluators(raw_evaluators, existing_datasets, base_path)
    assert evaluators == expected_evaluators

    # Test without base_path
    base_path = None

    # Prepare expected outputs
    expected_evaluators = [
        Evaluator(
            g_eval_name,
            [MappedDataset(g_ds_mappings, g_ds_dataset)],
            os.path.join("flows", g_eval_flow),
        ),
        Evaluator(
            r_eval_name,
            [MappedDataset(r_ds_mappings, r_ds_dataset)],
            os.path.join("flows", r_eval_name),
        ),
    ]

    # Check outputs
    evaluators = _create_evaluators(raw_evaluators, existing_datasets, base_path)
    assert evaluators == expected_evaluators

    # Asset that the groundedness evaluator can match the standard dataset (g_ds_reference) to the evaluation dataset (g_ds_dataset)
    assert (
        evaluators[0].find_dataset_with_reference(g_ds_reference)
        == evaluators[0].datasets
    )

    # Asset that the recall evaluator can match the standard dataset (r_ds_name) to the standard/evaluation dataset (r_ds_dataset)
    assert (
        evaluators[1].find_dataset_with_reference(r_ds_name) == evaluators[1].datasets
    )


@pytest.mark.parametrize(
    ("raw_evaluators", "error"),
    [
        ([{}], "Evaluator 'None' config missing parameter: name"),
        (
            [
                {
                    "name": "groundedness",
                }
            ],
            "Evaluator 'groundedness' config missing parameter: datasets",
        ),
    ],
)
def test_create_evaluators_missing_parameters(raw_evaluators: List[dict], error: str):
    available_datasets = {
        "groundedness": Dataset("groundedness", "groundedness_source", None, None),
    }
    # Check that evaluators with missing parameters raise an exception
    with pytest.raises(ValueError, match=error):
        _create_evaluators(raw_evaluators, available_datasets, None)


def test_experiment_creation():
    # Prepare inputs
    base_path = str(RESOURCE_PATH)
    name = "exp_name"
    flow = "exp_flow"

    # Prepare expected outputs
    expected_flow_variants = [
        {"var_0": "node_var_0", "var_1": "node_var_0"},
        {"var_3": "node_var_1", "var_4": "node_var_1"},
    ]
    expected_flow_default_variants = {"node_var_0": "var_0", "node_var_1": "var_3"}
    expected_flow_llm_nodes = {
        "node_var_0",
        "node_var_1",
    }

    # Check outputs
    experiment = Experiment(base_path, name, flow, [], [], None)
    flow_detail = experiment.get_flow_detail()

    assert flow_detail.flow_path == os.path.join(base_path, "flows", flow)
    assert flow_detail.all_variants == expected_flow_variants
    assert flow_detail.default_variants == expected_flow_default_variants
    assert flow_detail.all_llm_nodes == expected_flow_llm_nodes


@pytest.fixture(scope="session")
def prepare_expected_experiment():
    # Prepare standard datasets
    base_path = str(RESOURCE_PATH)

    expected_dataset_mappings = [
        {"ds1_input": "ds1_mapping"},
        {"ds2_input": "ds2_mapping"},
    ]
    expected_datasets = [
        Dataset("ds1", "ds1_source", "ds1_description", None),
        Dataset("ds2", "ds2_source", None, None),
    ]
    expected_mapped_datasets = [
        MappedDataset(expected_dataset_mappings[0], expected_datasets[0]),
        MappedDataset(expected_dataset_mappings[1], expected_datasets[1]),
    ]

    # Prepare evaluator datasets
    expected_evaluator_mapped_datasets = [
        [
            MappedDataset(
                {"ds1_input": "ds1_mapping", "ds1_extra": "ds1_extra_mapping"},
                expected_datasets[0],
            ),
            MappedDataset(
                {"ds2_extra": "ds2_extra_mapping"},
                Dataset("ds3", "ds3_source", "ds3_description", "ds2"),
            ),
        ],
        [
            MappedDataset({"ds2_input": "ds2_diff_mapping"}, expected_datasets[1]),
            MappedDataset({}, Dataset("ds4", "ds4_source", None, "ds1")),
        ],
    ]

    # Prepare evaluators
    expected_evaluators = [
        Evaluator(
            "eval1",
            expected_evaluator_mapped_datasets[0],
            os.path.join(base_path, "flows", "eval1"),
        ),
        Evaluator(
            "eval2",
            expected_evaluator_mapped_datasets[1],
            os.path.join(base_path, "flows", "eval2"),
        ),
    ]

    yield expected_mapped_datasets, expected_evaluators


@pytest.fixture(scope="session")
def prepare_expected_overlay():
    # Prepare standard datasets
    base_path = str(RESOURCE_PATH)
    expected_dataset = Dataset("dsx", "dsx_source", None, None)
    expected_mapped_datasets = [
        MappedDataset({"dsx_input": "dsx_mapping"}, expected_dataset)
    ]

    # Prepare evaluator datasets
    expected_evaluator_mapped_datasets = [
        MappedDataset({"dsx_diff_input": "dsx_diff_mapping"}, expected_dataset),
        MappedDataset({}, Dataset("dsy", "dsy_source", None, "dsx")),
    ]

    # Prepare evaluators
    expected_evaluators = [
        Evaluator(
            "evalx",
            expected_evaluator_mapped_datasets,
            os.path.join(base_path, "flows", "evalx"),
        )
    ]
    yield expected_mapped_datasets, expected_evaluators


@pytest.fixture(scope="session")
def prepare_special_overlay_evaluators():
    # Prepare standard datasets
    base_path = str(RESOURCE_PATH)

    # Prepare evaluator datasets
    expected_evaluator_mapped_datasets = [
        MappedDataset(
            {"ds1_diff_input": "ds1_diff_mapping"},
            Dataset("ds1", "ds1_source", "ds1_description", None),
        )
    ]

    # Prepare evaluators
    expected_evaluators = [
        Evaluator(
            "evalx",
            expected_evaluator_mapped_datasets,
            os.path.join(base_path, "flows", "evalx"),
        )
    ]
    yield expected_evaluators


def test_load_base_experiment(prepare_expected_experiment):
    # Prepare inputs
    base_path = str(RESOURCE_PATH)
    exp_file_path = os.path.join(base_path, "experiment.yaml")

    # Prepare expected outputs
    expected_name = "exp"
    expected_flow = "exp_flow"
    expected_runtime = "runtime_name"

    expected_mapped_datasets, expected_evaluators = prepare_expected_experiment

    # Test
    experiment = _load_base_experiment(exp_file_path, base_path)

    # Check outputs
    assert experiment.base_path == base_path
    assert experiment.name == expected_name
    assert experiment.flow == expected_flow
    assert experiment.datasets == expected_mapped_datasets
    assert experiment.evaluators == expected_evaluators
    assert experiment.runtime == expected_runtime


def test_apply_overlay(
    prepare_expected_experiment,
    prepare_expected_overlay,
    prepare_special_overlay_evaluators,
):
    # Prepare inputs
    base_path = str(RESOURCE_PATH)
    exp_file_path = os.path.join(base_path, "experiment.yaml")
    experiment = _load_base_experiment(exp_file_path, base_path)

    # Prepare expected results
    expected_name = "exp"
    expected_flow = "exp_flow"
    base_mapped_datasets, base_evaluators = prepare_expected_experiment
    overlay_mapped_datasets, overlay_evaluators = prepare_expected_overlay

    # Test dev0
    overlay_path = os.path.join(base_path, "experiment.dev0.yaml")
    dev_experiment = copy.deepcopy(experiment)
    _apply_overlay(dev_experiment, overlay_path, base_path)

    # Check outputs
    assert dev_experiment.base_path == base_path
    assert dev_experiment.name == expected_name
    assert dev_experiment.flow == expected_flow
    assert dev_experiment.datasets == overlay_mapped_datasets
    assert dev_experiment.evaluators == overlay_evaluators
    assert dev_experiment.runtime == "overridden_runtime"

    # Test dev1
    overlay_path = os.path.join(base_path, "experiment.dev1.yaml")
    dev_experiment = copy.deepcopy(experiment)
    _apply_overlay(dev_experiment, overlay_path, base_path)

    # Check outputs
    assert dev_experiment.base_path == base_path
    assert dev_experiment.name == expected_name
    assert dev_experiment.flow == expected_flow
    assert dev_experiment.datasets == overlay_mapped_datasets
    assert dev_experiment.evaluators == base_evaluators
    assert dev_experiment.runtime == "runtime_name"

    # Test dev2
    overlay_path = os.path.join(base_path, "experiment.dev2.yaml")
    dev_experiment = copy.deepcopy(experiment)
    _apply_overlay(dev_experiment, overlay_path, base_path)

    # Check outputs
    assert dev_experiment.base_path == base_path
    assert dev_experiment.name == expected_name
    assert dev_experiment.flow == expected_flow
    assert dev_experiment.datasets == base_mapped_datasets
    assert dev_experiment.evaluators == prepare_special_overlay_evaluators
    assert dev_experiment.runtime is None

    # Test dev3
    overlay_path = os.path.join(base_path, "experiment.dev3.yaml")
    dev_experiment = copy.deepcopy(experiment)
    _apply_overlay(dev_experiment, overlay_path, base_path)

    # Check outputs
    assert dev_experiment.base_path == base_path
    assert dev_experiment.name == expected_name
    assert dev_experiment.flow == expected_flow
    assert dev_experiment.datasets == []
    assert dev_experiment.evaluators == []
    assert dev_experiment.runtime == "runtime_name"


def test_load_experiment(prepare_expected_experiment):
    # Prepare inputs
    base_path = str(RESOURCE_PATH)

    # Prepare expected outputs
    expected_name = "exp"
    expected_flow = "exp_flow"

    expected_mapped_datasets, expected_evaluators = prepare_expected_experiment

    # Test
    experiment = load_experiment("experiment.yaml", base_path)

    # Check outputs
    assert experiment.base_path == base_path
    assert experiment.name == expected_name
    assert experiment.flow == expected_flow
    assert experiment.datasets == expected_mapped_datasets
    assert experiment.evaluators == expected_evaluators
    assert experiment.runtime == "runtime_name"


def test_load_experiment_with_overlay(prepare_expected_overlay):
    # Prepare inputs
    base_path = str(RESOURCE_PATH)

    # Prepare expected outputs
    expected_name = "exp"
    expected_flow = "exp_flow"

    expected_mapped_datasets, expected_evaluators = prepare_expected_overlay

    # Test
    experiment = load_experiment("experiment.yaml", base_path, "dev0")

    # Check outputs
    assert experiment.base_path == base_path
    assert experiment.name == expected_name
    assert experiment.flow == expected_flow
    assert experiment.datasets == expected_mapped_datasets
    assert experiment.evaluators == expected_evaluators
    assert experiment.runtime == "overridden_runtime"
