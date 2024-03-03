import argparse
from pathlib import Path
from typing_extensions import Concatenate
from uuid import uuid4
from datetime import datetime
import os
import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

# Steps
# 1. Read the source blob file
# 2. Change the file from csv to jsonl
# 3. Save it as the jsonl file in the target account as eval and exp blob
def main(source_blob_service_client, source_blob, target_blob_service_client, eval_blob, exp_blob):
    print('data processing component')
    # df = pd.read_csv(os.path.join(raw_data_dir, 'data.txt'), sep='\t')
    # df.to_json("data.jsonl", orient="records", lines=True)
    # shutil.copyfile("data.jsonl", os.path.join(target_dir, 'data.jsonl'))

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
        "--source_blob",
        type=str,
        help="source blob file",
    )
    parser.add_argument(
        "--eval_blob",
        type=str,
        help="evaluation blob file",
    )
    parser.add_argument(
        "--exp_blob",
        type=str,
        help="experimentation blob file",
    )

    args = parser.parse_args()
    source_storage_account = args.source_storage_account
    target_storage_account = args.target_storage_account
    source_blob = args.source_blob
    eval_blob = args.eval_blob
    exp_blob = args.exp_blob

    default_credential = DefaultAzureCredential()

    source_account_url = f"https://{source_storage_account}.blob.core.windows.net"
    source_blob_service_client = BlobServiceClient(source_account_url, credential=default_credential)

    target_account_url = "https://{target_storage_account}.blob.core.windows.net"
    target_blob_service_client = BlobServiceClient(target_account_url, credential=default_credential)

    main(source_blob_service_client, source_blob, target_blob_service_client, eval_blob, exp_blob)
