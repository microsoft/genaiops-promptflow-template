# How to Onboard new flow

Welcome to the process of onboarding a new Prompt flow `flow`! The content here will guide you through all the necessary steps and provide detailed instructions for adding a new flow to your factory's repository.

## Prerequisites

Before you begin the onboarding process, ensure you have the following prerequisites in place:

**Prompt flow Environment:** Azure DevOps project/Github repository along with Azure resources are provisioned before on-boarding new flows.

**New Flow:** You should already have the Prompt flow standard and evaluation flows. These are the custom flows that you've developed.

**Experience with Prompt flow and examples in this template:** New Flows should be on-boarded only after you get comfortable with the example flows in this repo and are able to execute them successfully either through Azure DevOps or Github workflows.

## Steps to Onboard new Flows

Follow these steps to onboard new Flows to your LLMOps template:

**Azure DevOps or Github Workflow or both:** Decide early on whether the LLMOps will use Azure DevOps or Github Workflows for Orchestration. Depending on this configuration either both or any one of these pipelines will be required.

**New Folder for new Flows** Similar to `named_entity_recognition` flow, a new folder should be created with the same sub-folder structure as `named_entity_recognition`.

**Flow Configuration:** The configuration of the use-case is managed by the `experiment.yaml` (sets the flow paths, datasets, and evaluations). Create your `experiment.yaml` file by referencing the [description](./the_experiment_file.md) of the file and the [YAML specification](./experiment.yaml) as well as checking the `experiment.yaml` of the existing use-cases.

You can start by copying an existing config file and modify it with relevant values. Provide valid values for all the configuration elements for your flow.

**Flows** Bring both the `standard and evaluation flows` within the `flows` sub-folder under a scenario folder. Files for both these type of flows should be under their own folder.

**Azure DevOps pipelines** The ``.azure-pipelines` folder should contains two yaml files - one for build validation during pull request and another for CI/CD. You can start by copying one of an existing folder under the new scenario folder and modify the files within this new folder. The modification in these files include - `Include
paths in `trigger and pr section` and the `default value` for `flow_to_execute` parameter in `parameters section`.

**Github Workflows** The `.github` folder should contains two yaml file- one for build validation during pull request and another for CI/CD for each use case along with platform related workflows and actions. You can start by copying existing scenario github workflows in this folder and modify the content to orchestrate the workflows for new flows and scenario.

**Configuration for deployment**  The configuration of the use-case deployment is managed by the `configs/deployment_config.json` file. Update the `deployment_config.json` for deployment related configuration. Modify the values in these configuration files to reflect your flow deployment.

**Bring Data**  The `data` folder contains data that would be uploaded to AzureML data assets and used for both bulk run and evaluation purpose. You can copy the data in this folder in `jsonl` format.

**Update Environment dependencies** The `environment` folder contains the `dockerfile` file needed during flow deployment to Azure web apps as Docker containers.

**Update local execution file**  You can start by copying one of the scripts in the `local_execution` folder and execute it after modifying variable values related to flow and data location.

**Write tests in tests folder:** The `tests` folder contains unit test implementation for the flows. These are python tests that will get executed as part of PR pipelines.

**Update sample-request.json:** Create a new file 'sample-request.json' containing data needed to test a Prompt flow endpoint after deployment from within the pipelines.
