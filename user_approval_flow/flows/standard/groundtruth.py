import csv
import re
import pandas as pd
from io import BytesIO, StringIO
from azure.storage.blob import BlobClient, BlobServiceClient
from promptflow import tool


def sanitise_input(rejected_rows):
    llm_output = rejected_rows.replace("'", "")
    llm_output = re.sub(r"\\n", "\n", llm_output)
    llm_output = re.sub(r"\"", "", llm_output)
    return llm_output


def get_groundtruth_from_blob():
    blob_client = BlobClient(
        account_url="https://machinelearnin9698811707.blob.core.windows.net",
        container_name="user-approval-groundtruth",
        blob_name="groundtruth_updated.xlsx",
        credential="yRxJUHTldT8mf5sUvwzKHj8xu4mnHFbxXJ3loZ1v45BEg7K8f5D0xlq3IX8prAMjVlKKidVV+kQN+AStpeL1vg==",
    )

    blob_data = blob_client.download_blob()
    blob_stream = BytesIO()
    blob_data.readinto(blob_stream)
    blob_stream.seek(0)

    # Use pandas to read the Excel file from the blob stream
    get_blob_data = pd.ExcelFile(blob_stream, engine="openpyxl")
    data_frame = get_blob_data.parse()
    return data_frame


# iterate through each row in the dictreader
#   check if there exists a matching ID in the ID column of the data_frame
#     if it exists, then update the value of the 'LLM Prediction' column of that row with the 'Status' value from the current row in dictreader
#     otherwise, create a new row with 'LLM Prediction' column of that row having the 'Status' value from the current row in dictreader
def update_groundtruth(reader, data_frame):
    flow_output = "\nID\tStatus\n----------------\n"
    count = 0
    for row in reader:
        flow_output += row["ID"] + "\t" + row["Status"] + "\n"
        df_row_index_value = data_frame.index[data_frame["ID"] == int(row["ID"])].values
        if df_row_index_value.size == 1:
            # print(df_row_index_value[0])
            data_frame.loc[df_row_index_value[0], "LLM Prediction"] = row["Status"]
        else:
            new_row = {
                "Firstname": "N/A",
                "Lastname": "N/A",
                "ID": int(row["ID"]),
                "Status": "Fake",
                "Software": "N/A",
                "LLM Prediction": row["Status"],
            }
            data_frame.loc[len(data_frame)] = new_row
        count += 1
    return flow_output


def save_df_to_excel_blob(data_frame):
    # Convert DataFrame to excel
    excel_buffer = BytesIO()
    data_frame.to_excel(excel_buffer, index=False)
    excel_data = excel_buffer.getvalue()

    # Save the modified file to blob
    blob_service_client = BlobServiceClient.from_connection_string(
        "DefaultEndpointsProtocol=https;AccountName=machinelearnin9698811707;AccountKey=yRxJUHTldT8mf5sUvwzKHj8xu4mnHFbxXJ3loZ1v45BEg7K8f5D0xlq3IX8prAMjVlKKidVV+kQN+AStpeL1vg==;EndpointSuffix=core.windows.net"
    )

    blob_client_upload = blob_service_client.get_blob_client(
        container="user-approval-groundtruth", blob="groundtruth_updated.xlsx"
    )
    blob_client_upload.upload_blob(excel_data, overwrite=True)


# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need
@tool
def my_python_tool(rejected_rows: str) -> str:

    llm_output = sanitise_input(rejected_rows)

    # Parse the CSV file with DictReader
    csv_data = StringIO(llm_output)
    reader = csv.DictReader(csv_data)

    # Get groundtruth file from blob
    data_frame = get_groundtruth_from_blob()

    # Add a new column if it doesnt exist
    if "LLM Prediction" not in data_frame.columns:
        data_frame["LLM Prediction"] = "approved"

    # Update the groundtruth file with the LLM predictions
    update_groundtruth(reader, data_frame)

    # Save the modified file to blob
    save_df_to_excel_blob(data_frame)

    return llm_output
