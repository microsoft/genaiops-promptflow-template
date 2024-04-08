import pytest
from llmops.common.experiment_cloud_config import (
    ExperimentCloudConfig,
    _try_get_env_var,
    _get_optional_env_var,
)


def test_try_get_env_var(monkeypatch: pytest.MonkeyPatch):
    env_var_key = "TEST_ENV_VAR"
    env_var_val = "test_value"

    monkeypatch.setenv(env_var_key, env_var_val)
    assert _try_get_env_var(env_var_key) == env_var_val

    monkeypatch.setenv(env_var_key, "")
    with pytest.raises(
        ValueError,
        match=f"Environment variable '{env_var_key}' is not set or is empty.",
    ):
        _try_get_env_var(env_var_key)

    monkeypatch.delenv(env_var_key)
    with pytest.raises(
        ValueError,
        match=f"Environment variable '{env_var_key}' is not set or is empty.",
    ):
        _try_get_env_var(env_var_key)


def test_get_optional_env_var(monkeypatch: pytest.MonkeyPatch):
    env_var_key = "TEST_ENV_VAR"
    env_var_val = "test_value"

    monkeypatch.setenv(env_var_key, env_var_val)
    assert _get_optional_env_var(env_var_key) == env_var_val

    monkeypatch.setenv(env_var_key, "")
    assert _get_optional_env_var(env_var_key) is None

    monkeypatch.delenv(env_var_key)
    assert _get_optional_env_var(env_var_key) is None


def test_experiment_cloud_config(monkeypatch: pytest.MonkeyPatch):
    subscription_id = "subscription_id"
    rg_name = "rg_name"
    ws_name = "ws_name"
    env_name = "dev"

    # Check works with arguments
    monkeypatch.setenv("SUBSCRIPTION_ID", "")
    monkeypatch.setenv("RESOURCE_GROUP_NAME", "")
    monkeypatch.setenv("WORKSPACE_NAME", "")
    monkeypatch.setenv("ENV_NAME", "")
    config = ExperimentCloudConfig(subscription_id, rg_name, ws_name, env_name)
    assert config.subscription_id == subscription_id
    assert config.resource_group_name == rg_name
    assert config.workspace_name == ws_name
    assert config.environment_name == env_name

    # Check fails without arguments or environment variables
    with pytest.raises(
        ValueError,
        match="Environment variable 'SUBSCRIPTION_ID' is not set or is empty.",
    ):
        ExperimentCloudConfig()

    # Check fails without RESOURCE_GROUP_NAME
    monkeypatch.setenv("SUBSCRIPTION_ID", subscription_id)
    monkeypatch.setenv("RESOURCE_GROUP_NAME", "")
    monkeypatch.setenv("WORKSPACE_NAME", "")
    with pytest.raises(
        ValueError,
        match="Environment variable 'RESOURCE_GROUP_NAME' is not set or is empty.",
    ):
        ExperimentCloudConfig()

    # Check fails without WORKSPACE_NAME
    monkeypatch.setenv("SUBSCRIPTION_ID", subscription_id)
    monkeypatch.setenv("RESOURCE_GROUP_NAME", rg_name)
    monkeypatch.setenv("WORKSPACE_NAME", "")
    with pytest.raises(
        ValueError,
        match="Environment variable 'WORKSPACE_NAME' is not set or is empty.",
    ):
        ExperimentCloudConfig()

    # Check works wth environment variables
    monkeypatch.setenv("SUBSCRIPTION_ID", subscription_id)
    monkeypatch.setenv("RESOURCE_GROUP_NAME", rg_name)
    monkeypatch.setenv("WORKSPACE_NAME", ws_name)
    monkeypatch.setenv("ENV_NAME", env_name)
    config = ExperimentCloudConfig()
    assert config.subscription_id == subscription_id
    assert config.resource_group_name == rg_name
    assert config.workspace_name == ws_name
    assert config.environment_name == env_name
