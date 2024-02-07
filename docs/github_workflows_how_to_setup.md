# How to setup the repo with Github Workflows

This template supports Azure Machine Learning (ML) as a platform for LLMOps, and Github workflows as a platform for Flow operationalization. LLMOps with Prompt Flow provides automation of:

* Running Prompt flow after a Pull Request
* Running multiple Prompt flow evaluations to ensure results are high quality
* Registering of prompt flow models
* Deployment of prompt flow models
* Deployment to Kubernetes and/or Azure ML compute
* A/B deployments
* Role based access control (RBAC) permissions to deployment system managed id to key vault and Azure ML workspace
* Endpoint testing
* Report generation

It is recommended to understand how [Prompt flow works](https://learn.microsoft.com/en-us/azure/machine-learning/prompt-flow/get-started-prompt-flow?view=azureml-api-2) before using this template.

## Prerequisites

- An Azure subscription. If you don't have an Azure subscription, create a free account before you begin. Try the [free or paid version of Machine Learning](https://azure.microsoft.com/free/).
- An Azure Machine Learning workspace.
- Git running on your local machine.
- GitHub as the source control repository.
- Azure OpenAI with Model deployed with name `gpt-35-turbo`.
- In case of Kubernetes based deployment, Kubernetes resources and associating it with Azure Machine Learning workspace would be required. More details about using Kubernetes as compute in AzureML is available [here](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-attach-kubernetes-anywhere?view=azureml-api-2).

The template deploys real-time online endpoints for flows. These endpoints have Managed ID assigned to them and in many cases they need access to Azure Machine learning workspace and its associated key vault. The template by default provides access to both the key vault and Azure Machine Learning workspace based on this [document](https://learn.microsoft.com/en-ca/azure/machine-learning/prompt-flow/how-to-deploy-for-real-time-inference?view=azureml-api-2#grant-permissions-to-the-endpoint)

## Create Azure service principal

Create one Azure service principal for the purpose of understanding this repository. You can add more depending on how many environments, you want to work on (Dev or Prod or Both). Service principals can be created using cloud shell, bash, powershell or from Azure UI.  If your subscription is part of an organization with multiple tenants, ensure that the Service Principal has access across tenants.

1. Copy the following bash commands to your computer and update the **spname** and **subscriptionId** variables with the values for your project. This command will also grant the **owner** role to the service principal in the subscription provided. This is required for GitHub Actions to properly use resources in that subscription.

    ``` bash
    spname="<your sp name>"
    roleName="Owner"
    subscriptionId="<subscription Id>"
    servicePrincipalName="Azure-ARM-${spname}"

    # Verify the ID of the active subscription
    echo "Using subscription ID $subscriptionID"
    echo "Creating SP for RBAC with name $servicePrincipalName, with role $roleName and in scopes     /subscriptions/$subscriptionId"

    az ad sp create-for-rbac --name $servicePrincipalName --role $roleName --scopes /subscriptions/$subscriptionId --sdk-auth

    echo "Please ensure that the information created here is properly save for future use."

1. Copy your edited commands into the Azure Shell and run them (**Ctrl** + **Shift** + **v**). If executing the commands on local machine, ensure Azure CLI is installed and successfully able to access after executing `az login` command. Azure CLI can be installed using information available [here](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)

1. After running these commands, you'll be presented with information related to the service principal. Save this information to a safe location, you'll use it later in the demo to configure GitHub.

    ```json

      {
      "clientId": "<service principal client id>",
      "clientSecret": "<service principal client secret>",
      "subscriptionId": "<Azure subscription id>",
      "tenantId": "<Azure tenant id>",
      "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
      "resourceManagerEndpointUrl": "https://management.azure.com/",
      "activeDirectoryGraphResourceId": "https://graph.windows.net/",
      "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
      "galleryEndpointUrl": "https://gallery.azure.com/",
      "managementEndpointUrl": "https://management.core.windows.net/"
      }
    ```

1. Copy the output, braces included. Save this information to a safe location, it will be use later in the demo to configure GitHub Repo.

1. Close the Cloud Shell once the service principals are created.


## Setup runtime for Prompt flow

Prompt Flow 'flows' require runtime associated with compute instance in Azure Machine Learning workspace. Both the compute instance and the associated runtime should be created prior to executing the flows. Both the Compute Instance and Prompt Flow runtime should be created using the Service Principal. This ensures that Service Principal is the owner of these resources and Flows can be executed on them from both Azure DevOps pipelines and Github workflows. This repo provides Azure CLI commands to create both the compute instance and the runtime using Service Principal.

Compute Instances and Prompt Flow runtimes can be created using cloud shell, local shells, or from Azure UI. If your subscription is a part of organization with multiple tenants, ensure that the Service Principal has access across tenants. The steps shown next can be executed from Cloud shell or any shell. The steps mentioned are using Cloud shell and they explicitly mentions any step that should not be executed in cloud shell.

### Steps:

1. Assign values to variables. Copy the following bash commands to your computer and update the variables with the values for your project.

```bash
subscriptionId=<your azure subscription id>
rgname=<your resource group name>
workspace_name=<your Azure machine learning workspace name>
userAssignedId=<enter user assigned managed identifier name>
keyvault=<your Azure machine learning workspace associate key vault name>
compute_name=<enter compute name>
location=<your Azure machine learning workspace region>
runtimeName=<enter runtime name>
sp_id=<your azure service principal or client id>
sp_password=<your service principal password>
tenant_id=<your azure tenant id>
```

2. This next 2 commands should not be performed from Cloud shell. It should be performed from local shells. It helps with interactive azure login and selects a subscription.

```bash
az login
az account set -s $subscriptionId
```

3. Create a user-assigned managed identity

```bash
az identity create -g $rgname -n $userAssignedId --query "id"
```

4. Get id, principalId of user-assigned managed identity

```bash
um_details=$(az identity show -g $rgname -n $userAssignedId --query "[id, clientId, principalId]")
```

5. Get id of user-assigned managed identity

```bash
user_managed_id="$(echo $um_details | jq -r '.[0]')"
```

6. Get principal Id of user-assigned managed identity

```bash
principalId="$(echo $um_details | jq -r '.[2]')"
```

7. Grant the user managed identity permission to access the workspace (AzureML Data Scientist)

```bash
az role assignment create --assignee $principalId --role "AzureML Data Scientist" --scope "/subscriptions/$subscriptionId/resourcegroups/$rgname/providers/Microsoft.MachineLearningServices/workspaces/$workspace_name"
```

8. Grant the user managed identity permission to access the workspace keyvault (get and list)

```bash
az keyvault set-policy --name $keyvault --resource-group $rgname --object-id $principalId --secret-permissions get list
```

9. login with Service Principal

```bash
az login --service-principal -u $sp_id -p $sp_password --tenant $tenant_id
az account set -s $subscriptionId
```

10. Create compute instance and assign user managed identity to it

```bash
az ml compute create --name $compute_name --size Standard_E4s_v3 --identity-type UserAssigned --type ComputeInstance --resource-group $rgname --workspace-name $workspace_name --user-assigned-identities $user_managed_id
```

11. Get Service Principal Azure Entra token for REST API

```bash
access_token=$(az account get-access-token | jq -r ".accessToken")
```

12. Construct POST url for runtime

```bash
runtime_url_post=$(echo "https://ml.azure.com/api/$location/flow/api/subscriptions/$subscriptionId/resourceGroups/$rgname/providers/Microsoft.MachineLearningServices/workspaces/$workspace_name/FlowRuntimes/$runtimeName?asyncCall=true")
```

13. Construct GET url for runtime

```bash
runtime_url_get=$(echo "https://ml.azure.com/api/$location/flow/api/subscriptions/$subscriptionId/resourceGroups/$rgname/providers/Microsoft.MachineLearningServices/workspaces/$workspace_name/FlowRuntimes/$runtimeName")
```

14. Create runtime using REST API

```bash
curl --request POST \
  --url "$runtime_url_post" \
  --header "Authorization: Bearer $access_token" \
  --header 'Content-Type: application/json' \
  --data "{
    \"runtimeType\": \"ComputeInstance\",
    \"computeInstanceName\": \"$compute_name\",
}"
```

**Note:** If you have provisioned a managed VNET for your Azure ML workspace, this operation will not work for now. You need to use a serverless runtime for now.

15. Get runtime creation status using REST API. Execute this step multiple times unless either you get output that shows createdOn with a valid date and time value or failure. In case of failure, troubleshoot the issue before moving forward.

```bash
curl --request GET \
  --url "$runtime_url_get" \
  --header "Authorization: Bearer $access_token"
```

The template also provides support for 'automatic runtime' where flows are executed within a runtime provisioned automatically during execution. This feature is in preview. The first execution might need additional time for provisioning of the runtime.

The template supports using dedicated compute instances and runtimes by default and 'automatic runtime' can be enabled easily with minimal change in code. (search for COMPUTE_RUNTIME in code for such changes) and also remove any value in `llmops_config.json` for each use-case example for `RUNTIME_NAME`.

## Set up Github Repo

Fork this repository [LLMOps Prompt Flow Template Repo](https://github.com/microsoft/llmops-promptflow-template) in your GitHub organization. This repo has reusable LLMOps code that can be used across multiple projects.

![fork the repository](images/fork.png)

Create a *development* branch from *main* branch and also make it as default one to make sure that all PRs should go towards it. This template assumes that the team works at a *development* branch as a primary source for coding and improving the prompt quality. Later, you can implement Github workflows that move code from the *development* branch into qa/main or execute a release process right away. Release management is not in part of this template.

![create a new development branch](images/new-branch.png)

At this time, `main` is the default branch.

![main as default branch](images/main-default.png)

From the settings page, switch the default branch from `main` to `development`

![change development as default branch](images/change-default-branch.png)

It might ask for confirmation.

![default branch confirmation](images/confirmation.png)

Eventually, the default branch in github repo should show `development` as the default branch.

![make development branch as default branch](images/default-branch.png)

The template comes with a few Github workflow related to Prompt Flow flows for providing a jumpstart (named_entity_recognition, web_classification and math_coding). Each scenario has 2 primary workflows and 1 optional workflow. The first one is executed during pull request(PR) e.g. [named_entity_recognition_pr_dev_workflow.yml](../.github/workflows/named_entity_recognition_pr_dev_workflow.yml), and it helps to maintain code quality for all PRs. Usually, this pipeline uses a smaller dataset to make sure that the Prompt Flow job can be completed fast enough.

The second Github workflow [named_entity_recognition_ci_dev_workflow.yml](../.github/workflows/named_entity_recognition_ci_dev_workflow.yml) is executed automatically before a PR is merged into the *development* or *main* branch. The main idea of this pipeline is to execute bulk run and evaluation on the full dataset for all prompt variants. The workflow can be modified and extended based on the project's requirements.

The optional third Github workflow [named_entity_recognition_post_prod_eval.yml](../.github/workflows/named_entity_recognition_post_prod_eval.yml) need to be executed manually after the deployment of the Prompt Flow flow to production and collecting production logs (example log file - [production_log.jsonl](../named_entity_recognition/data/production_log.jsonl)). This workflow is used to evaluate the Prompt Flow flow performance in production.

More details about how to create a basic Github workflows in general can be found [here](https://docs.github.com/en/actions/using-workflows).

- Another important step in this section is to enable workflows in the new repository just created after forking.

![enable githhub workflows](images/enable-workflows.png)

## Set up authentication with Azure and GitHub

From your GitHub project, select **Settings** -> **Secrets and  variables**,  **Actions** and **New repository secret**. Create a Github repository secret named 'AZURE_CREDENTIALS' with information related to Azure Service Principal. You can paste the service principal output as the content of the secret and use [this document](https://learn.microsoft.com/en-us/azure/developer/github/connect-from-azure?tabs=azure-portal%2Clinux#use-the-azure-login-action-with-a-service-principal-secret) as a reference.

![Screenshot of GitHub Secrets.](images/github-secrets.png)

## Setup connections for Prompt flow

Prompt Flow Connections helps securely store and manage secret keys or other sensitive credentials required for interacting with LLM and other external tools, for example Azure OpenAI.

This repository has 3 examples, and all the examples use a connection named `aoai` inside, we need to set up a connection with this name if we haven’t created it before.

This repository has all the examples use Azure OpenAI model `gpt-35-turbo` deployed with the same name `gpt-35-turbo`, we need to set up this deployment if we haven’t created it before.

Please go to Azure Machine Learning workspace portal, click `Prompt flow` -> `Connections` -> `Create` -> `Azure OpenAI`, then follow the instructions to create your own connections called `aoai`. Learn more on [connections](https://learn.microsoft.com/en-us/azure/machine-learning/prompt-flow/concept-connections?view=azureml-api-2). The samples use a connection named "aoai" connecting to a gpt-35-turbo model deployed with the same name in Azure OpenAI. This connection should be created before executing the out-of-box flows provided with the template.

![aoai connection in Prompt Flow](images/connection.png)

The configuration for connection used while authoring the repo:

![connection details](images/connection-details.png)

## Cloning the repo

 Now, we can clone the forked repo on your local machine using command shown here. Replace the repo url with your url.

``` bash
git clone https://github.com/ritesh-modi/llmops-promptflow-template.git

cd llmops-promptflow-template

git branch

```

Create a new feature branch using the command shown here. Replace the branch name with your preferred name.

``` bash

git checkout -b featurebranch

```

Update code so that we can create a pull request. Update the `llmops_config.json` file for any one of the examples (e.g. `named_entity_recognization`). Update configuration so that we can create a pull request for any one of the example scenarios (e.g. named_entity_recognition). Navigate to scenario folder and update the `llmops_config.json` file. Update the KEYVAULT_NAME, RESOURCE_GROUP_NAME, RUNTIME_NAME and WORKSPACE_NAME. Update the `ENDPOINT_NAME` and `CURRENT_DEPLOYMENT_NAME` in `configs/deployment_config.json` file. Update the `ENDPOINT_NAME` and `CURRENT_DEPLOYMENT_NAME` in `configs/deployment_config.json` file.

### Update llmops_config.json

**Note:** If you decide to use [the infrastructure deployed with the deployment script of this code base](../docs/tutorial/02-Infra%20deployment.md), this file is created and populated automatically.

Modify the configuration values in the `llmops_config.json` file available for each example based on description.

- `ENV_NAME`:  This represents the environment type. (The template supports *pr* and *dev* environments.)
- `RUNTIME_NAME`:  This is the name of a Prompt Flow runtime environment, used for executing the prompt flows. Add values to this field only when you are using dedicated runtime and compute. The template uses automatic runtime by default.
- `KEYVAULT_NAME`:  This points to an Azure Key Vault related to the Azure ML service, a service for securely storing and managing secrets, keys, and certificates.
- `RESOURCE_GROUP_NAME`:  Name of the Azure resource group related to Azure ML workspace.
- `WORKSPACE_NAME`:  This is name of Azure ML workspace.
- `STANDARD_FLOW_PATH`:  This is the relative folder path to files related to a standard flow. e.g.  e.g. "flows/standard_flow.yml"
- `EVALUATION_FLOW_PATH`:  This is a string value referring to relative evaluation flow paths. It can have multiple comma separated values- one for each evaluation flow. e.g. "flows/eval_flow_1.yml,flows/eval_flow_2.yml"

For the optional post production evaluation workflow, the above configuration will be same only `ENV_NAME` will be *postprodeval* and the respective flow path need to be mentioned in `STANDARD_FLOW_PATH` configuration.

### Update deployment_config.json in config folder

**Note:** If you decide to use [the infrastructure deployed with the deployment script of this code base](../docs/tutorial/02-Infra%20deployment.md), this file is created and populated automatically. You can modify some of the default values if required.

Modify the configuration values in the `deployment_config.json` file for each environment. These are required for deploying Prompt flows in Azure ML. Ensure the values for `ENDPOINT_NAME` and `CURRENT_DEPLOYMENT_NAME` are changed before pushing the changes to remote repository.

- `ENV_NAME`: This indicates the environment name, referring to the "development" or "production" or any other environment where the prompt will be deployed and used in real-world scenarios.
- `TEST_FILE_PATH`: The value represents the file path containing sample input used for testing the deployed model.
- `ENDPOINT_NAME`: The value represents the name or identifier of the deployed endpoint for the prompt flow.
- `ENDPOINT_DESC`: It provides a description of the endpoint. It describes the purpose of the endpoint, which is to serve a prompt flow online.
- `DEPLOYMENT_DESC`: It provides a description of the deployment itself.
- `PRIOR_DEPLOYMENT_NAME`: The name of prior deployment. Used during A/B deployment. The value is "" if there is only a single deployment. Refer to CURRENT_DEPLOYMENT_NAME property for the first deployment.
- `PRIOR_DEPLOYMENT_TRAFFIC_ALLOCATION`:  The traffic allocation of prior deployment. Used during A/B deployment. The value is "" if there is only a single deployment. Refer to CURRENT_DEPLOYMENT_TRAFFIC_ALLOCATION property for the first deployment.
- `CURRENT_DEPLOYMENT_NAME`: The name of current deployment.
- `CURRENT_DEPLOYMENT_TRAFFIC_ALLOCATION`: The traffic allocation of current deployment. A value of 100 indicates that all traffic is directed to this deployment.
- `DEPLOYMENT_VM_SIZE`: This parameter specifies the size or configuration of the virtual machine instances used for the deployment.
- `DEPLOYMENT_BASE_IMAGE_NAME`: This parameter represents the name of the base image used for creating the Prompt Flow runtime.
-  `DEPLOYMENT_CONDA_PATH`: This parameter specifies the path to a Conda environment configuration file (usually named conda.yml), which is used to set up the deployment environment.
- `DEPLOYMENT_INSTANCE_COUNT`:This parameter specifies the number of instances (virtual machines) that should be deployed for this particular configuration.
- `ENVIRONMENT_VARIABLES`: This parameter represents a set of environment variables that can be passed to the deployment.

Kubernetes deployments have additional properties - `COMPUTE_NAME`, `DEPLOYMENT_VM_SIZE`, `CPU_ALLOCATION` and `MEMORY_ALLOCATION` related to infrastructure and resource requirements. These should also be updates with your values before executing Kubernetes based deployments.

Now, push the new feature branch to the newly forked repo.

``` bash

git add .
git commit -m "changed code"
git push -u origin featurebranch

```

Raise a new PR to merge code from `feature branch` to the `development` branch. Ensure that the PR from feature branch to development branch happens within your repository and organization.

![raise a new PR](images/pr.png)

This should start the process of executing the Math_coding PR pipeline.

![PR pipeline execution](images/pr-workflow-execution.png)

After the execution is complete, the code can be merged to the `development` branch.

Now a new PR can be opened from `development` branch to the `main` branch. This should execute both the PR as well as the CI pipeline.

## Update configurations for Prompt flow and GitHub Actions

There are multiple configuration files for enabling Prompt Flow run and evaluation in Azure ML and Github workflows

### Update mapping_config.json in config folder

Modify the configuration values in the `mapping_config.json` file based on both the standard and evaluation flows for an example. These are used in both experiment and evaluation flow execution.

- `experiment`: This section defines inputs for standard flow. The values comes from corresponding experiment dataset.
- `evaluation`: This section defines the inputs for the related evaluation flows. The values generally comes from two sources - dataset and output from bulk run. Evaluation involves comparing predictions made during bulk run execution of a standard flow with corresponding expected ground truth values and eventually used to assess the performance of prompt variants.

### Update data_config.json in config folder

Modify the configuration values in the `data_config.json` file based on the environment. These are required in creating data assets in Azure ML and also consume them in pipelines.

- `ENV_NAME`: This indicates the environment name, referring to the "development" or "production" or any other environment where the prompt will be deployed and used in real-world scenarios.
- `DATA_PURPOSE`: This denotes the purpose of the data usage. This includes data for pull-request(pr_data), experimentation(training_data) or evaluation(test_data). These 3 types are supported by the template.
- `DATA_PATH`: This points to the file path e.g. "flows/web_classification/data/data.jsonl".
- `DATASET_NAME`: This is the name used for the created Data Asset on Azure ML. Special characters are not allowed for naming the dataset.
- `RELATED_EXP_DATASET`: This element is used to relate data used for bulk run with the data used for evaluation. The value is the name of the dataset used for standard flow.
- `DATASET_DESC`: This provides a description for the dataset.

### Update data folder with data files

Add your data into the `data` folder under the use case folder. It supports `jsonl` files and the examples already contains data files for both running and evaluating Prompt Flows.

### Update Standard and evaluation flows

The `flows` folder contains one folder for each standard and evaluation flow. Each example in the repository already has these flows.

### Update Environment related dependencies

The `environment` folder contains a `conda.yml` file and any additional dependencies needed by the flow should be added to it. This file is used during deployment process.

### Update test data

The `sample-request.json` file contains a single test data used for testing the online endpoint after deployment in the pipeline. Each example has its own `sample-request.json` file and for custom flows, it should be updated to reflect test data needed for testing.

## Example Prompt Run, Evaluation and Deployment Scenario

There are three examples in this template. While `named_entity_recognition` and `math_coding` have the same functionality, `web_classification` has multiple evaluation flows and datasets for the dev environment. This is a flow in general across all examples.

![Githib workflow execution](./images/github-execution.png)

This Github CI workflow contains the following steps:

**Run Prompts in Flow**
- Upload bulk run dataset
- Bulk run prompt flow based on dataset
- Bulk run each prompt variant

**Evaluate Results**
- Upload ground test dataset
- Execution of multiple evaluation flows for a single bulk run (only for web_classification)
- Evaluation of the bulk run result using single evaluation flow (for others)

**Register Prompt Flow LLM App**
- Register Prompt Flow as a Model in Azure Machine Learning Model Registry

**Deploy and Test LLM App**
- Deploy the Flow as a model to the development environment either as Kubernetes or Azure ML Compute endpoint
- Assign RBAC permissions to the newly deployed endpoint to Key Vault and Azure ML workspace
- Test the model/promptflow realtime endpoint.

**Run post production deployment evaluation**
- Upload the sampled production log dataset
- Execute the evaluation flow on the production log dataset
- Generate the evaluation report

### Online Endpoint

1. After the CI pipeline for an example scenario has run successfully, depending on the configuration it will either deploy to

     ![Managed online endpoint](./images/online-endpoint.png) or to a Kubernetes compute type

     ![Managed online endpoint](./images/kubernetes.png)

2. Once pipeline execution completes, it would have successfully completed the test using data from `sample-request.json` file as well.

     ![online endpoint test in pipeline](./images/pipeline-test.png)

## Moving to production

The example scenario can be run and deployed both for Dev environments. When you are satisfied with the performance of the prompt evaluation pipeline, Prompt Flow model, and deployment in development, additional pipelines similar to `dev` pipelines can be replicated and deployed in the Production environment.

The sample Prompt flow run & evaluation and GitHub workflows can be used as a starting point to adapt your own prompt engineering code and data.
