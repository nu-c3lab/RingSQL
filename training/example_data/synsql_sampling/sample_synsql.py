import json
import random
import sqlite3
import argparse
from pathlib import Path
from collections import defaultdict
from typing import *

def execute_query(db_path: str,
                  query: str) -> bool:
    """Execute a SQL query and return True if it yields non-empty results."""
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        conn.close()
        print(len(rows))
        return len(rows) > 0
    except Exception:
        return False

def uniform_sample(data: List[Dict],
                   db_root: str,
                   num_samples: int) -> List[Dict]:
    """Uniform sampling with execution filtering."""

    random.shuffle(data)

    valid_samples = []

    for item in data:
        if len(valid_samples) >= num_samples:
            break

        query = item.get("sql")
        db_id = item.get("db_id")
        if query is None or db_id is None:
            continue

        db_path = Path(db_root) / db_id / f"{db_id}.sqlite"
        if not db_path.exists():
            print(f"Database '{db_path}' not found.")
            continue

        if execute_query(db_path, query):
            valid_samples.append(item)
            print(f"Sampled {len(valid_samples)}")

    return valid_samples


def main(json_path: str,
         db_root: str,
         num_train_samples: int,
         num_dev_samples: int,
         train_output_path: str,
         dev_output_path: str) -> None:

    with open(json_path, "r") as f:
        data = json.load(f)
    print(f"Read in the data at {json_path}")

    total_num_samples = num_train_samples + num_dev_samples
    samples = uniform_sample(data, db_root, total_num_samples)
    print(f"Collected {len(samples)} valid samples")

    # Get train and dev splits
    train_samples = samples[:num_train_samples]
    dev_samples = samples[num_train_samples : num_train_samples+num_dev_samples]

    # Write out the samples to the train file
    with open(train_output_path, "w") as f:
        for item in train_samples:
            item["external_knowledge"] = ""
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            # json.dump(train_samples, f, indent=2)
    print(f"Wrote out {len(train_samples)} valid samples to {train_output_path}")

    # Write out the samples to the dev file
    with open(dev_output_path, "w") as f:
        for item in dev_samples:
            item["external_knowledge"] = ""
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
        # json.dump(dev_samples, f, indent=2)
    print(f"Wrote out {len(dev_samples)} valid samples to {dev_output_path}")

    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json_path", required=True)
    parser.add_argument("--db_root", required=True)
    parser.add_argument("--num_train_samples", type=int, required=True)
    parser.add_argument("--num_dev_samples", type=int, required=True)
    parser.add_argument("--train_output_path", required=True)
    parser.add_argument("--dev_output_path", required=True)

    args = parser.parse_args()

    main(json_path=args.json_path,
         db_root=args.db_root,
         num_train_samples=args.num_train_samples,
         num_dev_samples=args.num_dev_samples,
         train_output_path=args.train_output_path,
         dev_output_path=args.dev_output_path)
