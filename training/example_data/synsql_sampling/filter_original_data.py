import json
import argparse
from tqdm import tqdm

KEEP_KEYS = {"db_id", "question", "sql", "sql_complexity"}

def main(input_path: str, output_path: str):
    with open(input_path, "r") as f:
        data = json.load(f)
    print(f"Read in the data at {input_path}")

    filtered = []
    for item in tqdm(data):
        filtered.append({k: item[k] for k in KEEP_KEYS if k in item})

    with open(output_path, "w") as f:
        json.dump(filtered, f, indent=2)

    print(f"Wrote {len(filtered)} examples to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_path", required=True)
    parser.add_argument("--output_path", required=True)
    args = parser.parse_args()

    main(args.input_path, args.output_path)
