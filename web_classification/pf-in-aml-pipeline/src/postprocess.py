import argparse

import pandas as pd
from pathlib import Path

PF_OUTPUT_FILE_NAME = "parallel_run_step.jsonl"
def parse_args():
    """
    Parses the user arguments.

    Returns:
        argparse.Namespace: The parsed user arguments.
    """
    parser = argparse.ArgumentParser(
        allow_abbrev=False, description="parse user arguments"
    )
    parser.add_argument("--input_data_path", type=str)

    args, _ = parser.parse_known_args()
    return args


def main():
    """
    The main function that orchestrates the data preparation process.
    """
    args = parse_args()
    
    # Read promptflow output file and do some postprocessing
    input_data_path = args.input_data_path + '/' + PF_OUTPUT_FILE_NAME
    with open((Path(input_data_path)), 'r') as file:
        promptflow_output = pd.read_json(file, lines=True)
        print(promptflow_output.head())
        
    return

if __name__ == "__main__":
    main()
