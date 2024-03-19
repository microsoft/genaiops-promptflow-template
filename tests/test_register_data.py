from pathlib import Path
from unittest.mock import ANY, Mock, patch

import pytest
from llmops.common.register_data_asset import register_data_asset, generate_file_hash

THIS_PATH = Path(__file__).parent
RESOURCE_PATH = THIS_PATH / "resources"


@pytest.fixture(scope="module", autouse=True)
def _set_required_env_vars():
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("SUBSCRIPTION_ID", "TEST_SUBSCRIPTION_ID")
    monkeypatch.setenv("RESOURCE_GROUP_NAME", "TEST_RESOURCE_GROUP_NAME")
    monkeypatch.setenv("WORKSPACE_NAME", "TEST_WORKSPACE_NAME")


def test_register_data_asset():
    data_path = str(RESOURCE_PATH / "data/data.jsonl")
    data_hash = generate_file_hash(data_path)
    with patch("llmops.common.register_data_asset.MLClient") as mock_ml_client:
        # Mock the MLClient
        ml_client_instance = Mock()
        mock_ml_client.return_value = ml_client_instance

        # Mock available data asset
        mock_data = Mock()
        mock_data.tags.return_value = {}
        ml_client_instance.data.get.return_value = mock_data

        # Register data asset
        register_data_asset(
            exp_filename="experiment_2.yaml",
            base_path=str(RESOURCE_PATH),
            env_name="dev",
        )

        # Assert that ml_client.data.create_or_update is called
        ml_client_instance.data.create_or_update.assert_called_with(ANY)

        # Assert that ml_client.data.create_or_update is called with the correct argument
        created_data = ml_client_instance.data.create_or_update.call_args.args[0]
        assert created_data.name == "ds1"
        assert created_data.path == data_path
        assert created_data.tags["data_hash"] == data_hash


def test_register_existing_data_asset():
    data_path = str(RESOURCE_PATH / "data/data.jsonl")
    data_hash = generate_file_hash(data_path)
    with patch("llmops.common.register_data_asset.MLClient") as mock_ml_client:
        # Mock the MLClient
        ml_client_instance = Mock()
        mock_ml_client.return_value = ml_client_instance

        # Mock available data asset
        mock_data = Mock()
        mock_data.tags = {"data_hash": data_hash}
        ml_client_instance.data.get.return_value = mock_data

        # Register data asset
        register_data_asset(
            exp_filename="experiment_2.yaml",
            base_path=str(RESOURCE_PATH),
            env_name="dev",
        )

        # Assert that ml_client.data.create_or_update is not called
        ml_client_instance.data.create_or_update.assert_not_called()
