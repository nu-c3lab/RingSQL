import json
import os
import argparse

SQL_KEYWORDS = [
    "IN",
    "DISTINCT",
    "EXCEPT",
    "UNION",
    "INTERSECT",
    "HAVING",
    "NOT",
    "SELECT",
    "FROM",
    "WHERE",
    "JOIN",
    "GROUP BY",
    "ORDER BY",
    "LIMIT",
    "*",
]

SQL_COMPARATORS = [
    ">",
    "=",
    "<",
    ">=",
    "<=",
    "<>",
    "LIKE",
    "BETWEEN",
    "!=",
]

SQL_AGGREGATORS = [
    "count(",
    "avg(",
    "min(",
    "max(",
    "sum(",
]


def has_multi_join(q):
    return q.upper().count(" JOIN ") > 1


def has_order_by(q):
    return " ORDER BY " in q.upper()


def has_group_by(q):
    return " GROUP BY " in q.upper()


def has_join(q):
    return " JOIN " in q.upper()


compound_types = {
    "multiple_joins_with_group_by_and_order_by": lambda q: has_multi_join(q)
    and has_group_by(q)
    and has_order_by(q),
    "multiple_joins_with_group_by": lambda q: has_multi_join(q) and has_group_by(q),
    "multiple_joins_with_order_by": lambda q: has_multi_join(q) and has_order_by(q),
    "multiple_joins": has_multi_join,
    "join_with_group_by_and_order_by": lambda q: has_join(q)
    and has_group_by(q)
    and has_order_by(q),
    "join_with_group_by": lambda q: has_join(q) and has_group_by(q),
    "join_with_order_by": lambda q: has_join(q) and has_order_by(q),
    "join": has_join,
    "group_by_and_order_by": lambda q: has_group_by(q) and has_order_by(q),
    "group_by": has_group_by,
    "order_by": has_order_by,
}

all_keywords = SQL_KEYWORDS + SQL_AGGREGATORS + SQL_COMPARATORS


def count_keywords_for_examples(examples, query_key="query"):
    counts = {keyword: 0 for keyword in all_keywords + list(compound_types.keys())}
    counts["subqueries"] = 0
    if isinstance(examples, dict):
        examples = examples["data"]
    for ex in examples:
        if query_key in ex:
            q = ex[query_key]
        else:
            q = ex["sql"]
        for keyword in all_keywords:
            if keyword == "IN":
                if " IN " in q or " IN(" in q:
                    counts[keyword] += 1
            elif keyword in q or keyword.lower() in q:
                counts[keyword] += 1
        # if q.count("JOIN") > 1:
        #     counts["multiple_joins"] += 1
        # if "GROUP BY" in q.upper() and "ORDER BY" in q.upper():
        #     counts["group_by_and_order_by"] += 1
        if q.upper().count("SELECT") > 1:
            counts["subqueries"] += 1
        # if "JOIN" in q.upper() and "GROUP BY" in q.upper():
        #     counts["join_and_group_by"] += 1
        for e, f in compound_types.items():
            if f(q):
                counts[e] += 1
                break

    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--satdb_data_dir",
        default="generated_data/satdb_from_spider_full_3x_simplified_v7",
    )
    parser.add_argument(
        "--spider_data_dir", default="generated_data/spider/full_splits"
    )
    args = parser.parse_args()
    # sat data only seems to use LEFT OUTER JOINS
    # spider only uses regular JOIN (inner joins not present with sat data?)
    # TODO: add arg parser
    spider_sql_op_count_by_split = {}
    satdb_sql_op_count_by_split = {}

    THRESHOLD = 0.8
    # THRESHOLD = 1.6

    # spider_data_dir = "generated_data/spider/full_splits"
    # satdb_data_dir = "generated_data/satdb_from_spider_small/splits_clean"
    # satdb_data_dir = (
    #     "generated_data/test_v1_benchmark_dataset_from_spider_2025-02-04_18:46:55.385453/"
    # )

    # satdb_data_dir = "generated_data/satdb_from_spider_full_v0_2x/splits_clean"
    # satdb_data_dir = "generated_data/satdb_from_spider_full_v5/splits_raw"
    # satdb_data_dir = "generated_data/satdb_from_spider_full_3x_simplified_v6/splits_raw"
    # satdb_data_dir = "generated_data/satdb_from_spider_full_3x_simplified_v7/splits_raw"

    spider_data_dir = args.spider_data_dir
    satdb_data_dir = os.path.join(args.satdb_data_dir, "splits_clean")

    # out_fn = "generated_data/spider_small_satdb_coverage.json"
    # out_fn = "generated_data/test_v1_benchmark_dataset_from_spider_2025-02-04_18:46:55.385453/spider_small_satdb_coverage.json"
    # out_fn = "generated_data/satdb_from_spider_full_v5/spider_full_satdb_coverage.json"
    # out_fn = "generated_data/satdb_from_spider_full_3x_simplified_v6/spider_full_satdb_coverage.json"
    out_fn = os.path.join(satdb_data_dir, "spider_full_satdb_coverage.json")

    splits = ["dev", "test", "train"]

    for split in splits:
        spider_data = json.load(
            open(os.path.join(spider_data_dir, split + ".json"), "r")
        )
        satdb_data = json.load(open(os.path.join(satdb_data_dir, split + ".json"), "r"))
        spider_sql_op_count_by_split[split] = count_keywords_for_examples(spider_data)
        satdb_sql_op_count_by_split[split] = count_keywords_for_examples(satdb_data)
        # spider_sql_op_count_by_split[split] = {keyword: 0 for keyword in all_keywords}
        # spider_sql_op_count_by_split[split]["multiple_joins"] = 0
        # spider_sql_op_count_by_split[split]["group_by_and_order_by"] = 0
        # spider_sql_op_count_by_split[split]["subqueries"] = 0
        # spider_sql_op_count_by_split[split]["join_and_group_by"] = 0
        # for ex in spider_data:
        #     q = ex["query"]
        #     for keyword in all_keywords:
        #         # handle in differently since its a substring of other keywords
        #         if keyword == "IN":
        #             if " IN " in q or " IN(" in q:
        #                 spider_sql_op_count_by_split[split][keyword] += 1
        #         elif keyword in q:
        #             spider_sql_op_count_by_split[split][keyword] += 1
        #     if q.count("JOIN") > 1:
        #         spider_sql_op_count_by_split[split]["multiple_joins"] += 1
        #     if "GROUP BY" in q and "ORDER BY" in q:
        #         spider_sql_op_count_by_split[split]["group_by_and_order_by"] += 1
        #     if q.count("SELECT") > 1:
        #         spider_sql_op_count_by_split[split]["subqueries"] += 1
        #     if "JOIN" in q.upper() and "GROUP BY" in q.upper():
        #         spider_sql_op_count_by_split[split]["join_and_group_by"] += 1

        # satdb_sql_op_count_by_split[split] = {keyword: 0 for keyword in all_keywords}
        # satdb_sql_op_count_by_split[split]["multiple_joins"] = 0
        # satdb_sql_op_count_by_split[split]["group_by_and_order_by"] = 0
        # satdb_sql_op_count_by_split[split]["subqueries"] = 0
        # satdb_sql_op_count_by_split[split]["join_and_group_by"] = 0
        # if isinstance(satdb_data, dict):
        #     satdb_data = satdb_data["data"]
        # for ex in satdb_data:
        #     if "query" in ex:
        #         q = ex["query"]
        #     else:
        #         q = ex["sql"]
        #     for keyword in all_keywords:
        #         if keyword == "IN":
        #             if " IN " in q or " IN(" in q:
        #                 satdb_sql_op_count_by_split[split][keyword] += 1
        #         elif keyword in q:
        #             satdb_sql_op_count_by_split[split][keyword] += 1
        #     if q.count("JOIN") > 1:
        #         satdb_sql_op_count_by_split[split]["multiple_joins"] += 1
        #     if "GROUP BY" in q and "ORDER BY" in q:
        #         satdb_sql_op_count_by_split[split]["group_by_and_order_by"] += 1
        #     if q.count("SELECT") > 1:
        #         satdb_sql_op_count_by_split[split]["subqueries"] += 1
        #     if "JOIN" in q.upper() and "GROUP BY" in q.upper():
        #         satdb_sql_op_count_by_split[split]["join_and_group_by"] += 1

    diffs = {}
    for split in splits:
        diffs[split] = {
            k: spider_sql_op_count_by_split[split][k]
            - satdb_sql_op_count_by_split[split][k]
            for k in satdb_sql_op_count_by_split[split].keys()
        }

    # print(diffs)
    results = {
        "spider": spider_sql_op_count_by_split,
        "satdb": satdb_sql_op_count_by_split,
        "diffs": diffs,
    }

    missing_from_satdb = {}
    coverage_lapses_in_satdb = {}
    over_covered_in_satdb = {}
    for split in splits:
        missing_from_satdb[split] = []
        coverage_lapses_in_satdb[split] = {}
        over_covered_in_satdb[split] = {}
        for k in spider_sql_op_count_by_split[split].keys():
            if (
                spider_sql_op_count_by_split[split][k] > 0
                and satdb_sql_op_count_by_split[split][k] == 0
            ):
                missing_from_satdb[split].append(k)
            elif spider_sql_op_count_by_split[split][k] and (
                satdb_sql_op_count_by_split[split][k]
                / spider_sql_op_count_by_split[split][k]
                < THRESHOLD
            ):
                coverage_lapses_in_satdb[split][k] = (
                    satdb_sql_op_count_by_split[split][k]
                    / spider_sql_op_count_by_split[split][k]
                )
            elif spider_sql_op_count_by_split[split][k] and (
                spider_sql_op_count_by_split[split][k]
                / satdb_sql_op_count_by_split[split][k]
                < THRESHOLD
            ):
                over_covered_in_satdb[split][k] = (
                    spider_sql_op_count_by_split[split][k]
                    / satdb_sql_op_count_by_split[split][k]
                )
    results = {
        "spider": spider_sql_op_count_by_split,
        "satdb": satdb_sql_op_count_by_split,
        "diffs": diffs,
        "missing_in_satdb": missing_from_satdb,
        "satdb_coverage_lapses": coverage_lapses_in_satdb,
        "satdb_overcovered": over_covered_in_satdb,
    }

    json.dump(results, open(out_fn, "w"))
