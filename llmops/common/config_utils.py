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
        config_path: str = "llmops_config.yaml"
    ):
        """Intialize MLConfig with yaml config data."""
        flow_name = flow_name.strip('./')
        self.config_path = Path(flow_name, config_path)
        self._environment = environment
        load_dotenv()

        with open(self.config_path, "r", encoding="utf-8") as stream:
            self._raw_config = yaml.safe_load(os.path.expandvars(stream.read()))

    def __getattr__(self, __name: str) -> Any:
        """Get values for top level keys in configuration."""
        return self._raw_config[__name]
    
    @property
    def azure_config(self):
        """Get azure workspace config"""
        return self._raw_config['azure_config']

    @property
    def connections(self):
        """Get connections configuration"""
        return self._raw_config['connections']
    
    @property
    def env_config(self):
        """Get environment configuration."""
        return self._raw_config['environments'][self._environment]
    
    @property
    def base_experiment_config(self):
        if 'experiment' in self._raw_config:
            return self._raw_config['experiment']
        else:
            return None
    
    @property
    def overlay_experiment_config(self):
        if 'experiment' in self.env_config:
            return self.env_config['experiment']
        else:
            return None
    
    @property
    def evaluators_config(self):
        """Get evaluator configuration."""
        return self.overlay_experiment_config['evaluators']
    
    @property
    def deployment_configs(self):
        """Get deployment configuration."""
        if 'deployment_configs' in self.env_config:
            return self.env_config['deployment_configs']
        else:
            return None

    @property
    def azure_managed_endpoint_config(self):
        """Get azure managed endpoint deployment configuration."""
        if 'deployment_configs' in self.env_config and 'azure_managed_endpoint' in self.env_config['deployment_configs']:
            return self.env_config['deployment_configs']['azure_managed_endpoint']
        else:
            return None
    
    @property
    def kubernetes_endpoint_config(self):
        """Get kubernetes endpoint deployment configuration."""
        if 'deployment_configs' in self.env_config and 'kubernetes_endpoint' in self.env_config['deployment_configs']:
            return self.env_config['deployment_configs']['kubernetes_endpoint']
        else:
            return None
    
    @property
    def webapp_endpoint_config(self):
        """Get webapp endpoint deployment configuration."""
        if 'deployment_configs' in self.env_config and 'webapp_endpoint' in self.env_config['deployment_configs']:
            return self.env_config['deployment_configs']['webapp_endpoint']
        return None
    

if __name__ == "__main__":
    config = LLMOpsConfig(flow_name="math_coding", environment="pr")
    print(config.azure_config)
    print(config.connections)
    print(config.env_config)
    print(config.base_experiment_config)
    print(config.overlay_experiment_config)
    print(config.evaluators_config)
    print(config.deployment_configs)
    print(config.azure_managed_endpoint_config)
    print(config.kubernetes_endpoint_config)
    print(config.webapp_endpoint_config)
    if config.webapp_endpoint_config:
        for webapp_endpoint in config.webapp_endpoint_config:
            print(webapp_endpoint['CONNECTION_NAMES'])
