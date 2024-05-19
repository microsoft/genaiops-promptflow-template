# The llmops_config.yaml file

The `llmops_config.yaml` is used to configure LLM Ops configuration to an use-case. At least one it configures:
- azure configuration under azure_config
- promptflow connections configuration under connections block
- base experiment configuration under experiment block
- environments configuration for usecase in environments block
    -  experiment overlay configuration that overrides the parameters in base experiment block
    -  deployment configurations in deployment_configs block

Examples of the file are provided for the [named_entity_recognition](../named_entity_recognition/llmops_config.yaml), [math_coding](../math_coding/llmops_config.yaml) and [web classification](../web_classification/llmops_config.yaml).


