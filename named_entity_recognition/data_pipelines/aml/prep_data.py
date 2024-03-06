import argparse
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

# Steps
# 1. Read the source blob file
# 2. Change the file from csv to jsonl
# 3. Save it as the jsonl file in the target account as eval and exp blob
def main(source_blob_service_client, source_blob, target_blob_service_client, eval_blob, exp_blob):
    # df = pd.read_csv(os.path.join(raw_data_dir, 'data.txt'), sep='\t')
    # df.to_json("data.jsonl", orient="records", lines=True)
    # shutil.copyfile("data.jsonl", os.path.join(target_dir, 'data.jsonl'))
    print('data processing component')

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
    source_container_name = args.source_container_name
    target_container_name = args.target_container_name
    source_blob = args.source_blob
    eval_blob = args.eval_blob
    exp_blob = args.exp_blob

    default_credential = DefaultAzureCredential()

    source_account_url = f"https://{source_storage_account}.blob.core.windows.net"
    source_blob_service_client = BlobServiceClient(source_account_url, credential=default_credential)

    target_account_url = "https://{target_storage_account}.blob.core.windows.net"
    target_blob_service_client = BlobServiceClient(target_account_url, credential=default_credential)

    main(source_blob_service_client, source_blob, target_blob_service_client, eval_blob, exp_blob)
