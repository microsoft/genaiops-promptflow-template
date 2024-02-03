import argparse
from pathlib import Path
from typing_extensions import Concatenate
from uuid import uuid4
from datetime import datetime
import os
import pandas as pd
import shutil

def main(raw_data_dir, target_dir):
    df = pd.read_csv(os.path.join(raw_data_dir, 'data.txt'), sep='\t')
    df.to_json("data.jsonl", orient="records", lines=True)
    shutil.copyfile("data.jsonl", os.path.join(target_dir, 'data.jsonl'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--raw_data_dir",
        type=str,
        help="Path to raw data",
    )
    parser.add_argument(
        "--target_dir",
        type=str,
        help="Path to target dir",
    )

    args = parser.parse_args()
    raw_data_dir = args.raw_data_dir
    target_dir = args.target_dir

    main(raw_data_dir, target_dir)
