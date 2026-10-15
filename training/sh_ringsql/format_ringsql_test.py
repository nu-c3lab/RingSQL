"""
A script for putting the raw RingSQL outputs into a format that can be used for testing.
"""

import sys
import json
import argparse
import pandas as pd
from tqdm import tqdm

def main():
    parser = argparse.ArgumentParser(description="Convert a RingSQL JSON data file to a JSON file that can be used for testing.")
    parser.add_argument("--input-path", type=str, required=True, help="Path to the input JSON file")
    parser.add_argument("--output-path", type=str, required=True, help="Path to the output JSON file")
    args = parser.parse_args()

    try:
        # Read JSON
        with open(args.input_path, "r") as f:
            original_ringsql_data = json.load(f)

        # Format the data (assumes the JSON is a list of dictionary items to be formatted)
        formatted_data = []
        for idx, d in enumerate(tqdm(original_ringsql_data)):
            updated_instance = {
                "db_id": d["db_id"],
                "query": d["query"],
                "question": d["question"],
                "original_base_plan": d["base_plan"]
            }
            formatted_data.append(updated_instance)

        # Convert the data to a dataframe and write it to a parquet file
        df = pd.DataFrame(formatted_data)
        df.to_json(args.output_path, orient='records', indent=4)
        print(f"✅ Wrote {len(df)} records to {args.output_path}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()