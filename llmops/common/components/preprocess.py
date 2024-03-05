import argparse

import pandas as pd


def parse_args():
    """
    Parses the user arguments.

    Returns:
        argparse.Namespace: The parsed user arguments.
    """
    parser = argparse.ArgumentParser(
        allow_abbrev=False, description="parse user arguments"
    )
    parser.add_argument("--max_records", type=int, default=1)
    parser.add_argument("--input_data_path", type=str)
    parser.add_argument("--output_data_path", type=str)

    args, _ = parser.parse_known_args()
    return args


def main():
    """
    The main function that orchestrates the data preparation process.
    """
    args = parse_args()
    print("Maximum records to keep", args.max_records)

    input_data_path = args.input_data_path
    input_data_df = pd.read_json(input_data_path, lines=True)

    # take only max_records from input_data_df
    input_data_df = input_data_df.head(args.max_records)

    # Write input_data_df to a jsonl file
    input_data_df.to_json(
        args.output_data_path + "output_data.jsonl", orient="records", lines=True
    )
    print("Successfully written filtered data")

    return


if __name__ == "__main__":
    main()
