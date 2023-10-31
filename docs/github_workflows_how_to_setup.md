# How to setup the repo with Github Workflows

This template supports Azure ML as a platform for ML, and Github workflows as a platform for operationalization. Therefore, we assume that you already have an Azure ML Workspace as well as an Github repository in place, and all the code from this repository has been cloned into the repository.

In order to setup the repository, you need to complete few steps.

**Step 1.** Create a Github repository secret named 'AZURE_CREDENTIALS'. You can use [this document](https://learn.microsoft.com/en-us/azure/developer/github/connect-from-azure?tabs=azure-portal%2Clinux#use-the-azure-login-action-with-a-service-principal-secret) as a reference. 

**Step 2.** Create a *development* branch and make it as default one to make sure that all PRs should go towards to it. This template assumes that the team works at a *development* branch as a primary source for coding and improving the model quality. Later, you can implement Github workflows that mode code from the *development* branch into qa/main or execute a release process right away. Release management is not in scope of this template.

**Step 3.** Create two Github workflow for each use case (e.g. named_entity_recognition). Both Github workflow should be created based on existing YAML files. The first one is based on the [named_entity_recognition_pr_dev_workflow.yml](../.github/workflows/named_entity_recognition_pr_dev_workflow.yml), and it helps to maintain code quality for all PRs including integration tests for the Azure ML experiment. Usually, we recommend to have a toy dataset for the integration tests to make sure that the Prompt Flow job can be completed fast enough - there is not a goal to check prompt quality and we just need to make sure that our job can be executed. The second Github workflow is based on [named_entity_recognition_ci_dev_workflow.yml](../.github/workflows/named_entity_recognition_ci_dev_workflow.yml) that should be executed automatically once new PR has been merged into the *development* branch. The main idea of this pipeline is to execute bulk-run, evaluation on the full dataset to generate a prompt variant and flow that can be a candidate for production. This Github workflow should be extended based on the project's requirements. 

More details about how to create a basic Github workflows can be found [here](https://docs.github.com/en/actions/using-workflows).

**Step 3.** Modify the configuration values in config.json file available for each use-case.

- ENV_NAME:  This represents the environment name, referring to a development and other environments for the tests and deployment of the Prompt Flow flows.
- RUNTIME_NAME:  This is name of a Prompt Flow runtime environment, used for executing the prompt flows.
- KEYVAULT_NAME:  This points to the name of an Azure Key Vault, a service for securely storing and managing secrets, keys, and certificates.
- RESOURCE_GROUP_NAME:  This is the name of the Azure resource group where various Azure resources are organized.
- WORKSPACE_NAME:  This represent the name of a workspace, which is a container for machine learning assets and resources.
- CONNECTION_NAME:  This is name for a specific Prompt Flow connection, which is used to link different LLM's like Azure Open AI.
- DEPLOYMENT_NAME:  This is the name of a LLM deployment like GPT-3.5-Turbo model.
- STANDARD_FLOW_PATH:  This specify a standard flow path associated with an prompt experiment.
- EVALUATION_FLOW_PATH:  This is an string value referring to evaluation flow paths. e.g. "eval1,eval2"

**Step 4.** Modify the configuration values in mapping_config.json file based on the environment.  These are used in both experiment and evaluation flows.

- experiment: This section define an inputs for an experiment flow and its associated attributes. 
- evaluation: This section defines the related evaluation flows and corresponding inputs for the experiment's results. Evaluation involves comparing predictions made by a experiment flow or process with actual ground truth values to assess the flow's performance.

**Step 5.** Modify the configuration values in data_config.json file based on the environment. These are required in creating data assets in Azure ML and also consume them in pipelines.

- ENV_NAME: This indicates the environment name, referring to the "development" or "production" or any other environment where the prompt will be deployed and used in real-world scenarios.
- DATA_PURPOSE: This denotes the purpose of the data, indicating that it's intended for pull-request(pr_data), experimentation(training_data) or evaluation(test_data).
- DATA_PATH: This points to the file path e.g. "flows/web_classification/data/data.jsonl," suggesting the location of a dataset file.
- DATASET_NAME: This is the name assigned to the dataset created as Data Asset on Azure.
- RELATED_EXP_DATASET: This is an optional element and is needed only for datasets used for evaluation(test_data) only. It has the name of the dataset used for experimentation.
- DATASET_DESC": This provides a description of the dataset.


**Step 6.** Modify the configuration values in deployment_config.json file based on the environment.  These are required for deploying prompt flows in Azure ML.

- ENV_NAME: This indicates the environment name, referring to the "development" or "production" or any other environment where the prompt will be deployed and used in real-world scenarios.
- TEST_FILE_PATH: This parameter  represents the file path to a sample input request for testing the deployed model. 
- ENDPOINT_NAME: This parameter is the name or identifier of the deployed endpoint for the prompt flow.
- ENDPOINT_DESC: This parameter provides a description of the endpoint. It describes the purpose of the endpoint, which is to serve a prompt flow online.
- DEPLOYMENT_DESC: This parameter provides a description of the deployment itself.
- DEPLOYMENT_NAME: This parameter represents the name or identifier of the deployment. 
- DEPLOYMENT_TRAFFIC_ALLOCATION": This parameter represent the percentage allocation of traffic to this deployment. A value of 100 indicates that all traffic is directed to this deployment.
- DEPLOYMENT_VM_SIZE: This parameter specifies the size or configuration of the virtual machine instances used for the deployment.
- DEPLOYMENT_BASE_IMAGE_NAME": This parameter represent the name of the base image used for creating the Prompt Flow runtime.
- DEPLOYMENT_CONDA_PATH": This parameter specifies the path to a Conda environment configuration file (usually named conda.yml), which is used to set up the deployment environment.
- DEPLOYMENT_INSTANCE_COUNT":This parameter specifies the number of instances (virtual machines) that should be deployed for this particular configuration.
- ENVIRONMENT_VARIABLES": This parameter represents a set of environment variables that can be passed to the deployment.

**Step 7.** Add your data into data folder under use case folder. It supports, jsonl files. 

**Step 8.** Copy the standard and evaluation flow folders developed using Prompt Flow into the "flows" folder available for each use case.

Now, you can create a PR and test the flow.
