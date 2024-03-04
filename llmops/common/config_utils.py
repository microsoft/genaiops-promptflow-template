"""Configuration utils to load config from yaml/json."""
import os
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv
import yaml


class LLMOpsConfig:
    """LLMOpsConfig Class."""

    _raw_config: Any

    def __init__(
        self, 
        flow_name: str = "",
        environment: str = "pr", 
        config_path: str = "configs/llmops_config.yaml"
    ):
        """Intialize MLConfig with yaml config data."""
        self.config_path = Path(flow_name, config_path)
        self._environment = environment
        load_dotenv()

        with open(self.config_path, "r", encoding="utf-8") as stream:
            self._raw_config = yaml.safe_load(os.path.expandvars(stream.read()))

    def __getattr__(self, __name: str) -> Any:
        """Get values for top level keys in configuration."""
        return self._raw_config[__name]
    
    @property
    def model_config(self):
        """Get model configuration."""
        return self._raw_config['llmops_config'][self._environment]
    
    @property
    def mapping_config(self):
        """Get dataset mapping configuration."""
        return self._raw_config['llmops_config']['mapping_config']
    
    @property
    def deployment_configs(self):
        """Get webapp endpoint deployment configuration."""
        return self.model_config['deployment_configs']

    @property
    def datasets_config(self):
        """Get datasets configuration."""
        return self.model_config['datasets_config']

    @property
    def azure_managed_endpoint_config(self):
        """Get azure managed endpoint deployment configuration."""
        return self.model_config['deployment_configs']['azure_managed_endpoint']
    
    @property
    def kubernetes_endpoint_config(self):
        """Get kubernetes endpoint deployment configuration."""
        return self.model_config['deployment_configs']['kubernetes_endpoint']
    
    @property
    def webapp_endpoint_config(self):
        """Get webapp endpoint deployment configuration."""
        return self.model_config['deployment_configs']['webapp_endpoint']
    


if __name__ == "__main__":
    config = LLMOpsConfig(flow_name="web_classification", environment="dev")
    print(config.model_config)
    print(config.datasets_config)
    print(config.deployment_configs)
    print(config.mapping_config)
    print(config.azure_managed_endpoint_config)
    print(config.kubernetes_endpoint_config)
    print(config.webapp_endpoint_config)
    print(config.webapp_endpoint_config['CONNECTION_NAMES'])
    for connection in config.webapp_endpoint_config['CONNECTION_NAMES']:
        print(connection)
