import os
import sqlite3
from tqdm import tqdm
import json
import argparse
import time


class QueryTimeoutError(Exception):
    pass


def execute_with_timeout(conn, query, timeout_seconds=5.0, params=None):
    """
    Execute a SQLite query with a timeout.

    Args:
        conn: sqlite3 connection
        query: SQL query string
        timeout_seconds: Maximum execution time in seconds
        params: Query parameters (optional)

    Returns:
        Query results

    Raises:
        QueryTimeoutError: If query exceeds timeout
    """
    start_time = time.time()

    def progress_handler():
        if time.time() - start_time > timeout_seconds:
            return 1  # Non-zero aborts the query
        return 0  # Zero continues execution

    # Set progress handler (called every 100 VM instructions)
    conn.set_progress_handler(progress_handler, 100)

    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        results = cursor.fetchall()
        return results
    except sqlite3.OperationalError as e:
        # SQLite raises OperationalError when interrupted
        if "interrupted" in str(e).lower():
            raise QueryTimeoutError(
                f"Query exceeded {timeout_seconds}s timeout"
            )
        raise
    finally:
        # Always clear the progress handler
        conn.set_progress_handler(None, 0)


# def
# try:
#         # Fast query - should succeed
#         results = execute_with_timeout(
#             conn,
#             "SELECT * FROM users WHERE id = ?",
#             timeout_seconds=5.0,
#             params=(1,)
#         )
#         print(f"Got {len(results)} results")

#         # Slow query - will timeout
#         results = execute_with_timeout(
#             conn,
#             "SELECT * FROM large_table t1, large_table t2",  # Cartesian product
#             timeout_seconds=2.0
#         )

#     except QueryTimeoutError as e:
# print(f"Timeout: {e}")


def flatten_and_filter_none(nested_list):
    """Recursively flattens a nested list structure, yielding only non-None leaf values."""
    for item in nested_list:
        if item is not None:
            # If the item is a list/tuple, recurse into it
            if isinstance(item, (list, tuple)):
                yield from flatten_and_filter_none(item)
            # Otherwise, it's a leaf value, yield it
            else:
                yield item


# TODO: import this from standardize_sql? if not modified
def compare_queries(og_q, simple_q, db_id):
    db_name = db_id.split("-")[0]
    db_fn = f"../evaluation/database/{db_name}/{db_name}.sqlite"
    conn = sqlite3.connect(db_fn)
    # for handling special chars in wta_1 db
    conn.text_factory = lambda x: str(x, "latin1")
    og_results = None
    simple_results = None
    try:
        # og_results = conn.execute(og_q).fetchall()
        # simple_results = conn.execute(simple_q).fetchall()

        og_results = execute_with_timeout(conn, og_q)
        simple_results = execute_with_timeout(conn, simple_q)

        # print(og_results)
        # print(simple_results)
        # if (not og_results) or (not any(flatten_and_filter_none(og_results))):
        if (not og_results) or (not list(flatten_and_filter_none(og_results))):
            return -3
        if og_results == simple_results:
            return 1
        else:
            # handle diff from replacing LEFT OUTER JOIN WITH JOIN
            # if og_q.count("LEFT OUTER JOIN") == simple_q.count("JOIN"):
            # return 1
            # else:
            # return 0
            return 0
    except QueryTimeoutError as e:
        return -4
    except:
        if og_results is not None:
            return -1
        else:
            # print(og_q)
            # print(simple_q)
            # print(db_name)
            return -2
            # raise ValueError("Invalid original query")


def verify_queries(exs):
    execution_diffs = []
    null_results = []
    verified_exs = []
    timed_out_exs = []
    for ex in tqdm(exs):
        # ex["db_id"] = ex["ring_id"].split("-")[0]

        og_query = ex["og_query"]
        # print(og_query)
        simplified_query = ex["query"]
        # print(simplified_query)
        # if og_query.lower().replace("asc", " ").replace(
        #     " ", ""
        # ) != simplified_query.lower().replace(" ", ""):
        #     query_diffs.append(
        #         {
        #             "og_query": og_query,
        #             "simplified_query": simplified_query,
        #             "db_id": ex["db_id"],
        #         }
        #     )

        # ex["og_query"] = og_query
        # ex["query"] = simplified_query

        # TODO: exec on db and check results for diffs
        comparison = compare_queries(og_query, simplified_query, ex["db_id"])
        if comparison != 1:
            if comparison == -3:
                null_results.append(ex)
                continue
            elif comparison == -4:
                timed_out_exs.append(ex)
            execution_diffs.append(
                {
                    "og_query": og_query,
                    "simplified_query": simplified_query,
                    "db_id": ex["db_id"],
                    "comparison": comparison,
                    "bp": ex["base_plan"],
                }
            )
            continue

        verified_exs.append(ex)

    return verified_exs, execution_diffs, null_results, timed_out_exs


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_dir",
        # default="generated_data/satdb_from_bps_v0/sampled_data",
        # default="generated_data/satdb_from_bps_v0/sampled_data",
        # default="generated_data/satdb_from_bps_v0/standardized_removing_with"
        # default="generated_data/satdb_from_bps_final/standardized_sample"
        default="generated_data/satdb_from_spider_full_3x_simplified_v7_improved/standardized_sample",
    )
    parser.add_argument(
        "--output_dir",
        # default="generated_data/satdb_from_bps_v0/verified_sampled_data",
        # default="generated_data/satdb_from_bps_v0/all_verified_data",
        # default="generated_data/satdb_from_bps_final/verified_sampled_data"
        default="generated_data/satdb_from_spider_full_3x_simplified_v7_improved/verified_sample",
    )
    args = parser.parse_args()
    dir_in = args.input_dir
    # dir_in = "generated_data/satdb_from_bps_v0/standardized_sample"

    # takes too long to run on full dataset
    # dir_in = "generated_data/satdb_from_bps_v0/standardized_removing_with"

    dir_out = args.output_dir
    # dir_out = "generated_data/satdb_from_bps_v0/verified_sampled_data"
    # dir_out = "generated_data/satdb_from_bps_v0/all_verified_data"
    os.makedirs(dir_out, exist_ok=True)

    splits = ["dev.json", "test.json", "train.json"]
    # splits = ["test.json", "train.json"]
    # splits = ["dev.json"]
    # for fn in os.listdir(dir_in):
    for fn in splits:
        exs = json.load(open(os.path.join(dir_in, fn), "r"))
        verified_exs, execution_diffs, null_exs, timed_out_exs = verify_queries(
            exs
        )

        print(fn)
        print("Total examples:", len(exs))
        print("Verified:", len(verified_exs))
        print("Failed:", len(execution_diffs))
        print("Null:", len(null_exs))
        print("Timed Out:", len(timed_out_exs))

        json.dump(verified_exs, open(os.path.join(dir_out, fn), "w"))
        json.dump(
            execution_diffs, open(os.path.join(dir_out, "failed_" + fn), "w")
        )
        json.dump(null_exs, open(os.path.join(dir_out, "null_" + fn), "w"))
        json.dump(
            timed_out_exs, open(os.path.join(dir_out, "timed_out_" + fn), "w")
        )
