import argparse
import json
import os

import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
import io

# Replace the following code with the real data transformation code. This is just a placeholder data pipeline.

def prepare_data(blob_service_client, 
         source_container_name, 
         target_container_name, 
         source_blob, 
         exp_blob, 
         eval_blob):
    print('Data processing component')

    source_blob_client = blob_service_client.get_blob_client(container=source_container_name, blob=source_blob)
    source_blob_content = source_blob_client.download_blob().readall()

    df = pd.read_csv(io.StringIO(source_blob_content.decode('utf-8')))

    jsonl_list = []
    for _, row in df.iterrows():
        jsonl_list.append(json.dumps(row.to_dict()))

    exp_blob_client = blob_service_client.get_blob_client(container=target_container_name, blob=exp_blob)
    exp_blob_client.upload_blob('\n'.join(jsonl_list), overwrite=True)

    eval_blob_client = blob_service_client.get_blob_client(container=target_container_name, blob=eval_blob)
    eval_blob_client.upload_blob('\n'.join(jsonl_list), overwrite=True)

    print("CSV data converted to JSONL and uploaded successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--storage_account",
        type=str,
        help="storage account",
    )
    parser.add_argument(
        "--sa_sas_token",
        type=str,
        help="sas token",
    )
    parser.add_argument(
        "--source_container_name",
        type=str,
        help="source container name",
    )
    parser.add_argument(
        "--target_container_name",
        type=str,
        help="target container name",
    )
    parser.add_argument(
        "--source_blob",
        type=str,
        help="source blob file (csv)",
    )
    parser.add_argument(
        "--exp_blob",
        type=str,
        help="exp blob file (jsonl)"
    )
    parser.add_argument(
        "--eval_blob",
        type=str,
        help="eval blob file (jsonl)"
    )

    args = parser.parse_args()
    storage_account = args.storage_account
    sa_sas_token = args.sa_sas_token
    source_container_name = args.source_container_name
    target_container_name = args.target_container_name
    source_blob = args.source_blob
    exp_blob = args.exp_blob
    eval_blob = args.eval_blob
        
    storage_account_url = f"https://{storage_account}.blob.core.windows.net"

    blob_service_client = BlobServiceClient(storage_account_url, credential=sa_sas_token)

    prepare_data(blob_service_client, source_container_name, target_container_name, source_blob, exp_blob, eval_blob)
