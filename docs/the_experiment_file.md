# The experiment.yaml file

## The base file 

The `experiment.yaml` is used to configure an LLM use-case. At least one `experiment.yaml` file is needed per use-case and it configures:
- The use-case (experiment) name (`name` block)
- The path to the "standard" use-case flow (`flow` block)
- The datasets used to test the flow (`datasets` block)
- The path(s) to the "evaluation" flows of the use-case (`evaluators` block)
- The datasets used to evaluate the flow (also `evaluators` block)
- The Prompt Flow runtime used to run the standard and evaluation flows (`runtime` block)  

The full specification of the `experiment.yaml` file can be found [here](./experiment.yaml).
Examples of the file are provided for the [named_entity_recognition](../named_entity_recognition/experiment.yaml), [math_coding](../math_coding/experiment.yaml) and [web classification](../web_classification/experiment.yaml).

## The overlay file(s)

The `experiment.yaml` file is used as the base file for all environments. To change the configurations of a use-case for a specific environment, you can create an "overlay" file `experiment.<env>.yaml`.

For example if you want to change the configurations for the "dev" environment you can create a `experiment.dev.yaml` file. In this file, you can specify a new `datasets`, `evaluators` and/or `runtime`. You can not change the `name` and `flow` parameters, those will always be read from the base `experiment.yaml` file. 

If any of the `datasets`, `evaluators`, or `runtime` blocks are present in an overlay file (`experiment.<env>.yaml`), the corresponding block from the base file will be ignored and the block from the overlay file will be used for that environment. 

If no overlay file (`experiment.<env>.yaml`) is present for a given environment, the base file (`experiment.yaml`) will be used.