# Tutorial 03-Patterns of Prompt Flow

## Introduction

This tutorial will guide you through the concept and usage of advance patterns in Prompt Flow.

## Prerequisites

This tutorial assumes that you have completed the previous tutorials ([Tutorial 01](./01-Introduction.md), [Tutorial 02](./02-Development.md) and [Tutorial 02](./04-Patterns.md)) and have a working LLM flow with initial GitHub Actions.

## Exercises

### Create a flow with multiple variants

Each Flow has multiple nodes. Each node can have multiple variants. Think of variants as different versions of a recipe. You can tweak the recipe by changing ingredients or hyperparameters and see how it affects the outcome. Identifying and deploying the right variant based on its performance is critical.

In the basic flow add multiple variants by following the steps mentioned in this document: [Tune prompts using variants](https://learn.microsoft.com/en-us/azure/machine-learning/prompt-flow/how-to-tune-prompts-using-variants?view=azureml-api-2). Example for [web_classification](../../web_classification/) use case there are multiple variants defined in: [experiment](../../web_classification/flows/experiment/flow.dag.yaml).

### Create flows with Multiple Evaluation Flows and Metrics

Evaluation flows with different evaluation metrics and methods are important before deployments. e.g. calculating the relevancy and cosine similarity. You can think of multiple evaluation flows as different cooking recipe tester. Your recipe can be tested by multiple testers simultaneously.

Create more than one evaluation flows and add them to the template in `flows` directory for the specific use case folder. Example: for [web_classification](../../web_classification/) use case there are two evaluations flows: [evaluation](../../web_classification/flows/evaluation/) and [evaluation_avd](../../web_classification/flows/evaluation_adv/).

### Create flows with Multiple Datasets

A Flow can be evaluated using different datasets. E.g. a dataset with synthetic data viz-a-viz real data. Each dataset has a unique aspect. Think of data as a cooking ingredients. You can evaluate the recipe with different ingredients simultaneously.

Multiple data sets can be added by following the steps mentioned below:

- Add the data JSONL file to `data` directory for the specific use case folder. Example: for [web_classification](../../web_classification/) use case there are more than one data files: [data](../../web_classification/data/).
- Add a new dataset in the `datasets` block in the `experiment.yaml` file for the specific use case folder (see file [description](../the_experiment_file.md) and [specs](../experiment.yaml)). Example: for [web_classification](../../web_classification/) use case there are more than one datasets defined in: [experiment.yaml](../../web_classification/experiment.yaml).

### Execute flows with different runtimes

- Flow can be executed locally using the [VS Code extension](https://learn.microsoft.com/en-us/azure/machine-learning/prompt-flow/community-ecosystem?view=azureml-api-2#vs-code-extension) or [CLI](https://learn.microsoft.com/en-us/azure/machine-learning/prompt-flow/community-ecosystem?view=azureml-api-2#prompt-flow-sdkcli) or using [run_local.py](../../local_execution/prompt_experimentation/run_local.py) script. Example: for [web_classification](../../web_classification/) use case [web_classification_local_experiment.py](../../local_execution/web_classification_local_experiment.py) script is used to execute the flow locally.
- Flows can be executed in Azure ML using dedicated runtime and compute instance OR using automatic runtime and serverless compute. To use a dedicated runtime and compute instance, set the name of the runtime in the `experiment.yaml` file in the root of the specific use case folder. To use automatic runtime and serverless compute, do not set the runtime in the `experiment.yaml` file and the automatic runtime will be use by default.

### Deploy flows with different deployment targets

Flows can be deployed as an endpoint in the following deployment targets:

- Kubernetes deployment: Add the deployment target named `kubernetes_endpoint` in `/configs/deployment_config.json` file for the specific use case folder. Example: for [web_classification](../../web_classification/) use case there is a deployment target defined for Kubernetes in: [deployment_config.json](../../web_classification/configs/deployment_config.json).
- AML Managed instance: Add the deployment target named `azure_managed_endpoint` in `/configs/deployment_config.json` file for the specific use case folder. Example: for [web_classification](../../web_classification/) use case there is a deployment target defined for AML Managed instance in: [deployment_config.json](../../web_classification/configs/deployment_config.json).
- Flows can be also be exported as Docker images and can be deployed as running containers to any platform, OS and cloud. For more details refer documents in: [Prompt Flow GitHub](https://github.com/microsoft/promptflow/tree/main/docs/how-to-guides/deploy-a-flow).
