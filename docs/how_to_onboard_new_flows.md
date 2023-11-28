# How to Onboard new flow

Welcome to the process of onboarding a new Prompt Flow `flow`! The content here will guide you through all the necessary steps and provide detailed instructions for adding a new flow to your factory's repository.

## Prerequisites

Before you begin the onboarding process, ensure you have the following prerequisites in place:

**Prompt Flow Environment:** Azure DevOps project/Github repository along with Azure resources are provisioned before on-boarding new flows.

**New Flow:** You should already have the Prompt Flow standard and evaluation flows. These are the custom flows that you've developed.

**Experience with Prompt Flow and examples in this template:** New Flows should be on-boarded only after you get comfortable with the example flows in this repo and are able to execute them successfully either through Azure DevOps or Github workflows.

## Steps to Onboard new Flows

Follow these steps to onboard new Flows to your LLMOps template:

**Azure DevOps or Github Workflow or both:** Decide early on whether the LLMOps will use Azure DevOps or Github Workflows for Orchestration. Depending on this configuration either both or any one of these pipelines will be required.

**New Folder for new Flows** Similar to `named_entity_recognition` flow, a new folder should be created with the same sub-folder structure as `named_entity_recognition`.

**Flow Configuration:** The `llmops_config.json` file in scenario folder contains a section for each environment (dev, test, production). The values for elements in this file should reflect the provisioned infrastructure and flows.

You can start by copying an existing config file and modify it with relevant values. Provide valid values for all the configuration elements for your flow.

**Flows** Bring both the `standard and evaluation flows` within the `flows` sub-folder under a scenario folder. Files for both these type of flows should be under their own folder. The `llmops_config.json` should be updated with the path of these flows. The name of these folders are very important and used within multiple other configuration files - these are used in `llmops_config.json` and `mapping_config.json` files.

**Azure DevOps pipelines** The ``.azure-pipelines` folder should contains two yaml files - one for build validation during pull request and another for CI/CD. You can start by copying one of an existing folder under the new scenario folder and modify the files within this new folder. The modification in these files include - `Include
paths in `trigger and pr section` and the `default value` for `flow_to_execute` parameter in `parameters section`.

**Github Workflows** The `.github` folder should contains two yaml file- one for build validation during pull request and another for CI/CD for each use case along with platform related workflows and actions. You can start by copying existing scenario github workflows in this folder and modify the content to orchestrate the workflows for new flows and scenario.

**Configuration for flows**  The `configs` folder contains the `deployment and data configuration` for the flows. The `data_config.json` file contains one element for each type of dataset required for an environment. For example, a flow needs 3 datasets - "pr_data", "training_data" and "test_data" represented by the "data_purpose" element. Update the `deployment_config.json` for deployment related configuration. Modify the values in these configuration files to reflect your flow deployment. Update the `mapping_config.json` for data mapping related configuration. Modify the values in these configuration files to reflect your flow execution.

**Bring Data**  The `data` folder contains data that would be uploaded to AzureML data assets and used for both bulk run and evaluation purpose. You can copy the data in this folder in `jsonl` format.

**Update Environment dependencies** The `environment` folder contains the `conda.yml` file needed during flow deployment for installing all python package dependencies.

**Update local execution file**  You can start by copying one of the scripts in the `local_execution` folder and execute it after modifying variable values related to flow and data location.

**Write tests in tests folder:** The `tests` folder contains unit test implementation for the flows. These are python tests that will get executed as part of PR pipelines.

**Update sample-request.json:** Create a new file 'sample-request.json' containing data needed to test a Prompt Flow endpoint after deployment from within the pipelines.
