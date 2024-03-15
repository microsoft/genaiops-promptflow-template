import argparse
import json

import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient


# Steps
# 1. Read the source blob file
# 2. Change the file from csv to jsonl
# 3. Save it as the jsonl file in the target account
def prep(source_blob_service_client, 
         target_blob_service_client, 
         source_container_name, 
         target_container_name, 
         source_blob, 
         target_blob):
    print('Data processing component')

    # Get the source blob
    source_blob_client = source_blob_service_client.get_blob_client(container=source_container_name,
                                                                        blob=source_blob)
    # Read the content of the source blob
    source_blob_content = source_blob_client.download_blob().readall()

    # Read the CSV content into a Pandas DataFrame (sample data processing)
    df = pd.read_csv(pd.compat.StringIO(source_blob_content.decode('utf-8')))

    # Convert DataFrame rows to JSONL format
    jsonl_list = []
    for _, row in df.iterrows():
        jsonl_list.append(json.dumps(row.to_dict()))

    # Upload JSONL data to the target container
    target_blob_client = target_blob_service_client.get_blob_client(container=target_container_name,
                                                                        blob=target_blob)
    target_blob_client.upload_blob('\n'.join(jsonl_list), overwrite=True)

    print("CSV data converted to JSONL and uploaded successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source_storage_account",
        type=str,
        help="source storage account",
    )
    parser.add_argument(
        "--target_storage_account",
        type=str,
        help="target storage account",
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
        "--source_sa_sas_toekn",
        type=str,
        help="source container name",
    )
    parser.add_argument(
        "--target_sa_sas_toekn",
        type=str,
        help="target container name",
    )
    parser.add_argument(
        "--source_blob",
        type=str,
        help="source blob file (csv)",
    )
    parser.add_argument(
        "--target_blob",
        type=str,
        help="target asset path"
    )

    args = parser.parse_args()
    source_storage_account = args.source_storage_account
    target_storage_account = args.target_storage_account
    source_container_name = args.source_container_name
    target_container_name = args.target_container_name
    source_blob = args.source_blob
    target_blob = args.target_blob
    source_sa_sas_toekn = args.source_sa_sas_toekn
    target_sa_sas_toekn = args.target_sa_sas_toekn

    default_credential = DefaultAzureCredential()

    source_account_url = f"https://{source_storage_account}.blob.core.windows.net"
    source_blob_service_client = BlobServiceClient(source_account_url, credential=source_sa_sas_toekn)

    target_account_url = "https://{target_storage_account}.blob.core.windows.net"
    target_blob_service_client = BlobServiceClient(target_account_url, credential=target_sa_sas_toekn)

    prep(source_blob_service_client, target_blob_service_client, source_container_name, target_container_name, source_blob, target_blob)
