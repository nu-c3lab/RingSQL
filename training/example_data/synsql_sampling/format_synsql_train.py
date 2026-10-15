import os
import sys
import json
import random
import argparse
import pandas as pd
from typing import *
from tqdm import tqdm

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

def load_sql_files(directory) -> Dict[str, str]:
    """Load in the contents of the DDL files."""
    sql_files = {}
    for filename in os.listdir(directory):
        if filename.endswith(".sql"):
            filepath = os.path.join(directory, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                sql_files[os.path.splitext(filename)[0]] = f.read()
    return sql_files

def main():
    parser = argparse.ArgumentParser(description="Convert a JSON file to a Parquet file.")
    parser.add_argument("--input-path", type=str, required=True, help="Path to the input JSON file")
    parser.add_argument("--spider-ddl-dir", type=str, required=True, help="Path to the directory with the SPIDER database DDL files")
    parser.add_argument("--output-path", type=str, required=True, help="Path to the output Parquet file")
    parser.add_argument("--split", type=str, required=True, help="Data split the input file corresponds to")
    args = parser.parse_args()

    try:
        # Read JSON
        with open(args.input_path, "r") as f:
            data = json.load(f)

        # Read in the extracted schema DDL and pass in the right one to the format_instance() function
        db_id_to_ddl = load_sql_files(args.spider_ddl_dir)

        # Format the data (assumes the JSON is a list of dictionary items to be formatted)
        formatted_data = []
        for idx, d in enumerate(tqdm(data)):
            db_id = d["db_id"]
            formatted_instance = format_instance(question=d["question"],
                                                 database_schema=db_id_to_ddl[db_id],
                                                 data_source="spider",
                                                 db_id=db_id,
                                                 query=d["query"],
                                                 split=args.split,
                                                 idx=idx)
            formatted_data.append(formatted_instance)

        # Shuffle the data
        random.shuffle(formatted_data)

        # Convert the data to a dataframe and write it to a parquet file
        df = pd.DataFrame(formatted_data)
        df.to_parquet(args.output_path, index=False)
        # df.to_json("./formatted.json", orient='records', indent=4)      # can uncomment this to examine outputs more easily
        print(f"✅ Wrote {len(df)} records to {args.output_path}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
