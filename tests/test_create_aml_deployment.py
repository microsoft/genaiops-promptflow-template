"""Tests for create_aml_deployment.py."""
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from llmops.common.deployment.provision_deployment import create_deployment

SUBSCRIPTION_ID = "TEST_SUBSCRIPTION_ID"
RESOURCE_GROUP_NAME = "TEST_RESOURCE_GROUP_NAME"
WORKSPACE_NAME = "TEST_WORKSPACE_NAME"

THIS_PATH = Path(__file__).parent
RESOURCE_PATH = THIS_PATH / "resources"

REQUEST_TIMEOUT_MS = 3 * 60 * 1000


@pytest.fixture(scope="module", autouse=True)
def _set_required_env_vars():
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("SUBSCRIPTION_ID", "TEST_SUBSCRIPTION_ID")
    monkeypatch.setenv("RESOURCE_GROUP_NAME", "TEST_RESOURCE_GROUP_NAME")
    monkeypatch.setenv("WORKSPACE_NAME", "TEST_WORKSPACE_NAME")


def test_create_kubernetes_deployment():
    """Test create_kubernetes_deployment."""
    model_name = "exp_dev"
    model_version = "1"
    endpoint_name = "test-endpoint"
    prior_deployment_name = "test-prior-deployment"
    deployment_name = "test-deployment"
    deployment_description = "test-deployment-description"
    deployment_vm_size = "test-vm-size"
    deployment_instance_count = 1
    deployment_config = {
        "liveness_route": {"path": "/health", "port": "8080"},
        "readiness_route": {"path": "/health", "port": "8080"},
        "scoring_route": {"path": "/score", "port": "8080"},
    }

    with patch(
        "llmops.common.deployment.provision_deployment.MLClient"
    ) as mock_ml_client:
        # Mock the MLClient
        ml_client_instance = Mock()
        mock_ml_client.return_value = ml_client_instance

        # Mock model get
        ml_client_instance.models.get.return_value = Mock()

        # Mock deployment list
        mock_deployment = Mock()
        mock_old_deployment = Mock()
        mock_deployment.name = deployment_name
        mock_old_deployment.name = prior_deployment_name
        ml_client_instance.online_deployments.list.return_value = [
            mock_deployment,
            mock_old_deployment,
        ]

        # Create the deployment
        create_deployment(
            model_version,
            base_path=str(RESOURCE_PATH),
            env_name="dev"
        )

        # Assert ml_client.models.get is called with the expected arguments
        ml_client_instance.models.get.assert_called_with(
            model_name,
            model_version
        )

        # Assert online_deployments.list is called with the expected arguments
        ml_client_instance.online_deployments.list.assert_called_with(
            endpoint_name, local=False
        )

        # Assert online_deployments.begin_create_or_update is called once
        create_deployment_calls = (
            ml_client_instance.online_deployments.begin_create_or_update
        )
        assert create_deployment_calls.call_count == 1

        # Assert that ml_client.online_endpoints.begin_create_or_update
        # is called with the correct arguments

        # create_endpoint_calls.call_args_list is triple nested,
        # first index: select the call of
        # ml_client.online_deployments.begin_create_or_update [0]
        # second index: select the argument of
        # ml_client.online_deployments.begin_create_or_update [0 (deployment)]
        # third index: select the first element of the tuple [0]
        created_deployment = create_deployment_calls.call_args_list[0][0][0]
        assert created_deployment.name == deployment_name
        assert created_deployment.description == deployment_description
        assert created_deployment.endpoint_name == endpoint_name
        assert created_deployment.instance_type == deployment_vm_size
        assert created_deployment.instance_count == deployment_instance_count
        assert created_deployment.app_insights_enabled is True

        assert created_deployment.environment.name == deployment_name
        assert created_deployment.environment.build.path == str(
            RESOURCE_PATH / "flows/exp_flow"
        )
        assert (
            created_deployment.environment.build.dockerfile_path == (
                "docker/dockerfile"
            )
        )
        assert created_deployment.environment.inference_config == (
            deployment_config
        )

        assert (
            created_deployment.request_settings.request_timeout_ms
            == REQUEST_TIMEOUT_MS
        )

        env_vars = created_deployment.environment_variables
        assert env_vars["test-key"] == "test-value"
        assert env_vars["PROMPTFLOW_RUN_MODE"] == "serving"

        expected_deployment_config = (
            f"deployment.subscription_id={SUBSCRIPTION_ID},"
            f"deployment.resource_group={RESOURCE_GROUP_NAME},"
            f"deployment.workspace_name={WORKSPACE_NAME},"
            f"deployment.endpoint_name={endpoint_name},"
            f"deployment.deployment_name={deployment_name}"
        )
        assert env_vars["PRT_CONFIG_OVERRIDE"] == expected_deployment_config

        # Assert online_endpoints.begin_create_or_update is called twice
        update_endpoint_calls = ml_client_instance.begin_create_or_update
        assert update_endpoint_calls.call_count == 1

        # Assert that ml_client.online_endpoints.begin_create_or_update
        # is called with the correct argument

        # update_endpoint_calls.call_args_list is triple nested,
        # first index: select the call of
        # ml_client.online_endpoints.begin_create_or_update [0]
        # second index: select the argument of
        # ml_client.online_endpoints.begin_create_or_update [0 (endpoint)]
        # third index: select the first element of the tuple [0]
        updated_endpoint = update_endpoint_calls.call_args_list[0][0][0]
        assert int(updated_endpoint.traffic[deployment_name]) == 90
        assert int(updated_endpoint.traffic[prior_deployment_name]) == 10
