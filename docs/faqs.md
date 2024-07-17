# Frequently Asked Questions (FAQs)

## Table of Contents

* [Frequently Asked Questions (FAQs)](#frequently-asked-questions-faqs)
  * [Supported Azure Services](#supported-azure-services)
    * [Which Azure Services are supported?](#which-azure-services-are-supported)
    * [How to use Azure AI Studio?](#how-to-use-azure-ai-studio)
    * [How to use Azure Machine Learning?](#how-to-use-azure-machine-learning)
  * [Prompt Flow Runtime](#prompt-flow-runtime)
    * [Can I use serverless or automatic runtime?](#can-i-use-serverless-or-automatic-runtime)
    * [Can I use dedicated runtime?](#can-i-use-dedicated-runtime)
  * [Python dependencies](#python-dependencies)
    * [Where are python dependencies defined?](#where-are-python-dependencies-defined)
    * [How to install python dependencies locally?](#how-to-install-python-dependencies-locally)
  * [Environmental Variables](#environmental-variables)
    * [How to pass config values to Flows?](#how-to-pass-config-values-to-flows)
    * [What is an example of ENV_VARS value?](#what-is-an-example-of-env_vars-value)
    * [What is an example of .env file?](#what-is-an-example-of-env-file)
    * [What values should go into .env file and ENV_VARS ?](#what-values-should-go-into-env-file-and-env_vars-)
  * [Experiments](#experiments)
    * [How are experiments defined?](#how-are-experiments-defined)
    * [How to run an experiment?](#how-to-run-an-experiment)
    * [How to define different experiments for different environments?](#how-to-define-different-experiments-for-different-environments)
    * [What types of standard flows are supported?](#what-types-of-standard-flows-are-supported)
    * [How to run an experiments locally?](#how-to-run-an-experiments-locally)
    * [How to run an experiments on Azure from local machine?](#how-to-run-an-experiments-on-azure-from-local-machine)
  * [Evaluations](#evaluations)
    * [How are evaluations defined?](#how-are-evaluations-defined)
    * [How to run an evaluation locally?](#how-to-run-an-evaluation-locally)
    * [How to run an evaluation on Azure from local machine?](#how-to-run-an-evaluation-on-azure-from-local-machine)
    * [What types of evaluation flows are supported?](#what-types-of-evaluation-flows-are-supported)
    * [How are experiments defined?](#how-are-experiments-defined-1)
    * [How many evaluators can be defined for an experiment?](#how-many-evaluators-can-be-defined-for-an-experiment)
    * [How to define different evaluators for different environments?](#how-to-define-different-evaluators-for-different-environments)
  * [Connections](#connections)
    * [What connections are supported?](#what-connections-are-supported)
    * [How to configure connections?](#how-to-configure-connections)
    * [How do I provide value for ${api_key}?](#how-do-i-provide-value-for-api_key)
    * [How to use connections in the experiment?](#how-to-use-connections-in-the-experiment)
    * [How to add new connection types?](#how-to-add-new-connection-types)
    * [What is the schema for the connections?](#what-is-the-schema-for-the-connections)
  * [Configurations](#configurations)
    * [What configurations are needed for running the flow on Azure?](#what-configurations-are-needed-for-running-the-flow-on-azure)
    * [What configurations are needed for running the flow locally?](#what-configurations-are-needed-for-running-the-flow-locally)
  * [Deployments](#deployments)
    * [What is the purpose of the deployment.json file?](#what-is-the-purpose-of-the-deploymentjson-file)
    * [What are the different types of endpoints supported?](#what-are-the-different-types-of-endpoints-supported)
    * [How do I configure an Azure Managed Endpoint?](#how-do-i-configure-an-azure-managed-endpoint)
    * [What is the significance of CURRENT_DEPLOYMENT_TRAFFIC_ALLOCATION?](#what-is-the-significance-of-currentdeploymenttraffic_allocation)
    * [How do I allocate traffic during a deployment update?](#how-do-i-allocate-traffic-during-a-deployment-update)
    * [How do I configure a Kubernetes Endpoint?](#how-do-i-configure-a-kubernetes-endpoint)
    * [How do I configure a WebApp Endpoint?](#how-do-i-configure-a-webapp-endpoint)
    * [What is the role of CONNECTION_NAMES in WebApp Endpoint configuration?](#what-is-the-role-of-connection_names-in-webapp-endpoint-configuration)
    * [Can I define multiple endpoints in the same configuration file?](#can-i-define-multiple-endpoints-in-the-same-configuration-file)
    * [Does Webapp and managed endpoints uses FASTApi?](#does-webapp-and-managed-endpoints-uses-fastapi)
  * [Datasets](#datasets)
    * [What is the purpose of the datasets section in experiments.yaml?](#what-is-the-purpose-of-the-datasets-section-in-experimentsyaml)
    * [What is the difference between source and reference in the datasets configuration?](#what-is-the-difference-between-source-and-reference-in-the-datasets-configuration)
    * [How should I configure datasets when the evaluation flow uses a different but related dataset?](#how-should-i-configure-datasets-when-the-evaluation-flow-uses-a-different-but-related-dataset)
    * [How should I configure datasets when the evaluation flow uses the same dataset as the standard flow?](#how-should-i-configure-datasets-when-the-evaluation-flow-uses-the-same-dataset-as-the-standard-flow)
    * [What should I do if my evaluation flow is not recognizing the dataset?](#what-should-i-do-if-my-evaluation-flow-is-not-recognizing-the-dataset)
    * [How do I handle multiple datasets in the same configuration?](#how-do-i-handle-multiple-datasets-in-the-same-configuration)
    * [Can I use multiple evaluators with different datasets?](#can-i-use-multiple-evaluators-with-different-datasets)
  * [Docker usage](#docker-usage)
    * [Why do I have a docker folder with dockerfile in each standard flow?](#why-do-i-have-a-docker-folder-with-dockerfile-in-each-standard-flow)
    * [Why do I have a dockerfile within environment folder?](#why-do-i-have-a-dockerfile-within-environment-folder)
    * [Can the docker image be deployed elsewhere?](#can-the-docker-image-be-deployed-elsewhere)
  * [Troubleshooting](#troubleshooting)
    * [How do I troubleshoot a failed experiment?](#how-do-i-troubleshoot-a-failed-experiment)
    * [How do I troubleshoot a failed evaluation?](#how-do-i-troubleshoot-a-failed-evaluation)
    * [How do I troubleshoot a failed deployment?](#how-do-i-troubleshoot-a-failed-deployment)
    * [How do I troubleshoot a failed local connection?](#how-do-i-troubleshoot-a-failed-local-connection)

## Supported Azure Services

### Which Azure Services are supported?
The template supports the following Azure Services:
- `Azure AI Studio`
- `Azure Machine Learning`

`Workspace name` and `Project name` are used interchangeably in the template to align to both Azure AI Studio and Azure Machine Learning. When using Azure AI Studio, the WORKSPACE_NAME should point to AI STUDIO PROJECT NAME. When using Azure Machine Learning, the WORKSPACE_NAME should point to AML WORKSPACE NAME. The RESOURCE_GROUP_NAME should point to the resource group where the AI STUDIO PROJECT or AML Resource is located. The `SUBSCRIPTION_ID` should point to the subscription id where the AI STUDIO PROJECT or AML resource is located. The `KEY_VAULT_NAME` should point to the key vault associated with AI Studio or AML Workspace.

### How to use Azure AI Studio?
Add the following environment variable for each environment (e.g. pr, dev, prod) in github, each environment specific library variable in Azure DevOps and within .env file for local execution. This will be used to authenticate with Azure AI Studio. The `WORKSPACE_NAME` should point to AI STUDIO PROJECT NAME. The `RESOURCE_GROUP_NAME` should point to the resource group where the AI STUDIO PROJECT is located. The `SUBSCRIPTION_ID` should point to the subscription id where the `AI STUDIO PROJECT` is located. The `KEY_VAULT_NAME` should point to the key vault associated with AI Studio. For example:

- SUBSCRIPTION_ID=xxx
- KEY_VAULT_NAME=xxx
- WORKSPACE_NAME=xxx
- RESOURCE_GROUP_NAME=xxx

for .env file
```.env

KEY_VAULT_NAME=xxx
WORKSPACE_NAME=xxx
RESOURCE_GROUP_NAME=xxx
SUBSCRIPTION_ID=xxx

```

### How to use Azure Machine Learning?
Add the following environment variable for each environment (e.g. pr, dev, prod) in github, each environment specific library variable in Azure DevOps and within .env file for local execution. This will be used to authenticate with Azure machine learning workspace. The `WORKSPACE_NAME` should point to AML WORKSPACE NAME. The `RESOURCE_GROUP_NAME` should point to the resource group where the AML Resource is located. The `SUBSCRIPTION_ID` should point to the subscription id where the AML resource is located. The `KEY_VAULT_NAME` should point to the key vault associated with AMl Workspace. For example:

- SUBSCRIPTION_ID=xxx
- KEY_VAULT_NAME=xxx
- WORKSPACE_NAME=xxx
- RESOURCE_GROUP_NAME=xxx

for .env file
```.env

KEY_VAULT_NAME=xxx
WORKSPACE_NAME=xxx
RESOURCE_GROUP_NAME=xxx
SUBSCRIPTION_ID=xxx

```

## Prompt Flow Runtime

### Can I use serverless or automatic runtime?
yes, the default runtime is serverless. You don't have to do anything to use `serverless runtime`. The runtime is automatically selected based on the environment.

### Can I use dedicated runtime?
yes, the default runtime is serverless however you can use `dedicated runtime` by setting the `runtime` element in the experiment.yaml file. The dedicated runtime should be provisioned prior to using it. This template does not provision dedicated runtime.


## Python dependencies

### Where are python dependencies defined?
Python dependencies are defined in the requirements.txt file. This file contains all the python packages that are required to run the code.

There are 2 places where python dependencies are defined:
1. `execute_job_requirements.txt` file defined within Azure DevOp/Github/Jenkins folders. These are needed for setting up prompt flow environment and runtime.
2. `requirements.txt` file defined within each use case folder (within the flows directory). These are needed for setting up use case specific environment. Check web_classification_flows for an example.

while executing Github workflows/Azure DevOps pipeline/Jenkins pipeline, both execute_job_requirements.txt file and use case specific requirements.txt file is used to install python dependencies.

### How to install python dependencies locally?
To install python dependencies, run both the following command. The first command installs the dependencies needed for setting up prompt flow environment and runtime. The second command installs the dependencies needed for setting up use case specific environment. `Check web_classification_flows for an example`:

```bash
pip install -r ./.github/requirements/execute_job_requirements.txt

pip install -r ./web_classification/flows/experiment/requirements.txt
```

## Environmental Variables

### How to pass config values to Flows?
Each use case should define an env.yaml file within the environments directory. This file contains all secrets and config values that you want to pass to the flow. The values in this file are then passed to the flow as environmental variables. If the value is a plcaeholder for a secret, it should be defined as ${secret_name} in the env.yaml file. The actual value for the secret should be stored in the ENV_VARS secret in github, library variable in Azure DevOps and within .env file for local execution. 

If the value is a constant, it should be defined as a key-value pair in the env.yaml file. The value will be made available as TOKEN_LENGTH environment variable within the flow. For example:

```yaml
token_lengh: 3000
```

### What is an example of ENV_VARS value?

Note that all keys are in upper case and the values are the actual secrets. Stick to alphanumeric characters and underscores for keys. Newline characters within a value are not supported. There cannot be whitespaces around the equals sign. There should not be special characters like semicolon(;) or hashes(#). If values are in quotes they should not be mismatched. For example:

```.env
KEY_VAULT_NAME=xxx
WORKSPACE_NAME=xxx
RESOURCE_GROUP_NAME=xxx
SUBSCRIPTION_ID=xxx
AZURE_OPENAI_API_KEY=xxxx
AZURE_OPENAI_ENDPOINT=xxxx
MODEL_CONFIG_AZURE_ENDPOINT=xxxx
MODEL_CONFIG_API_KEY=xxxx
MAX_TOTAL_TOKEN=xxxx
AOAI_API_KEY=xxxx
AOAI_API_BASE=xxxx
APPLICATIONINSIGHTS_CONNECTION_STRING=xxxx
```

### What is an example of .env file?

Note that all keys are in upper case and the values are the actual secrets. Stick to alphanumeric characters and underscores for keys. Newline characters within a value are not supported. There cannot be whitespaces around the equals sign. There should not be special characters like semicolon(;) or hashes(#). If values are in quotes they should not be mismatched. For example:

```.env
KEY_VAULT_NAME=xxx
WORKSPACE_NAME=xxx
RESOURCE_GROUP_NAME=xxx
SUBSCRIPTION_ID=xxx
AZURE_OPENAI_API_KEY=xxxx
AZURE_OPENAI_ENDPOINT=xxxx
MODEL_CONFIG_AZURE_ENDPOINT=xxxx
MODEL_CONFIG_API_KEY=xxxx
MAX_TOTAL_TOKEN=xxxx
AOAI_API_KEY=xxxx
AOAI_API_BASE=xxxx
APPLICATIONINSIGHTS_CONNECTION_STRING=xxxx
```

### What values should go into .env file and ENV_VARS ?

If you have configurations in flows (init.json, flow.flex.yaml), experiment.yaml and env.yaml files that uses ${secret_name} style placeholders, then the actual value for secret_name should be stored in ENV_VARS secret in github, library variable in Azure DevOps and within .env file for local execution. These placeholders will be replaced by the actual values during execution either from ENV_VARS secret in github, library variable in Azure DevOps or from .env file for local execution.

- `experiment.yaml` file should contain placeholders for api_key within connections element.
- `env.yaml` file should contain placeholders for all other configurations. Check use case `function_flows` for an example. It has multiple ${} placeholder within env.yaml.
- `init.yaml` file can contain placeholders for all configurations.
- `flex.flow.yaml` file can contain placeholders for elements within Model_config element. Check use case `class_flows` for an example. It has ${api_key} placeholder within Model_config element.


## Experiments

### How are experiments defined?
Experiments are defined using experiments.yaml file. Refer to documentation related to experiments [here](./the_experiment_file.md).


### How to run an experiment?
Experiments are executed with help of prompt_pipeline.py python script

### How to define different experiments for different environments?
The template used the concepts of overlays. The base experiment is defined in experiment.yaml. `You can define one experiment.yaml per environment`. e.g environment.pr.yaml, environment.dev.yaml, environment.prod.yaml. `The base experiment.yaml file should contain all the common configurations`. The environment specific experiment.yaml file should contain only the configurations that are specific to that environment. Rest of the configurations will be picked up from the base experiment.yaml file.

The environment name used for naming of experiment.yaml file should be the same as the one used for `env_name' parameter used in python scripts and github workflows or `exec_environment` for Azure devops pipelines.

provide different specific configurations in the environment specific experiment.yaml file. The rest of the configurations will be picked up from the base experiment.yaml file. `Check math_coding for an example`. It uses different dataset for PR environment and different connection for dev environment.


### What types of standard flows are supported?
The template supports the following standard flows:
- `Function Flows` - The standard flow is defined as python function along with flow.flex.yaml file.
- `Class Flows` - The standard flow is defined as python class along with flow.flex.yaml file.
- `YAML based Flows` - The standard flow is defined as flow.dag.yaml file.

### How to run an experiments locally?

Experiments can be executed using the `prompt_pipeline.py` python script locally. The script takes the experiment.yaml file as input and runs the evaluations defined in the experiment.yaml file along with use case name and environment name. This generates RUN_ID.txt file containing the run id's which is later used for evaluation phase.

Change the value of `EXECUTION_TYPE` to `LOCAL` in `config.py` file located within `llmops/` directory.

```python
EXECUTION_TYPE = "AZURE"
```

```bash
python -m llmops.common.prompt_pipeline --subscription_id xxxx --base_path math_coding --env_name dev --output_file run_id.txt --build_id 100
```

### How to run an experiments on Azure from local machine?

Experiments can be executed using the `prompt_pipeline.py` python script locally. The script takes the experiment.yaml file as input and runs the evaluations defined in the experiment.yaml file along with use case name and environment name. This generates RUN_ID.txt file containing the run id's which is later used for evaluation phase.

NOTE: Azure Login using CLI should be done prior to running the experiment on Azure. This is needed to authenticate with Azure services.

Change the value of `EXECUTION_TYPE` to `AZURE` in `config.py` file located within `llmops/` directory.

```python
EXECUTION_TYPE = "AZURE"
```

```bash
python -m llmops.common.prompt_pipeline --subscription_id xxxx --base_path math_coding --env_name dev --output_file run_id.txt --build_id 100
```

## Evaluations

### How are evaluations defined?

Evaluations are defined using evaluators collection within the experiment.yaml file.

```yaml

evaluators:
- name: class_flows
  flow: flows/eval_checklist
  datasets:
  - name: class_flow_data_test
    reference: class_flow_data
    source: data/data_test.jsonl
    description: "This dataset is for evaluating flows."
    mappings:
      statements: "${data.statements}"
      answer: "${run.outputs.output}"

```

### How to run an evaluation locally?

Evaluations can be run using the `prompt_eval.py` python script locally. The script takes the experiment.yaml file as input and runs the evaluations defined in the experiment.yaml file along with use case name and environment name. For pure python script based evaluations, the python script is executed to run the evaluation. Check out `eval_nlp` evaluation as an example within `class_flows` use case. In this case, you do not need to execute bulk run experiments prior to evaluation. For rest of the evaluation types, you need to execute bulk run experiments prior to evaluation. This uses RUN_ID.txt file containing the run id's generated as part of experiment phase.

Change the value of `EXECUTION_TYPE` to `LOCAL` in `config.py` file located within `llmops/` directory.

```python
EXECUTION_TYPE = "LOCAL"

```bash
python -m llmops.common.prompt_eval --run_id run_id.txt --subscription_id xxxxx --base_path math_coding  --env_name dev  --build_id 100
```

### How to run an evaluation on Azure from local machine?

Evaluations can be run using the `prompt_eval.py` python script locally. The script takes the experiment.yaml file as input and runs the evaluations defined in the experiment.yaml file along with use case name and environment name. For pure python script based evaluations, the python script is executed to run the evaluation. Check out `eval_nlp` evaluation as an example within `class_flows` use case. In this case, you do not need to execute bulk run experiments prior to evaluation. For rest of the evaluation types, you need to execute bulk run experiments prior to evaluation. This uses RUN_ID.txt file containing the run id's generated as part of experiment phase.

NOTE: Azure Login using CLI should be done prior to running the experiment on Azure. This is needed to authenticate with Azure services.

Change the value of `EXECUTION_TYPE` to `LOCAL` in `config.py` file located within `llmops/` directory.

```python
EXECUTION_TYPE = "AZURE"

```bash
python -m llmops.common.prompt_eval --run_id run_id.txt --subscription_id xxxxx --base_path math_coding  --env_name dev  --build_id 100
```

### What types of evaluation flows are supported?
The template supports the following standard flows:
- `Function Flows` - The evaluation flow is defined as python function along with flow.flex.yaml file.
- `Class Flows` - The evaluation flow is defined as python class along with flow.flex.yaml file.
- `YAML based flows` - The evaluation flow is defined as flow.dag.yaml file.
- `Pure python script based evaluations` - In this case, the evaluation is defined in a python script. The python evaluation script is executed to run the prompt_eval.py file. Check out `eval_nlp` evalaution for an example within `class_flows` use case.

### How are evaluations defined?
Experiments are defined using experiments.yaml file. Refer to documentation related to experiments [here](docs/experiment.yaml).


### How many evaluators can be defined for an experiment?
You can define as many evaluators as you need in the experiment.yaml file. Each evaluator should have a unique name. The evaluator `name` is used to refer to the evaluator in the experiment.yaml file. The `flow` is also used to refer to the evaluation flow.

### How to define different evaluators for different environments?
The template used the concepts of overlays. The base experiment is defined in experiment.yaml. You can define one experiment.yaml per environment. e.g environment.pr.yaml, environment.dev.yaml, environment.prod.yaml. The base experiment.yaml file should contain all the common configurations. The environment specific experiment.yaml file should contain only the configurations that are specific to that environment. Rest of the configurations will be picked up from the base experiment.yaml file.

The environment name used for naming of experiment.yaml file should be the same as the one used for env_name parameter used in python scripts and github workflows/Azure devops/Jenkins pipelines.

provide just the evaluator specific configurations in the environment specific experiment.yaml file. The rest of the configurations will be picked up from the base experiment.yaml file. `Check math_coding for an example`. It uses different dataset for PR environment and different connection for dev environment.


## Connections

### What connections are supported?
This template supports all the major connections provided by the Prompt Flow service including: 
- AzureOpenAIConnection
- OpenAIConnection
- CognitiveSearchConnection
- CustomConnection
- FormRecognizerConnection
- SerpConnection
- AzureContentSafetyConnection

### How to configure connections?
To configure a connection, add the following yaml snippet to your experiment.yaml file:
```yaml
connections:
- name: aoai
  connection_type: AzureOpenAIConnection
  api_base: https://demoopenaiexamples.openai.azure.com/
  api_version: 2023-07-01-preview
  api_key: ${api_key}
  api_type: azure

:
```
You can add as many connections as you need to your experiment.yaml file.

### How do I provide value for ${api_key}?
To provide a value for ${api_key}, you can set it as an environment variable via .env file and also add to ENV_VARS secret in github, library variable in Azure DevOps. 
.env file will be used for local execution and ENV_VARS secret will be used for execution in the cloud.

It is mandatory to use environment variables for sensitive information especially API keys.

### How to use connections in the experiment?

To use a connection in the experiment, you can refer to the connection name in the experiment.yaml file. For example, to use the AzureOpenAIConnection in the experiment, you can refer to it as `aoai` in the experiment.yaml file. The same connection name should be available in Azure Prompt Flow connections. This connection name can then be used within init.json (as part of Model_config), flow.flex.yaml (as part of Model_config), flow.dag.yaml, and other files in the experiment.

### How to add new connection types?

Connections are created both locally as well as on Azure by ./llmops/common/create_connections.py file. Check out the schema for the new connection type. If it supports name-value pairs then just by adding an additional entry to CONNECTION_CLASSES will allow using the connection in the experiment. Notice that the connection type should be the same as the one defined by Prompt Flow. the key in this dictionary is all in lower case.

### What is the schema for the connections?
The schema for the connections is as follows:
```yaml

Azure OpenAI Connection:
    name: fields.Str()
    type: AzureOpenAIConnection
    api_key: fields.Str()
    api_base: fields.Str()
    api_type: fields.Str(default="azure")
    api_version: fields.Str()

OpenAI Connection:
    name: fields.Str()
    type: OpenAIConnection
    api_key: fields.Str()
    organization: fields.Str()
    base_url: fields.Str()


Azure Document Intelligence:
    name: fields.Str()
    type: FormRecognizerConnection
    api_key: fields.Str()
    endpoint: fields.Str()
    api_version: fields.Str()
    api_type: fields.Str(default="Form Recognizer")

Azure Search AI:
    name: fields.Str()
    type: CognitiveSearchConnection
    api_key: fields.Str()
    api_base: fields.Str()
    api_version: fields.Str()

Custom Connection:
    name: fields.Str()
    type: CustomConnection
    secrets:
      api_key: fields.Str()
    configs:
      api_base: fields.Str()
      api_version: fields.Str()

Azure Content Safety Connection:
    name: fields.Str()
    type: CustomConnection
    api_key: fields.Str()
    api_type: fields.Str()
    endpoint: fields.Str()
    api_version: fields.Str()

```

## Configurations

### What configurations are needed for running the flow on Azure?
This template requires the following configurations:

1. `Experiment configurations` - These are defined in the experiment.yaml file. The experiment.yaml file contains all the configurations needed to run the experiment. This includes the use case name, environment name, connections, evaluators, runtime and datasets.

2. `Environment configurations` - These are defined in the env.yaml file. The env.yaml file contains all the secrets and config values that you want to pass to the flow. The values in this file are then passed to the flow as environmental variables. If the value is a plcaeholder for a secret, it should be defined as ${secret_name} in the env.yaml file. The actual value for the secret should be stored in the ENV_VARS secret in github, library variable in Azure DevOps and within .env file for local execution. If the value is a constant, it should be defined as a key-value pair in the env.yaml file. The value will be made available as TOKEN_LENGTH environment variable within the flow.

3. `Deployment configurations` - These are defined in the deployment.yaml file. The deployment.yaml file contains all the configurations needed to deploy the flows. This includes deployment to Webapps, Managed endpoints on AI Studio or AML compute, Attached AKS nodes.

4. For `github repo`, the following configurations are needed:
   - `Github secrets` - These are defined in the `ENV_VARS` secret in github. The ENV_VARS secret contains the copy of .env file needed to run the experiment. This includes the api keys, endpoints, and other sensitive information. The ENV_VARS secret is used to replace the placeholders in prior mentioned configuration files with the actual values. `AZURE_CREDENTIALS` is a special secret that is used to authenticate with Azure. This secret is used to authenticate with Azure AI Studio, Azure Machine Learning, and other Azure services. This contains information about the service principal, tenant id, secret and subscription id. `DOCKER_IMAGE_REGISTRY` is a special secret that is used to authenticate with the docker registry. This secret is used to push the docker image to the docker registry. This contains information about the docker registry username and password.

   - `Github Environment variables` - These are defined in the github environment variables. The github environment variables are used to pass the environment specific values to the experiment. There same environment variables are used for all environments. For example, `WORKSPACE_NAME`, `RESOURCE_GROUP_NAME`, `KEY_VAULT_NAME` are environment variables that are used for all environments (pr, dev, prod). The values for each environment variable are environment specific. 

   - `Github PR workflows` - For each use case specific PR workflows are defined in the `.github/workflows` directory. The workflows are used to run the experiment on minimal dataset. The workflows are triggered based on the events defined in the workflow file. The workflows use the `ENV_VARS` and `AZURE_CREDENTIALS` secret and `env_name and use_case_base_path` are other parameters used in the workflow file. 
   `env_name` is the environment name used for naming of experiment.yaml file. `use_case_base_path` is the path to the use case folder. 

   - `Github CI workflows` - For each use case specific CI workflows are defined in the `.github/workflows` directory. The workflows are used to run the experiment, evaluation, and deployment. The workflows are triggered based on the events defined in the workflow file. The workflows use the `ENV_VARS, DOCKER_IMAGE_REGISTRY and AZURE_CREDENTIALS secret and env_name, use_case_base_path and deployment_type` are other parameters used in the workflow file. 
   `env_name` is the environment name used for naming of experiment.yaml file. `use_case_base_path` is the path to the use case folder. `deployment_type` is the type of deployment. Valid Deployment_types are `webapps, aml, and aks`. `aml` will deploy the flow to either Azure Machine Learning or AI Studio depending on other configurations. `webapps` will deploy the flow to Azure Webapps using a DOCKER IMAGE. `aks` will deploy the flow to AML attached Kubernetes compute. The deployment_type is used to determine appropriate configuration within deployment.yaml file to use for deployment. The deployment.yaml file contains all the configurations needed to deploy the flows. 

5. For `Azure DevOps repo`, the following configurations are needed:
   - `Azure DevOps Variables` - These are defined in the `ENV_VARS` variable in Azure DevOps. The `ENV_VARS` secret contains the copy of .env file needed to run the experiment. This includes the api keys, endpoints, and other sensitive information. The ENV_VARS secret is used to replace the placeholders in prior mentioned configuration files with the actual values. Azure Service connection name is a variable that is used to authenticate with Azure. This secret is used to authenticate with Azure AI Studio, Azure Machine Learning, and other Azure services. Azure Service connection contains information about the service principal, tenant id, secret and subscription id. `DOCKER_IMAGE_REGISTRY` is a special secret that is used to authenticate with the docker registry. This secret is used to push the docker image to the docker registry. This contains information about the docker registry username and password. `wk_name`, `rg_name`, `kv_name` are other variables that should be defined based on environment. 

   - `Azure DevOps PR workflows` - For each use case specific PR workflows are defined in the `.azure-pipelines/` directory. The pipeline are used to run the experiment on minimal dataset. The pipeline are triggered based on the events defined in the workflow file. The workflows use the `env_vars, exec_environment, use_case_base_path, wk_name and rg_name` are other parameters used in the workflow file. `exec_environment` is the environment name used for naming of experiment.yaml file. `use_case_base_path `is the path to the use case folder. 

   - `Azure DevOps CI workflows` - For each use case specific CI pipelines are defined in the use case specific `.azure-pipelines/` directory. The pipelines are used to run the experiment, evaluation, and deployment. The pipelines are triggered based on merging a PR to next environment defined in the pipeline file. The pipeline use the `ENV_VARS, DOCKER_IMAGE_REGISTRY and AZURE_CREDENTIALS secret and env_name, use_case_base_path and deployment_type` are other parameters used in the workflow file. 
   `env_name` is the environment name used for naming of experiment.yaml file. `use_case_base_path` is the path to the use case folder. `deployment_type` is the type of deployment. Valid Deployment_types are `webapps, aml, and aks`. `aml` will deploy the flow to either Azure Machine Learning or AI Studio depending on other configurations. `webapps` will deploy the flow to Azure Webapps using a DOCKER IMAGE. `aks` will deploy the flow to AML attached Kubernetes compute. The `deployment_typ`e is used to determine appropriate configuration within deployment.yaml file to use for deployment. The deployment.yaml file contains all the configurations needed to deploy the flows. wk_name, kv_name and rg_name are other parameters used in the workflow file.

### What configurations are needed for running the flow locally?
This template requires the following configurations for local execution:

1. Experiment configurations - These are defined in the experiment.yaml file. The experiment.yaml file contains all the configurations needed to run the experiment. This includes the use case name, environment name, connections, evaluators, runtime and datasets.

2. Environment configurations - These are defined in the env.yaml file. The env.yaml file contains all the secrets and config values that you want to pass to the flow. The values in this file are then passed to the flow as environmental variables. If the value is a plcaeholder for a secret, it should be defined as ${secret_name} in the env.yaml file. The actual value for the secret should be stored in the ENV_VARS secret in github, library variable in Azure DevOps and within .env file for local execution. If the value is a constant, it should be defined as a key-value pair in the env.yaml file. The value will be made available as TOKEN_LENGTH environment variable within the flow.

3. setup .env file - The .env file contains all the secrets and config values that you want to pass to the flow. The values in this file are then passed to the flow as environmental variables.

NOTE: Azure Login using CLI should be done prior to running the experiment on Azure. This is needed to authenticate with Azure services.


## Deployments

### What is the purpose of the deployment.json file?
The deployment.json file is used to define various deployment configurations for different environments and endpoints. It includes details about the deployment environment, endpoints, traffic allocation, and other settings.


### What are the different types of endpoints supported?

The deployment.json file supports three types of endpoints:

- Azure Managed Endpoint
- Attached Kubernetes Endpoint
- WebApp Endpoint

### How do I configure an Azure Managed Endpoint?

To configure an Azure Managed Endpoint, you need to specify details such as environment name, endpoint name, deployment name, VM size, instance count, and environment variables.

Example:
```json
{
    "azure_managed_endpoint":[
        {
            "ENV_NAME": "dev",
            "TEST_FILE_PATH": "sample-request.json",
            "ENDPOINT_NAME": "cf01eee",
            "ENDPOINT_DESC": "An online endpoint serving a flow for python class based flow",
            "DEPLOYMENT_DESC": "prompt flow deployment",
            "PRIOR_DEPLOYMENT_NAME": "",
            "PRIOR_DEPLOYMENT_TRAFFIC_ALLOCATION": "",
            "CURRENT_DEPLOYMENT_NAME": "cf01ddd",
            "CURRENT_DEPLOYMENT_TRAFFIC_ALLOCATION": "100",
            "DEPLOYMENT_VM_SIZE": "Standard_F4s_v2",
            "DEPLOYMENT_INSTANCE_COUNT": 1,
            "ENVIRONMENT_VARIABLES": {
                "example-name": "example-value"
            }
        }
    ]
}

```

### What is the significance of CURRENT_DEPLOYMENT_TRAFFIC_ALLOCATION?
The CURRENT_DEPLOYMENT_TRAFFIC_ALLOCATION field specifies the percentage of traffic that should be routed to the current deployment. This helps in gradually shifting traffic during updates or rollouts. This is used when having multiple deployment for an endpoint (A/B deployment).

### How do I allocate traffic during a deployment update?
Use the CURRENT_DEPLOYMENT_TRAFFIC_ALLOCATION and PRIOR_DEPLOYMENT_TRAFFIC_ALLOCATION fields to allocate traffic between the current and prior deployments. This allows for smooth traffic transition and rollback if necessary.

### How do I configure a Kubernetes Endpoint?
To configure a Kubernetes Endpoint, you need to provide details such as environment name, endpoint description, deployment description, VM size, instance count, CPU and memory allocation, and environment variables.

Example:

```yaml
{
    "kubernetes_endpoint":[
        {
            "ENV_NAME": "dev",
            "TEST_FILE_PATH": "sample-request.json",
            "ENDPOINT_NAME": "",
            "ENDPOINT_DESC": "A kubernetes endpoint serving a flow for named entity",
            "DEPLOYMENT_DESC": "prompt flow deployment",
            "PRIOR_DEPLOYMENT_NAME": "",
            "PRIOR_DEPLOYMENT_TRAFFIC_ALLOCATION": "",
            "CURRENT_DEPLOYMENT_NAME": "",
            "CURRENT_DEPLOYMENT_TRAFFIC_ALLOCATION": 100,
            "COMPUTE_NAME": "",
            "DEPLOYMENT_VM_SIZE": "",
            "DEPLOYMENT_INSTANCE_COUNT": 1,
            "CPU_ALLOCATION": "",
            "MEMORY_ALLOCATION": "",
            "ENVIRONMENT_VARIABLES": {
                "example-name": "example-value"
            }
        }
    ]
}
```

### How do I configure a WebApp Endpoint?
To configure a WebApp Endpoint, you need to specify details such as environment name, test file path, connection names, registry name, resource group name, app plan name, web app name, SKU, and user-managed ID.

Example:

```yaml
{
    "webapp_endpoint":[
        {
            "ENV_NAME": "dev",
            "TEST_FILE_PATH": "sample-request.json",
            "CONNECTION_NAMES": ["aoai"],
            "REGISTRY_NAME": "ACR_NAME",
            "REGISTRY_RG_NAME": "ACR_RESOURCE_RG",
            "APP_PLAN_NAME": "test_web_plan",
            "WEB_APP_NAME": "test_web_app",
            "WEB_APP_RG_NAME": "test_web_app_rg",
            "WEB_APP_SKU": "B3",
            "USER_MANAGED_ID": "web_app_managed_id"
        }
    ]
}

```
### What is the role of CONNECTION_NAMES in WebApp Endpoint configuration?
The CONNECTION_NAMES field lists the names of Prompt flow connections required for the execution of standard flow. 

### Can I define multiple endpoints in the same configuration file?
Yes, you can define multiple endpoints of different types by adding additional entries in their respective sections.

Example:

```yaml
{
    "azure_managed_endpoint":[
        {
            "ENV_NAME": "dev",
            "TEST_FILE_PATH": "sample-request.json",
            "ENDPOINT_NAME": "cf01eee",
            "ENDPOINT_DESC": "An online endpoint serving a flow for python class based flow",
            "DEPLOYMENT_DESC": "prompt flow deployment",
            "PRIOR_DEPLOYMENT_NAME": "",
            "PRIOR_DEPLOYMENT_TRAFFIC_ALLOCATION": "",
            "CURRENT_DEPLOYMENT_NAME": "cf01ddd",
            "CURRENT_DEPLOYMENT_TRAFFIC_ALLOCATION": "100",
            "DEPLOYMENT_VM_SIZE": "Standard_F4s_v2",
            "DEPLOYMENT_INSTANCE_COUNT": 1,
            "ENVIRONMENT_VARIABLES": {
                "example-name": "example-value"
            }
        }
    ],
    "kubernetes_endpoint":[
        {
            "ENV_NAME": "dev",
            "TEST_FILE_PATH": "sample-request.json",
            "ENDPOINT_NAME": "",
            "ENDPOINT_DESC": "A kubernetes endpoint serving a flow for named entity",
            "DEPLOYMENT_DESC": "prompt flow deployment",
            "PRIOR_DEPLOYMENT_NAME": "",
            "PRIOR_DEPLOYMENT_TRAFFIC_ALLOCATION": "",
            "CURRENT_DEPLOYMENT_NAME": "",
            "CURRENT_DEPLOYMENT_TRAFFIC_ALLOCATION": 100,
            "COMPUTE_NAME": "",
            "DEPLOYMENT_VM_SIZE": "",
            "DEPLOYMENT_INSTANCE_COUNT": 1,
            "CPU_ALLOCATION": "",
            "MEMORY_ALLOCATION": "",
            "ENVIRONMENT_VARIABLES": {
                "example-name": "example-value"
            }
        }
    ],
    "webapp_endpoint":[
        {
            "ENV_NAME": "dev",
            "TEST_FILE_PATH": "sample-request.json",
            "CONNECTION_NAMES": ["aoai"],
            "REGISTRY_NAME": "ACR_NAME",
            "REGISTRY_RG_NAME": "ACR_RESOURCE_RG",
            "APP_PLAN_NAME": "test_web_plan",
            "WEB_APP_NAME": "test_web_app",
            "WEB_APP_RG_NAME": "test_web_app_rg",
            "WEB_APP_SKU": "B3",
            "USER_MANAGED_ID": "web_app_managed_id"
        }
    ]
}

```

### Does Webapp and managed endpoints uses FASTApi?
By default both the docker images for webapp and managed endpoints uses FASTApi.

## Datasets

### What is the purpose of the datasets section in experiments.yaml?
The datasets section in experiments.yaml is used to define the datasets that will be utilized for experimentation and evaluation. It includes details such as the dataset's name, source, description, and mappings of data attributes.

### What is the difference between source and reference in the datasets configuration?
Source: Refers to the primary data used for experimentation or evaluation. It can be a file path or azure data asset.
Reference: Indicates that the evaluation flow uses a dataset related to, but distinct from, the primary dataset specified in the standard flow.

### How should I configure datasets when the evaluation flow uses a different but related dataset?
When the evaluation flow uses a different but related dataset, you should specify both source and reference fields in the evaluation dataset configuration. This clarifies that the datasets for the standard flow and evaluation flow are different.

Example:

```yaml
datasets:
- name: class_flow_data
  source: data/data.jsonl
  description: "This dataset is for prompt experiments."
  mappings:
    question: "${data.question}"
    chat_history: "${data.chat_history}"

evaluators:
- name: class_flows
  flow: flows/eval_checklist
  datasets:
  - name: class_flow_data_test
    reference: class_flow_data
    source: data/data_test.jsonl
    description: "This dataset is for evaluating flows."
    mappings:
      statements: "${data.statements}"
      answer: "${run.outputs.output}"


```

### How should I configure datasets when the evaluation flow uses the same dataset as the standard flow?
When the evaluation flow uses the same dataset as the standard flow, you do not need to specify the source and reference fields. Ensure that the dataset names in both the standard flow and evaluation flow are identical.

Example:

```yaml
datasets:
- name: class_flow_data
  source: data/data.jsonl
  description: "This dataset is for prompt experiments."
  mappings:
    question: "${data.question}"
    chat_history: "${data.chat_history}"

evaluators:
- name: class_flows_nlp
  flow: flows/eval_nlp
  datasets:
  - name: class_flow_data
    description: "This dataset is for evaluating nlp."
    mappings:
      context: "${data.context}"
      answer: "${target.output}"

```

### What should I do if my evaluation flow is not recognizing the dataset?
- Check Dataset Names: Ensure that the dataset names in the standard and evaluation flows match if they are supposed to use the same dataset.
- Check Dataset configuration: Ensure that the dataset reference element match the name to dataset related to standard flow and source element in evaluation flows match the right data source(if standard and evaluation flows are supposed to use different datasets).
- Verify Paths: Confirm that the paths specified in the source fields are correct and that the file or Azure Data asset exists.
- Consistent Mappings: Ensure that the data attribute mappings are consistent and correctly defined.

### How do I handle multiple datasets in the same configuration?
You can define multiple datasets by adding additional entries in the datasets section. Each dataset should have a unique name and corresponding attributes.

Example:

```yaml
datasets:
- name: class_flow_data
  source: data/data.jsonl
  description: "This dataset is for prompt experiments."
  mappings:
    question: "${data.question}"
    chat_history: "${data.chat_history}"
- name: another_dataset
  source: data/another_data.jsonl
  description: "This dataset is for another set of experiments."
  mappings:
    query: "${data.query}"
    response: "${data.response}"

```

### Can I use multiple evaluators with different datasets?
Yes, you can define multiple evaluators, each with its own dataset configurations. Make sure to specify unique names for each evaluator and their datasets.

Example:
```yaml
evaluators:
- name: class_flows
  flow: flows/eval_checklist
  datasets:
  - name: class_flow_data_test
    reference: class_flow_data
    source: data/data_test.jsonl
    description: "This dataset is for evaluating flows."
    mappings:
      statements: "${data.statements}"
      answer: "${run.outputs.output}"

- name: another_evaluator
  flow: flows/eval_another_checklist
  datasets:
  - name: another_dataset_test
    reference: another_dataset
    source: data/another_data_test.jsonl
    description: "This dataset is for evaluating another flow."
    mappings:
      queries: "${data.queries}"
      responses: "${run.outputs.responses}"

```

## Docker usage

### Why do I have a docker folder with dockerfile in each standard flow?
The docker folder contains the Dockerfile needed to build the docker image for the standard flow. The Dockerfile contains the instructions to build the docker image. The docker image is used to deploy the flow to Azure online endpoints.

The current dockerfile is a sample dockerfile. You can modify the dockerfile as needed to include additional dependencies or configurations.

```dockerfile
FROM mcr.microsoft.com/azureml/promptflow/promptflow-runtime:latest
COPY ./requirements.txt .
RUN pip install -r requirements.txt
```

### Why do I have a dockerfile within environment folder?
The docker folder contains the Dockerfile needed to build the docker image for the standard flow. The Dockerfile contains the instructions to build the docker image. The docker image is used to deploy the flow to Azure web apps. This dockerfile will be removed in future.

The current dockerfile is a sample dockerfile. You can modify the dockerfile as needed to include additional dependencies or configurations.

```bash
# syntax=docker/dockerfile:1
FROM docker.io/continuumio/miniconda3:latest

WORKDIR /

COPY ./flow/requirements.txt /flow/requirements.txt

# gcc is for build psutil in MacOS
RUN apt-get update && apt-get install -y runit gcc

# create conda environment
RUN conda create -n promptflow-serve python=3.9.16 pip=23.0.1 -q -y && \
    conda run -n promptflow-serve \
    pip install -r /flow/requirements.txt && \
    conda run -n promptflow-serve pip install keyrings.alt && \
    conda run -n promptflow-serve pip install gunicorn==20.1.0 && \
    conda run -n promptflow-serve pip cache purge && \
    conda clean -a -y

COPY ./flow /flow


EXPOSE 8080

COPY ./connections/* /connections/

# reset runsvdir
RUN rm -rf /var/runit
COPY ./runit /var/runit
# grant permission
RUN chmod -R +x /var/runit

COPY ./start.sh /
CMD ["bash", "./start.sh"]

```

### Can the docker image be deployed elsewhere?
The docker image can be pushed to any container registry. The docker image can be pushed to Azure Container Registry (out-of-box), Docker Hub (needs code changes), or any other container registry. The docker image can be pulled from the container registry and deployed to the desired platform and operating system. It can be Azure or Non-Azure environment as well. The only requirement is that it should be a containerized environment.


## Troubleshooting

### How do I troubleshoot a failed experiment?
To troubleshoot a failed experiment, you can check the logs generated during the experiment execution. The logs contain information about the execution steps, errors, and other details. You can also check the experiment.yaml file for any misconfigurations or missing values related to environment variables, connections, or datasets.

### How do I troubleshoot a failed evaluation?
To troubleshoot a failed evaluation, you can check the logs generated during the evaluation execution. The logs contain information about the evaluation steps, errors, and other details. You can also check the experiment.yaml file for any misconfigurations or missing values related to environment variables, connections, or datasets.

### How do I troubleshoot a failed deployment?
To troubleshoot a failed deployment, you can check the logs generated during the deployment execution. The logs contain information about the deployment steps, errors, and other details. You can also check the deployment.json file for any misconfigurations or missing values related to environment variables, connections, or endpoints.

For Azure deployments, you can check the Azure endpoint logs for deployment status, logs, and other details.

For Webapp deployment, you can check the Azure Webapp logs for deployment status, logs, and other details. Log Streamin is available in Azure portal which is one of the most effective way to check the logs.

### How do I troubleshoot a failed local connection?

You can list all local connections and related configuration using the following command:

```bash
pf connection list
```

