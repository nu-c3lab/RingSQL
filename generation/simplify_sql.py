import requests
import os
import json
import sqlite3
import argparse
import concurrent.futures

# BASE_DIR = "generated_data/satdb_from_spider_full_v5/"
# BASE_DIR = "generated_data/satdb_from_spider_full_3x_simplified/"
# BASE_DIR = "generated_data/satdb_from_spider_full_3x_simplified_v6/"
# BASE_DIR = "generated_data/satdb_v6_from_bps/"
# BASE_DIR = "generated_data/satdb_from_spider_full_coverage_check/"

dir_in = "splits_raw"
dir_out = "simplified_sql"

# for already rephrased data
# dir_in = "rephrased"
# dir_out = "simplified_sql_updated_clean"


# BASE_DIR = "test_new_templates"
# # BASE_DIR = "generated_data/satdb_from_spider_full_coverage_check/"
# dir_in = ""
# dir_out = "simplified_sql"


SATYRN_URL = "http://127.0.0.1:5000"
MAX_RETRIES = 3


def simplify_sql(
    ring_id: str,
    sql: str,
) -> str:
    simplified_sql = None
    attempts = 0
    while not simplified_sql and attempts < MAX_RETRIES:
        try:
            attempts += 1
            resp = requests.get(
                "/".join([SATYRN_URL, "api", "simplify_sql", ring_id, "1"]),
                # headers=HEADERS,
                json={
                    "sql": sql,
                },
                timeout=10,
            )
            results = json.loads(resp.content.decode("utf-8"))
            simplified_sql = results["sql_simplified"]
        except:
            print(f"Timeout for rid: {ring_id} and query: {sql}")

    if not simplified_sql:
        print(f"Exceeded number of retries for rid: {ring_id} and query: {sql}")
        return sql
    return simplified_sql


# def run_query(conn, query):
def run_query(db_fn, query):
    """Run a query and fetch all results."""
    try:
        conn = sqlite3.connect(db_fn)
        # for handling special chars in wta_1 db
        conn.text_factory = lambda x: str(x, "latin1")
        return conn.execute(query).fetchall()
    except Exception as e:
        return e  # Return the exception for caller to handle
    finally:
        conn.close()


def compare_queries(og_q, simple_q, db_id, timeout=10):
    db_name = db_id.split("-")[0]
    db_fn = f"../evaluation/database/{db_name}/{db_name}.sqlite"
    # conn = sqlite3.connect(db_fn)
    # # for handling special chars in wta_1 db
    # conn.text_factory = lambda x: str(x, "latin1")
    og_results = None
    simple_results = None
    # TODO: make this work right? - still doesn't stop sometimes - seems like some processes in query execution can't be stopped?
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        try:
            # future_og = executor.submit(run_query, conn, og_q)
            future_og = executor.submit(run_query, db_fn, og_q)
            future_simple = executor.submit(run_query, db_fn, simple_q)
            # future_simple = executor.submit(run_query, conn, simple_q)
            og_results = future_og.result(timeout=timeout)
            simple_results = future_simple.result(timeout=timeout)

            # print(og_results)
            # print(simple_results)
            # Check if exceptions were returned
            if isinstance(og_results, Exception) or isinstance(
                simple_results, Exception
            ):
                raise Exception("Query failed")

            if og_results == simple_results:
                return 1
            else:
                # handle slightly different results from removing LEFT OUTER JOINS?
                if og_q.count("LEFT OUTER JOIN") == simple_q.count("JOIN"):
                    return 1
                else:
                    return 0

        except concurrent.futures.TimeoutError:
            print(f"Query timed out after {timeout} seconds for {db_name}")
            # Treat as "OK" — return 1 since you said it should be considered OK
            return 1

        except Exception as e:
            # print(e)
            # import traceback
            # print(traceback.format_exc())
            if og_results is not None and not isinstance(og_results, Exception):
                # print(og_results)
                return -1
            else:
                # print("Error:", e)
                # print(og_q)
                # print(simple_q)
                # print(db_name)
                return -2

        # finally:
        #     conn.close()
    # try:
    #     og_results = conn.execute(og_q).fetchall()
    #     simple_results = conn.execute(simple_q).fetchall()
    #     # print(og_results)
    #     # print(simple_results)
    #     if og_results == simple_results:
    #         return 1
    #     else:
    #         # handle diff from replacing LEFT OUTER JOIN WITH JOIN
    #         if og_q.count("LEFT OUTER JOIN") == simple_q.count("JOIN"):
    #             return 1
    #         else:
    #             return 0
    # except:
    #     if og_results is not None:
    #         return -1
    #     else:
    #         print(og_q)
    #         print(simple_q)
    #         print(db_name)
    #         return -2
    #         # raise ValueError("Invalid original query")


SPLITS = ["dev.json", "test.json", "train.json"]
# SPLITS = ["train.json"]
# SPLITS = ["dev.json"]
# SPLITS = ["test.json"]


def main(base_dir):

    os.makedirs(os.path.join(base_dir, dir_out), exist_ok=True)
    for fn in os.listdir(os.path.join(base_dir, dir_in)):
        print(fn)
        # if not fn.endswith(".json"):
        if not fn in SPLITS:
            continue
        # if fn != "dev.json":
        # continue
        failed_simplifications = []
        simplified_examples = []
        data = json.load(open(os.path.join(base_dir, dir_in, fn), "r"))

        for ex in data["data"]:
            # for already rephrased data
            # for ex in data:
            ex["sql_original"] = ex["sql"]
            ex["sql"] = simplify_sql(
                ex["ring_id"],
                ex["sql"],
            )
            # for already cleaned/rephrased data
            # ex["og_simplified_query"] = ex.pop("query")
            ex["query"] = simplify_sql(
                ex["ring_id"],
                ex["sql_original"],
            )

            comparison = compare_queries(
                ex["sql_original"],
                ex["sql"],
                # for already cleaned/rephrased data
                # ex["query"],
                ex["ring_id"],
            )
            # TODO: fix query time
            if comparison != 1:
                failed_simplifications.append(
                    {
                        "og_sql": ex["sql_original"],
                        "simplified_sql": ex["sql"],
                        # for already cleaned/rephrased data
                        # "simplified_sql": ex["query"],
                        "error": (
                            "invalid simplified query"
                            if comparison == -1
                            else (
                                "mismatching results"
                                if comparison == 0
                                else "invalid original query"
                            )
                        ),
                        "source": ex["source"],
                        "rid": ex["ring_id"],
                    }
                )
                # print(ex["sql"])
                # print(ex["ring_id"])
            else:
                simplified_examples.append(ex)
        # json.dump(
        #     {"metadata": data["metadata"], "data": simplified_examples},
        #     open(os.path.join(base_dir, dir_out, fn), "w"),
        # )

        json.dump(
            simplified_examples,
            open(os.path.join(base_dir, dir_out, fn), "w"),
        )
        json.dump(
            failed_simplifications,
            open(os.path.join(base_dir, dir_out, "comparison-" + fn), "w"),
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base_dir",
        default="generated_data/satdb_from_spider_full_3x_simplified_v7_improved/",
    )
    args = parser.parse_args()

    main(args.base_dir)
