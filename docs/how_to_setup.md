# How to setup the repo with Azure DevOps

This template supports Azure ML as a platform for ML, and Azure DevOps as a platform for operationalization. Therefore, we assume that you already have an Azure ML Workspace as well as an Azure DevOps project in place, and all the code from the repository has been cloned into the DevOps project.

In order to setup the repository, you need to complete few steps.

**Step 1.** Create a service connection in Azure DevOps. You can use [this document](https://learn.microsoft.com/en-us/azure/devops/pipelines/library/service-endpoints?view=azure-devops&tabs=yaml) as a reference. Use Azure Resource Manager as a type of the service connection.

**Step 2.** Create a new variable group (mlops_platform_dev_vg) with the following variables:

- AZURE_RM_SVC_CONNECTION: the service connection name from the previous step.

Information about variable groups in Azure DevOps can be found in [this document](https://learn.microsoft.com/en-us/azure/devops/pipelines/library/variable-groups?view=azure-devops&tabs=classic).

**Step 3.** Create a *development* branch and make it as default one to make sure that all PRs should go towards to it. This template assumes that the team works at a *development* branch as a primary source for coding and improving the model quality. Later, you can implement Azure Pipeline that mode code from the *development* branch into qa/main or execute a release process right away. Release management is not in scope of this template.

**Step 4.** Create two Azure Pipelines. Both Azure Pipelines should be created based on existing YAML files. The first one is based on the [named_entity_recognition_pr_dev_pipeline.yml](../.azure-pipelines/named_entity_recognition_pr_dev_pipeline.yml), and it helps to maintain code quality for all PRs including integration tests for the Azure ML experiment. Usually, we recommend to have a toy dataset for the integration tests to make sure that the Prompt Flow job can be completed fast enough - there is not a goal to check prompt quality and we just need to make sure that our job can be executed. The second Azure Pipeline is based on [named_entity_recognition_pr_dev_pipeline_ci_dev_pipeline.yml](../.azure-pipelines/named_entity_recognition_pr_dev_pipeline_ci_dev_pipeline.yml) that should be executed automatically once new PR has been merged into the *development* branch. The main idea of this pipeline is to execute training on the full dataset to generate a prompt variant and flow that can be a candidate for production. This Azure Pipeline should be extended based on the project's requirements. 

More details about how to create a basic Azure Pipeline can be found [here](https://learn.microsoft.com/en-us/azure/devops/pipelines/create-first-pipeline?view=azure-devops&tabs).

**Step 5.** Setup a policy for the *development* branch. At this stage we have an Azure Pipeline that should be executed on every PR to the *development* branch. At the same time successful completion of the build is not a requirement. So, it's important to add our PR build as a policy. Pay special attention that named_entity_recognition_pr_dev_pipeline_pr_dev_pipeline.yml](../devops/pipeline/named_entity_recognition_pr_dev_pipeline_pr_dev_pipeline.yml) has various paths in place. We are using these paths to limit number of runs if the current PR doesn't affect ML component (for example, PR modifies a documentation file). Therefore, setting up the policy you need to make sure that you are using the same set of paths in the *Path filter* field.

More details about how to create a policy can be found [here](https://learn.microsoft.com/en-us/azure/devops/repos/git/branch-policies?view=azure-devops&tabs=browser).

**Step 6.** Modify the configuration values in model_config.json file based on the environment.

- ML_MODEL_CONFIG_NAME:  This is the name of the use-case and prompt configuration.
- ENV_NAME:  This represents the environment name, referring to a development and other environments for the deployment and testing of the prompt flows.
- AZURE_RM_SVC_CONNECTION:  This is connection name reference for Azure DevOps service connection for interacting with Azure services.
- RUNTIME_NAME:  This is name of a Prompt Flow runtime environment, used for executing the prompt flows.
- EXPERIMENT_BASE_NAME:  This refer to a base name for various experiments conducted with the prompts.
- KEYVAULT_NAME:  This points to the name of an Azure Key Vault, a service for securely storing and managing secrets, keys, and certificates.
- MODEL_BASE_NAME:  This is base name for different versions or variations of prompt flows.
- RESOURCE_GROUP_NAME:  This is the name of the Azure resource group where various Azure resources are organized.
- WORKSPACE_NAME:  This represent the name of a workspace, which is a container for machine learning assets and resources.
- CONNECTION_NAME:  This is name for a specific Prompt Flow connection, which is used to link different LLM's like Azure Open AI.
- DEPLOYMENT_NAME:  This is the name of a LLM deployment like GPT-3.5-Turbo model.
- STANDARD_FLOW_PATH:  This specify a standard flow path associated with an prompt experiment.
- DEPLOY_FLOW_PATH:  This points to a flow path related to the deployment process for prompt flow.
- DATA_MAPPING_CONFIG:  This  refers to the configuration file ("mapping_config.json") for mapping data to the prompt's input format.
- EVALUATION_FLOW_PATH:  This is an string value referring to flow paths for evaluation. e.g. "eval1,eval2"
- DATA_CONFIG_PATH:  This points to the path of a configuration file ("data_config.json") that  defines how input data is processed and used.
- REALTIME_DEPLOYMENT_CONFIG:  This indicates a configuration file ("deployment_config.json") for real-time deployment settings on Azure ML.


**Step 7.** Modify the configuration values in mapping_config.json file based on the environment.  These are used in both experiment and evaluation flows.

- experiment: This section define an inputs for an experiment flow and its associated attributes. 
- evaluation: This section defines the related evaluation flows and corresponding inputs for the experiment's results. Evaluation involves comparing predictions made by a experiment flow or process with actual ground truth values to assess the flow's performance.

**Step 8.** Modify the configuration values in data_config.json file based on the environment. These are required in creating data assets in Azure ML and also consume them in pipelines.

- ML_MODEL_CONFIG_NAME: This is the name of the use-case and prompt configuration. This value should be same as in model_config.json
- ENV_NAME: This indicates the environment name, referring to the "development" or "production" or any other environment where the prompt will be deployed and used in real-world scenarios.
- AZURE_RM_SVC_CONNECTION: This is connection name reference for Azure DevOps service connection for interacting with Azure services.
- DATA_PURPOSE: This denotes the purpose of the data, indicating that it's intended for pull-request(pr_data), experimentation(training_data) or evaluation(test_data).
- DATA_PATH: This points to the file path e.g. "flows/web_classification/data/data.jsonl," suggesting the location of a dataset file.
- DATASET_NAME: This is the name assigned to the dataset created as Data Asset on Azure.
- RELATED_EXP_DATASET: This is an optional element and is needed only for datasets used for evaluation(test_data) only. It has the name of the dataset used for experimentation.
- DATASET_DESC": This provides a description of the dataset.


**Step 9.** Modify the configuration values in deployment_config.json file based on the environment.  These are required for deploying prompt flows in Azure ML.

- ML_MODEL_CONFIG_NAME: This is the name of the use-case and prompt configuration. This value should be same as in model_config.json
- ENV_NAME: This indicates the environment name, referring to the "development" or "production" or any other environment where the prompt will be deployed and used in real-world scenarios.
- AZURE_RM_SVC_CONNECTION: This is connection name reference for Azure DevOps service connection for interacting with Azure services.
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

Now, you can create a PR and test the flow.
