import argparse
import json

import pandas as pd
from azure.storage.blob import BlobServiceClient
import io

# Replace the following code with the real data transformation code. This is just a placeholder data pipeline.

def prepare_data(blob_service_client, 
         source_container_name, 
         target_container_name, 
         source_blob, 
         target_data_assets):
    print('Data processing component')

    source_blob_client = blob_service_client.get_blob_client(container=source_container_name, blob=source_blob)
    source_blob_content = source_blob_client.download_blob().readall()

    df = pd.read_csv(io.StringIO(source_blob_content.decode('utf-8')))

    jsonl_list = []
    for _, row in df.iterrows():
        jsonl_list.append(json.dumps(row.to_dict()))

    # Upload JSONL data to the target container
    target_data_assets_list = json.loads(target_data_assets)
    for target_data_asset in target_data_assets_list:
        file_name = target_data_asset['PATH']
        target_blob_client = blob_service_client.get_blob_client(container=target_container_name,
                                                                            blob=file_name)
        target_blob_client.upload_blob('\n'.join(jsonl_list), overwrite=True)

        print(f"CSV data converted to JSONL and uploaded successfully!: {file_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--storage_account",
        type=str,
        help="storage account",
    )
    parser.add_argument(
        "--sa_acc_key",
        type=str,
        help="sa account key",
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
        "--assets",
        type=str,
        help="target assets to be created"
    )

    args = parser.parse_args()
    storage_account = args.storage_account
    sa_acc_key = args.sa_acc_key
    source_container_name = args.source_container_name
    target_container_name = args.target_container_name
    source_blob = args.source_blob
    target_data_assets = args.assets
        
    storage_account_url = f"https://{storage_account}.blob.core.windows.net"

    blob_service_client = BlobServiceClient(storage_account_url, credential=sa_acc_key)

    prepare_data(blob_service_client, source_container_name, target_container_name, source_blob, target_data_assets)
