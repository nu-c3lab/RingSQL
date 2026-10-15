import os
import re
import sys
import json
import random
import sqlite3
import argparse
from typing import *
from pathlib import Path

import pandas as pd

def read_jsonl(file_path: str) -> Generator:
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():  # skip empty lines
                yield json.loads(line)

def get_user_and_system_messages(question: str,
                                 db_schema: str) -> Tuple[str, str]:
    external_knowledge = ""
    sql_complexity = "Complex"

    # Build the system prompt message
    system_message = f"""You are a helpful SQL expert assistant.
The assistant first thinks about how to write the SQL query by analyzing the question, database schema and external knowledge, then provides the final SQL query.
The reasoning process and SQL query are enclosed within <think> </think> and <answer> </answer> tags respectively.
The answer must contain the SQL query within ```sql ``` tags.

Database Schema:
{db_schema}

External Knowledge:
{external_knowledge}

SQL Complexity Level: {sql_complexity}

For example:
<think>
To translate the given natural language question into an executable SQLite query, we need to follow these detailed steps:
1. **Identify Key Elements**: The question queries for code snippets that are both complicated (complexity score > 5) and public (`is_public` = 1). We need to retrieve their descriptions and complexity scores.
2. **Focus on Relevant Tables**: The `code_snippets` table contains the necessary fields (`description`, `complexity`, `is_public`).
3. **Construct the Query**: We should select the required fields (`description` and `complexity`) from the `code_snippets` table. We also apply the conditions specified in the question to filter the results.
4. **Ordering**: The reference solution includes an `ORDER BY` clause to sort results by complexity in descending order, which is a reasonable way to present the data to highlight the most complex snippets first.
5. **Final Query Construction**: Putting all this together into a SQL query.
</think>
<answer>
Here's how the query can be written:
```sql
SELECT description, complexity FROM code_snippets WHERE complexity > 5 AND is_public = 1 ORDER BY complexity DESC;
```
This query retrieves the descriptions and complexity scores of code snippets that are both complicated (complexity > 5) and publicly available (`is_public` = 1), sorted by complexity in descending order.
This solution is straightforward and precisely matches the requirements of the question. It avoids unnecessary complexities, such as joining or selecting columns not relevant to the query itself.
</answer>"""

    # Build the user prompt message
    user_message = question

    return system_message, user_message

def format_instance(question: str,
                    database_schema: str,
                    data_source: str,
                    db_id: str,
                    query: str,
                    idx: int,
                    split: str) -> Dict:
    # "question": ...
    # "db_id": ...
    # "external_knowledge": "" (empty)
    # "sql": ...
    # "data_source": "synsql" --> "spider"
    # "prompt": [ {"content": "<input prompt>", "role": "user"} ]
    # "ability": "logic",
    # "reward_model": {
    #       "ground_truth": {
    #         "db_id": <db_id string>,
    #         "sql": <ground truth SQL string>
    #       },
    #       "style": "rule"
    #     }
    # "extra_info": {
    #       "index": 2,
    #       "split": "train"
    #     }

    system_message, user_message = get_user_and_system_messages(question, database_schema)

    solution = {
        "db_id": db_id,
        "sql": query
    }
    data = {
        "question": question,
        "db_id": db_id,
        "external_knowledge": "",
        "sql": query,
        "data_source": data_source,
        "prompt": [
            {
                "role": "system",
                "content": system_message
            },
            {
                "role": "user",
                "content": user_message,
            }
        ],
        "ability": "logic",
        "reward_model": {
            "style": "rule",
            "ground_truth": solution
        },
        "extra_info": {
            "split": split,
            "index": idx
        }
    }
    return data

def parse_question(instruction_text: str) -> Optional[str]:
    match = re.search(r'Question:\s*(.+?)$', instruction_text, re.MULTILINE)
    return match.group(1).strip() if match else None

def parse_schema(instruction_text: str) -> str:
    # Remove /* ... */ comment blocks (example rows)
    no_comments = re.sub(r'/\*.*?\*/', '', instruction_text, flags=re.DOTALL)

    # Extract all CREATE TABLE statements
    tables = re.findall(r'(CREATE TABLE.*?;)', no_comments, re.DOTALL)

    return '\n\n'.join(t.strip() for t in tables)

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

def main():
    parser = argparse.ArgumentParser(description="Sample text-to-sql data from SENSE and create the train/dev Parquet files required for RL for training.")
    parser.add_argument("--input-path", type=str, required=True, help="Path to the input JSONL file")
    parser.add_argument("--output-dir", type=str, required=True, help="Directory to write the final train/dev Parquet files to.")
    parser.add_argument("--db-root", type=str, required=True, help="Path to the Spider databases.")
    args = parser.parse_args()

    try:
        formatted_data = []
        for idx, l in enumerate(read_jsonl(args.input_path)):
            question = parse_question(l["instruction"])
            database_schema = parse_schema(l["instruction"])
            data_source: str = 'spider'
            db_id: str = l['db_id']
            query: str = l['output']
            split: str = 'train'
            formatted_instance = format_instance(question,
                                                 database_schema,
                                                 data_source,
                                                 db_id,
                                                 query,
                                                 idx,
                                                 split)

            formatted_data.append(formatted_instance)

        # Shuffle the data
        random.shuffle(formatted_data)

        # Make sure the queries run and return at least one row of results
        num_train = 4000
        num_dev = 1000
        executable_and_formatted_data = uniform_sample(formatted_data, args.db_root, num_train + num_dev)
        print(f"Collected {len(executable_and_formatted_data)} valid samples")

        # Split into train and dev splits of 4000/1000
        train_split = executable_and_formatted_data[:num_train]
        dev_split = executable_and_formatted_data[num_train:num_train+num_dev]

        # Convert the data splits to a dataframes and write them to parquet files
        train_path = os.path.join(args.output_dir, 'train.parquet')
        dev_path = os.path.join(args.output_dir, 'dev.parquet')

        train_df = pd.DataFrame(train_split)
        dev_df = pd.DataFrame(dev_split)

        train_df.to_parquet(train_path, index=False)
        print(f"✅ Wrote {len(train_df)} 'train' records to {train_path}")
        dev_df.to_parquet(dev_path, index=False)
        print(f"✅ Wrote {len(dev_df)} 'dev' records to {dev_path}")

        # df.to_json("./formatted.json", orient='records', indent=4)      # can uncomment this to examine outputs more easily

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

