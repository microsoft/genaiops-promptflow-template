from promptflow import tool
from promptflow.connections import CustomConnection
from llama_index.core.schema import Document
from azure.storage.blob import BlobServiceClient
from io import StringIO
import csv

# Credentials for Storages
STORAGE_ACCOUNT_NAME = "machinelearnin9698811707"
ORIGIN_CONTAINER_NAME = "user-approval-data"
TARGET_CONTAINER_NAME = "user-approval-processed"


def read_csv(
    blob_service_client: BlobServiceClient, container_name: str, blob_path: str
):

    # Get a BlobClient object
    blob_client = blob_service_client.get_blob_client(
        container=container_name, blob=blob_path
    )

    # Download the blob's content as a string
    csv_data = blob_client.download_blob().content_as_text()
    csv_buffer = StringIO(csv_data)
    csv_reader = csv.DictReader(csv_buffer)

    # Create a list of Document objects
    docs = []
    for row in csv_reader:
        doc = Document(
            text=",".join(f"{v.strip()}" for k, v in row.items()),
            extra_info=None or {},
        )
        docs.append(doc.text)

    return docs


def move_blob(blob_service_client: BlobServiceClient, blob_path: str, blob_url: str):
    copied_blob = blob_service_client.get_blob_client(TARGET_CONTAINER_NAME, blob_path)
    status = copied_blob.start_copy_from_url(blob_url)["copy_status"]
    return status


def delete_blobs(
    blob_service_client: BlobServiceClient, container_name: str, moved_blobs: list
):
    for blob_path in moved_blobs:
        blob_client = blob_service_client.get_blob_client(
            container=container_name, blob=blob_path
        )
        blob_client.delete_blob()


@tool
# Steps:
# 1. Read CSV files from the blob storage
# 2. Copy the files to another container
# 3. Delete the original files
def my_python_tool(myconn: CustomConnection) -> list:
    NUM_BLOBS = 3
    # # Create a BlobServiceClient
    # blob_service_client = BlobServiceClient(
    #     account_url=STORAGE_ACCOUNT_URL,
    #     credential=STORAGE_ACCOUNT_KEY,
    # )

    blob_service_client = BlobServiceClient.from_connection_string(
        myconn.connection_string
    )

    # Get container client
    container_client = blob_service_client.get_container_client(ORIGIN_CONTAINER_NAME)

    # List blobs in the container
    blob_list = container_client.list_blobs()

    docs = []
    moved_blobs = []

    for blob in blob_list:
        blob_path = blob.name
        blob_url = f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{ORIGIN_CONTAINER_NAME}/{blob_path}"
        if NUM_BLOBS == 0:
            break
        else:
            # Read the CSV file, and append the documents to the docs list
            docs += read_csv(blob_service_client, ORIGIN_CONTAINER_NAME, blob_path)
            # Copy the blob to another container
            move = move_blob(blob_service_client, blob_path, blob_url)
            # If the blob is successfully copied, add it to the list to be deleted
            if move == "success":
                moved_blobs.append(blob_path)
            NUM_BLOBS -= 1

    # Delete the original blobs
    delete_blobs(blob_service_client, ORIGIN_CONTAINER_NAME, moved_blobs)
    return docs
