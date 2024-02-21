# Tutorial 02: Development of flows
This tutorial will show you how to developing, testing and deploy promptflow using Azure AI studio UI, VS code extension and CLI/SDK.

## Setup environment
To try prompt flow, we would recommend you to use Azure AI studio, you can follow the steps below to create a new project and develop your own prompt flow.:
- [What is Azure AI Studio?](https://learn.microsoft.com/en-gb/azure/ai-studio/what-is-ai-studio?tabs=home)
- [How to create and manage an Azure AI resource](https://learn.microsoft.com/en-gb/azure/ai-studio/how-to/create-azure-ai-resource)
- [Create an Azure AI project in Azure AI Studio](https://learn.microsoft.com/en-gb/azure/ai-studio/how-to/create-projects)

You need create compute instance and runtime to submit prompt flow run:
- [How to create and manage compute instances in Azure AI Studio](https://learn.microsoft.com/en-gb/azure/ai-studio/how-to/create-manage-compute)
- [How to create and manage prompt flow runtimes in Azure AI Studio](https://learn.microsoft.com/en-gb/azure/ai-studio/how-to/create-manage-runtime)

You can use compute instance as your dev box, learn more here: [Get started with Azure AI projects in VS Code (Web)](https://learn.microsoft.com/en-gb/azure/ai-studio/how-to/vscode-web)

We also provide VS code extension to help you develop prompt flow, learn more here: [Prompt flow for VS Code](https://marketplace.visualstudio.com/items?itemName=prompt-flow.prompt-flow)

## Prompt flow authoring

Learn how to using prompt flow to develop your own flow: [Prompt flow authoring](https://learn.microsoft.com/en-gb/azure/ai-studio/how-to/flow-develop)

Meanwhile, Crafting a good prompt is a challenging task, in prompt flow we introduce variants to help you easily tune different prompt. You can try different prompt content via variant even set different parameter to LLM models. learn more here: [Tune prompts using variants in Azure AI Studio](https://learn.microsoft.com/en-gb/azure/ai-studio/how-to/flow-tune-prompts-using-variants)

To evaluation for the performance of your prompt flow, you can use the evaluation feature in prompt flow. learn more here: [Develop an evaluation flow in Azure AI Studio](https://learn.microsoft.com/en-gb/azure/ai-studio/how-to/flow-develop-evaluation)


## Deploy prompt flow as online endpoint

You can deploy prompt flow as online endpoint, learn more here: [Deploy a flow for real-time inference](https://learn.microsoft.com/en-gb/azure/ai-studio/how-to/flow-deploy?tabs=azure-studio)

## Code first experience for prompt flow

Prompt flow also provide CLI/SDK support e2e experience from authoring, testing, evaluation and deployment. learn more here: [Integrate prompt flow with LLM-based application DevOps](https://learn.microsoft.com/en-us/azure/machine-learning/prompt-flow/how-to-integrate-with-llm-app-devops?view=azureml-api-2&tabs=cli)
