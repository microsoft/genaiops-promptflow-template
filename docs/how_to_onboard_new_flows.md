# How to Onboard new flow 

Welcome to the process of onboarding a new Prompt Flow 'flow'! The content here will guide you through all the necessary steps and provide detailed instructions for adding a new flow to your factory's repository.

## Prerequisites

Before you begin the onboarding process, ensure you have the following prerequisites in place:

**Prompt Flow Environment:** Azure DevOps project/Github repository along with Azure resources are provisioned before on-boarding new flows. 

**New Flow:** You should have the Prompt Flow standard and evaluation flows you want to onboard. These are the custom flows that you've developed.

## Steps to Onboard new Flows

Follow these steps to onboard new Flows to your LLMOps template:

**Azure DevOps or Github Workflow or both:** Decide early on whether the LLMOps will use Azure DevOps or Github Workflows for LLMOps. Depending on this configuration for both or a single set of pipelines will be required.

**New Folder for new Flows** Similar to "named_entity_recognition" flow, a new folder should be created with the same sub-folder structure.

**Flow Configuration:** The config.json file in use-case folder contains a section for each environment (dev, test, production). The values for elements in this file should reflect the provisioned infrastructure and flows. 

You can start by copying an existing config file and modify it with relevant values. Provide valid values for all the configuration elements for your flow.

**Flows** Bring both the standard and evaluation flows within the 'flows' sub-folder in the use-case folder. Both these type of flows should be in their own folder. The config.json should be updated with the path of these flows.

**Azure DevOps pipelines** The .azure-pipelines folder should contains two yaml file- one for build validation during pull request and another for CI/CD. You can start by copying one of an existing folder in this folder and modify the files within the new folder. The modification in these files include: the include 
paths in trigger and pr section with values related to new flows and the default value for flow_to_execute parameter in parameters section.

**Github Workflows** The .github folder should contains two yaml file- one for build validation during pull request and another for CI/CD for each use case along with platform workflows and actions. You can start by copying existing use-case github workflows in this folder and modify the contentto reflect the new flows and use-case.

**Configuration for flows**  The configs folder contains the deployment and data configuration for the Model. The data_config.json file contains one element for each type of dataset required for an environment. For example, a flow needs 3 datasets - "pr_data", "training_data" and "test_data" represented by the "data_purpose" element. Update the deployment_config for deployment related configuration. Modify the values in these configuration files to reflect your flow deployment. Update the data_mapping for data mapping related configuration. Modify the values in these configuration files to reflect your flow execution.

**Bring Data**  The data folder contains data that would be uploaded to AzureML data assets. You can copy the data in this folder.

**Update Environment dependencies** The environment folder containsconda.yml file needed by the flow related to any python package dependencies as part of endpoint deployment.

**update local execution file**  You can start by copying one of an existing local_execution folder modify the python files to refer to new flows and related data.

**Write tests in tests folder:** The tests folder contains unit test implementation for the flows. These are python tests that will get executed as part of PR pipelines.

**Update sample-request.json:** Create a new file 'sample-request.json' containing data needed to test a Prompt Flow endpoint after deployment from pipeline.