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
         source_blob,
         target_blob_service_client):
    print('data processing component')
    # Get the source blobs
    source_blob_client = source_blob_service_client.get_blob_client(container=source_container_name, blob=source_blob)
    # Read the content of the source blobs
    source_blob_content = source_blob_client.download_blob().readall()

    # Read the CSV content into a Pandas DataFrame
    df = pd.read_csv(pd.compat.StringIO(source_blob_content.decode('utf-8')))

    # Convert DataFrame rows to JSONL format
    jsonl_list = []
    for _, row in df.iterrows():
        jsonl_list.append(json.dumps(row.to_dict()))

    # Write JSONL data to a file (optional, if you want to save it locally)
    jsonl_file_path = 'data.jsonl'  # Replace with your desired local path
    with open(jsonl_file_path, 'w') as jsonl_file:
        for line in jsonl_list:
            jsonl_file.write(line + '\n')

    # Upload JSONL data to the target container
    target_blob_client = target_blob_service_client.get_blob_client(container=target_container_name, blob=source_blob)
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
        "--source_blob",
        type=str,
        help="source blob file (csv)",
    )

    args = parser.parse_args()
    source_storage_account = args.source_storage_account
    target_storage_account = args.target_storage_account
    source_container_name = args.source_container_name
    target_container_name = args.target_container_name
    source_blob = args.source_blob

    default_credential = DefaultAzureCredential()

    source_account_url = f"https://{source_storage_account}.blob.core.windows.net"
    source_blob_service_client = BlobServiceClient(source_account_url, credential=default_credential)

    target_account_url = "https://{target_storage_account}.blob.core.windows.net"
    target_blob_service_client = BlobServiceClient(target_account_url, credential=default_credential)

    prep(source_blob_service_client, source_blob, target_blob_service_client)
