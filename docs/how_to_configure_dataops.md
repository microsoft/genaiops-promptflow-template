# How to Configure DataOps

Implementing the DataOps pattern will help manage and scale the data pipelines. The following sections will explain the necessary steps to integrate DataOps into the LLMOps pattern.

## Prerequisites

This document assumes that you have already gone through [How to Onboard new flow](./how_to_onboard_new_flows.md) and implemented the steps. Once you have all the components from the document in place, you can start setting up DataOps.

**Data Pipeline Environment:** You will need storage account containers to store the raw and processed data used in the sample DataOps implementation.

## The Sample Implementation

This repository includes an implementation of DataOps for the `named_entity_recognition` sample. The sample implementation uses Azure Machine Learning to run the data pipelines.

The data pipeline loads data from the source system, processes it, and stores it in the target location. The processed data is stored as JSONL files, which are registered as data assets

![dataops llmops](images/dataops_llmops.png)

The sample CI/CD pipelines manage the lifecycle of the data pipelines. They build and deploy the pipelines to the target environments. The CI/CD pipelines also register the required Datastores and Data Assets according to the processed JSONL files for Promptflow to consume.

If you are not using data pipelines to create the data assets, the Promptflow flows will use the JSONL files inside the `data` folder to create the data assets.

## Steps to Configure DataOps

Follow these steps to configure DataOps for your flow:

**New Folder for data pipelines** The data pipelines for the `named_entity_recognition` flow are inside a sub-folder named `data_pipelines`. Create a similar folder under your flow folder for the data pipelines.

**Configure source and target location** As mentioned earlier, the data pipeline loads data from a source storage account container and stores the processed data in a target storage account container. The processed data in the target storage account gets mapped to the azure machine learning Data Asset. Create these two containers and upload the source dataset to the source container.

**Data Pipeline Configuration:** The `dataops_config.json` file contains configurations for the data pipeline.

You can start by copying an existing config file and modify it with relevant values. Provide valid values for all the configuration elements.

**Updating Flow Configuration:** The configuration of the use-case is managed by the `experiment.yaml` (sets the flow paths, datasets, and evaluations). The `experiment.yaml` in the repo uses local data files. If you are using DataOps,this config file needs to point to the Data Asset path. The data asset path will look like this `azureml://datastores/[data_store_name]/paths/[file_path]`

Update any datasets elements in the `experiment.yaml` files and make sure the source field point to the Data Asset path in format `azureml:<my_data_asset_name>`

**Create Data Pipelines** The `named_entity_recognition` use case provides a sample python file for a data pipeline - [prep_data.py](../named_entity_recognition/data_pipelines/aml/prep_data.py). This is a placeholder for your data pipeline code. Replace it with your actual data transformation script.