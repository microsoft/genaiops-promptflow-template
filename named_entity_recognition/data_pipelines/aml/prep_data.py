import argparse
import json

import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
import io

"""
This function prepares data for processing.
It reads a CSV file from a source blob storage,
converts the CSV data to JSONL (JSON Lines) format,
and then uploads the JSONL data to a target blob storage.

Args:
--blob_service_client: The Azure blob service client.
This argument is required for interacting with Azure blob storage.
--source_container_name: The name of the source container in blob storage.
This argument is required to specify the source container from where the CSV data is read.
--target_container_name: The name of the target container in blob storage.
This argument is required to specify the target container to where the JSONL data is uploaded.
--source_blob: The name of the source blob in the source container.
This argument is required to specify the source blob from where the CSV data is read.
--target_data_assets: The target data assets in the target container.
This argument is required to specify the target data assets to where the JSONL data is uploaded.
"""


def prepare_data(blob_service_client,
                 source_container_name,
                 target_container_name,
                 source_blob,
                 target_data_assets):
    print('Data processing component')

    source_blob_client = blob_service_client.get_blob_client(container=source_container_name,
                                                             blob=source_blob)
    source_blob_content = source_blob_client.download_blob().readall()

    assets = [item.strip() for item in target_data_assets.split(":")]

    df = pd.read_csv(io.StringIO(source_blob_content.decode('utf-8')))

    jsonl_list = []
    for _, row in df.iterrows():
        jsonl_list.append(json.dumps(row.to_dict()))

    # Upload JSONL data to the target container
    for asset in assets:
        target_blob_client = blob_service_client.get_blob_client(container=target_container_name,
                                                                 blob=asset)
        target_blob_client.upload_blob('\n'.join(jsonl_list), overwrite=True)
        print(f"CSV data converted to JSONL and uploaded successfully!: {asset}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--storage_account",
        type=str,
        help="storage account",
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
        "--assets_str",
        type=str,
        help="target assets to be created as a string"
    )

    args = parser.parse_args()
    storage_account = args.storage_account
    source_container_name = args.source_container_name
    target_container_name = args.target_container_name
    source_blob = args.source_blob
    target_data_assets = args.assets_str

    storage_account_url = f"https://{storage_account}.blob.core.windows.net"

    blob_service_client = BlobServiceClient(storage_account_url,
                                            credential=DefaultAzureCredential())

    prepare_data(blob_service_client,
                 source_container_name,
                 target_container_name,
                 source_blob,
                 target_data_assets)
