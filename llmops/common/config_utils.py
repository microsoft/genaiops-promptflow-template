"""Configuration utils to load config from yaml"""
import os
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv
import yaml


class ExperimentConfig:
    """ExperimentConfig Class."""
    _raw_config: Any

    def __init__(
        self, 
        flow_name: str = "",
        environment: str = None
    ):
        """Intialize raw config with yaml config data."""
        config_path = "experiment.yaml"
        flow_name = flow_name.strip('./')
        self._exp_config_path = Path(flow_name, config_path)
        if self._exp_config_path.is_file():
            self._raw_config = self.load_yaml(self._exp_config_path)
        self._environment = environment
        if self._environment:
            self._env_exp_config_path = Path(flow_name, f'experiment_{self._environment}.yaml')
            if self._env_exp_config_path.is_file():
                self._env_exp_config = self.load_yaml(self._env_exp_config_path)
        
      
    def load_yaml(self, config_path: str) -> Any:
        """Load yaml file config"""
        load_dotenv()
        raw_config = None
        with open(config_path, "r", encoding="utf-8") as stream:
            raw_config = yaml.safe_load(os.path.expandvars(stream.read()))
        return raw_config

        
    def __getattr__(self, __name: str) -> Any:
        """Get values for top level keys in configuration."""
        print(__name)
        return self._raw_config[__name]
    

    @property
    def base_exp_config(self):
        return self._raw_config
    
    @property
    def azure_config(self):
        """Get azure workspace config"""
        if 'azure_config' in self.base_exp_config:
            return self.base_exp_config['azure_config']
        else:
            return None

    @property
    def connections(self):
        """Get connections configuration"""
        if 'connections' in self.base_exp_config:
            return self.base_exp_config['connections']
    
    @property
    def env_config(self):
        """Get environment configuration."""
        return self._env_exp_config

    
    @property
    def base_experiment_config(self):
        if 'experiment_config' in self.base_exp_config:
            return self.base_exp_config['experiment_config']
        else:
            return None
    
    @property
    def overlay_experiment_config(self):
        if 'experiment_config' in self._env_exp_config:
            return self._env_exp_config['experiment_config']
        else:
            return None
    
    @property
    def evaluators_config(self):
        """Get evaluator configuration."""
        if self.overlay_experiment_config and 'evaluators' in self.overlay_experiment_config:
            return self.overlay_experiment_config['evaluators']
        else:
            return None
    
    @property
    def deployment_configs(self):
        """Get deployment configuration."""
        if 'deployment_configs' in self._env_exp_config:
            return self._env_exp_config['deployment_configs']
        else:
            return None

    @property
    def azure_managed_endpoint_config(self):
        """Get azure managed endpoint deployment configuration."""
        if 'deployment_configs' in self._env_exp_config and 'azure_managed_endpoint' in self._env_exp_config['deployment_configs']:
            return self._env_exp_config['deployment_configs']['azure_managed_endpoint']
        else:
            return None
    
    @property
    def kubernetes_endpoint_config(self):
        """Get kubernetes endpoint deployment configuration."""
        if 'deployment_configs' in self._env_exp_config and 'kubernetes_endpoint' in self._env_exp_config['deployment_configs']:
            return self._env_exp_config['deployment_configs']['kubernetes_endpoint']
        else:
            return None
    
    @property
    def webapp_endpoint_config(self):
        """Get webapp endpoint deployment configuration."""
        if 'deployment_configs' in self._env_exp_config and 'webapp_endpoint' in self._env_exp_config['deployment_configs']:
            return self._env_exp_config['deployment_configs']['webapp_endpoint']
        return None
    

if __name__ == "__main__":
    config = ExperimentConfig(flow_name="web_classification", environment="dev")
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