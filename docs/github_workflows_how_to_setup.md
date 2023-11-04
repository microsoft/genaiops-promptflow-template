# How to setup the repo with Github Workflows

This template supports Azure ML as a platform for LLMOps, and Github workflows as a platform for Flow operationalization. Therefore, we assume that you already have an Azure ML Workspace as well as an Github repository created, and all the code from this repository has been cloned locally.

In order to setup your repository, you need to complete few steps.

**Step 1.** Create a Github repository secret named 'AZURE_CREDENTIALS' with information related to Azure Service Principal. You can use [this document](https://learn.microsoft.com/en-us/azure/developer/github/connect-from-azure?tabs=azure-portal%2Clinux#use-the-azure-login-action-with-a-service-principal-secret) as a reference. A Service Principal should pre-exist before executing this step. 

**Step 2.** Clone this repo and create a *development* branch and make it as default one to make sure that all PRs should go towards it. This template assumes that the team works at a *development* branch as a primary source for coding and improving the prompt quality. Later, you can implement Github workflows that move code from the *development* branch into qa/main or execute a release process right away. Release management is not in part of this template.

**Step 3.** The template comes with few Github workflow related to Prompt Flow flows for providing a jumpstart (named_entity_recognition, web_classification and math_coding). Each scenerio has 2 workflows. The first one is executed during pull request(PR) e.g. [named_entity_recognition_pr_dev_workflow.yml](../.github/workflows/named_entity_recognition_pr_dev_workflow.yml), and it helps to maintain code quality for all PRs. Usually, this pipeline uses a smaller dataset to make sure that the Prompt Flow job can be completed fast enough. The second Github workflow [named_entity_recognition_ci_dev_workflow.yml](../.github/workflows/named_entity_recognition_ci_dev_workflow.yml) is executed automatically once new PR has been merged into the *development* or *main* branch. The main idea of this pipeline is to execute bulk run, evaluation on the full dataset for all prompt variants. Both the workflow can and should be modified and extended based on the project's requirements. 

More details about how to create a basic Github workflows in general can be found [here](https://docs.github.com/en/actions/using-workflows).

**Step 4.** Provision Azure Resources needed to executing code in this repository. These are

- [Azure Machine Learning workspace]()
- [Azure OpenAI](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/create-resource?pivots=web-portal)
- [Azure OpenAI connections](https://learn.microsoft.com/en-us/azure/machine-learning/prompt-flow/how-to-create-manage-runtime?view=azureml-api-2)

Prompt Flow runtimes are optional by default. The template uses the concept of 'automatic runtime' where flows are executed within a runtime provisioned automatically during execution. The first execution might need additional time for provisioning of the runtime. The template supports using dedicated compute instances and runtimes and they can be enabled easily with minimal change in code. (search for COMPUTE_RUNTIME in code for such changes)

The samples uses a connection named "aoai" connecting to a gpt-35-turbo model deployed in Azure OpenAI. This connection should be created before executing the out-of-box flows provided with the template.

**Step 5.** Modify the configuration values in config.json file available for each use-case. Azure resources - Azure Machine Learning workspace, Azure OpenAI, Prompt Flow runtime and Azure OpenAI connections should already pre-exists before executing this step.

- ENV_NAME:  This represents the environment name, referring to a development and other environments for the tests and deployment of the Prompt Flow flows.
- RUNTIME_NAME:  This is name of a Prompt Flow runtime environment, used for executing the prompt flows. Use this only when using dedicated runtime and compute
- KEYVAULT_NAME:  This points to the name of an Azure Key Vault, a service for securely storing and managing secrets, keys, and certificates.
- RESOURCE_GROUP_NAME:  This is the name of the Azure resource group where various Azure resources are organized.
- WORKSPACE_NAME:  This represent the name of a workspace, which is a container for machine learning assets and resources.
- STANDARD_FLOW_PATH:  This specify a standard flow path associated with an prompt experiment. e.g.  e.g. "flows/standard_flow.yml"
- EVALUATION_FLOW_PATH:  This is an string value referring to evaluation flow paths. e.g. "flows/eval_flow_1.yml,flows/eval_flow_2.yml"

**Step 6.** Modify the configuration values in mapping_config.json file based on both the standard and evaluation flows. These are used in both experiment and evaluation flows.

- experiment: This section define inputs for standard flow. The values comes from a dataset.
- evaluation: This section defines the inputs for the related evaluation flows. The values generally comes from two sources - dataset and output from bulk run. Evaluation involves comparing predictions made during bulk run execution of a standard flow with corresponding expected ground truth values and eventually used to assess the performance of prompt variants.

**Step 7.** Modify the configuration values in data_config.json file based on the environment. These are required in creating data assets in Azure ML and also consume them in pipelines.

- ENV_NAME: This indicates the environment name, referring to the "development" or "production" or any other environment where the prompt will be deployed and used in real-world scenarios.
- DATA_PURPOSE: This denotes the purpose of the data usage. These includes data for pull-request(pr_data), experimentation(training_data) or evaluation(test_data). These 3 types are supported by the template.
- DATA_PATH: This points to the file path e.g. "flows/web_classification/data/data.jsonl".
- DATASET_NAME: This is the name used for created Data Asset on Azure ML.
- RELATED_EXP_DATASET: This element is used to relate data used for bulk run with the data used for evaluation. The value is the name of the dataset used for bulk run of standard flows.
- DATASET_DESC": This provides a description for the dataset.


**Step 8.** Modify the configuration values in deployment_config.json file based on the environment.  These are required for deploying prompt flows in Azure ML.

- ENV_NAME: This indicates the environment name, referring to the "development" or "production" or any other environment where the prompt will be deployed and used in real-world scenarios.
- TEST_FILE_PATH: The value represents the file path containing sample input used for testing the deployed model. 
- ENDPOINT_NAME: The value represents the name or identifier of the deployed endpoint for the prompt flow.
- ENDPOINT_DESC: It provides a description of the endpoint. It describes the purpose of the endpoint, which is to serve a prompt flow online.
- DEPLOYMENT_DESC: It provides a description of the deployment itself.
- DEPLOYMENT_NAME: The value represents the name or identifier of the deployment. 
- PRIOR_DEPLOYMENT_NAME: The name of prior deployment. Used during A/B deployment. The value is "" if there is only a single deployment. Refer to CURRENT_DEPLOYMENT_NAME property for the first deployment. 
- PRIOR_DEPLOYMENT_TRAFFIC_ALLOCATION:  The traffic allocation of prior deployment. Used during A/B deployment. The value is "" if there is only a single deployment. Refer to CURRENT_DEPLOYMENT_TRAFFIC_ALLOCATION property for the first deployment. 
- CURRENT_DEPLOYMENT_NAME: The name of current deployment.
- CURRENT_DEPLOYMENT_TRAFFIC_ALLOCATION: The traffic allocation of current deployment.
- DEPLOYMENT_TRAFFIC_ALLOCATION": This parameter represent the percentage allocation of traffic to this deployment. A value of 100 indicates that all traffic is directed to this deployment.
- DEPLOYMENT_VM_SIZE: This parameter specifies the size or configuration of the virtual machine instances used for the deployment.
- DEPLOYMENT_BASE_IMAGE_NAME": This parameter represent the name of the base image used for creating the Prompt Flow runtime.
- DEPLOYMENT_CONDA_PATH": This parameter specifies the path to a Conda environment configuration file (usually named conda.yml), which is used to set up the deployment environment.
- DEPLOYMENT_INSTANCE_COUNT":This parameter specifies the number of instances (virtual machines) that should be deployed for this particular configuration.
- ENVIRONMENT_VARIABLES": This parameter represents a set of environment variables that can be passed to the deployment.

Kubernetes deployments have addtional properties - COMPUTE_NAME, CPU_ALLOCATION and MEMORY_ALLOCATION related to infrastructure and resource requirements.

**Step 9.** Add your data into data folder under use case folder. It supports jsonl files. 

**Step 10.** Copy the standard and evaluation flow folders developed using Prompt Flow into the "flows" folder available for each use case.

Now, you can create a PR and test the flow.
