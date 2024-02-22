# Promptflow in Azure Machine Learning Pipeline

## Overview
To provide scalability and reliability, we can run promptflow in Azure Machine Learning pipeline. Azure Machine Learning provides a scalable and reliable environment to run the promptflow jobs. It also provides observability and monitoring for the pipeline runs.

Go to [Use Flow in Azure ML Pipeline Job](https://microsoft.github.io/promptflow/cloud/azureai/use-flow-in-azure-ml-pipeline.html?highlight=pipeline#directly-use-a-flow-in-a-pipeline-job) for more details.

## Prerequisites
1. Azure ML workspace 

## Steps to run the AML pipeline
1. Go to the default blob data store of AML workspace.
2. Upload the input data  `web_classification/data/data.jsonl` to a new `./pf_in_pipeline/` folder in the AML default blob store.
3. Create an azure openai connection with name `aoai` in Promptflow connections in AML workspace.
4. Update your .env.template in `pf-in-aml-pipeline` folder with the required values and rename it to .env
5. Setup a python environment with the packages mentioned in requirements.txt:
```bash
pip install -r requirements.txt
```
6. Run the following commands to execute the pipeline:
```bash
cd pf-in-aml-pipeline
python run_pipeline.py
```
7. Go to AML workspace and check the pipeline run status.