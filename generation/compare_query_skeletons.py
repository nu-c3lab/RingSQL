import json
import sqlglot
from sqlglot import exp, parse_one
from sqlglot import diff as ast_diff
from sqlglot.diff import Move
import os
from tqdm import tqdm
import argparse


def skeletonize_sql(sql: str, dialect: str = "sqlite") -> str:
    """
    Replace all schema objects (tables, columns, aliases) and
    literals (strings, numbers) with underscores.
    """

    def anonymize(node: exp.Expression) -> exp.Expression:
        # Replace all identifiers (column names, table names, aliases)
        if isinstance(node, (exp.Column, exp.Table, exp.Identifier)):
            # print(node)
            return exp.Identifier(this="_")

        # Replace all literal values
        if isinstance(node, (exp.Literal, exp.Boolean)):
            # print(repr(node))
            return exp.Literal.number("_")

        # Replace function names (preserve structure)
        # if isinstance(node, exp.Func):
        #     print(repr(node))
        #     node.set("this", "_")
        #     return node

        return node

    try:
        tree = sqlglot.parse_one(sql, read=dialect)
        anonymized = tree.transform(anonymize)
        # return anonymized.sql(pretty=False, dialect=dialect)
        return anonymized
    except Exception as e:
        return f"-- Error parsing SQL: {e}"


# q1 = "Select count(_), _ from _ where _ > _ and _ = _"
# q2 = "Select _, count(_) from _ where _ = _ and _ > _"

# ast_1 = skeletonize_sql(q1)
# ast_2 = skeletonize_sql(q2)

# diff = ast_diff(ast_1, ast_2, delta_only=True)
# print(diff)
# print(help(diff[0]))
# print(len([c for c in diff if not isinstance(c, Move)]))


def get_ast_diff(q1, q2, dialect="sqlite"):
    ast_1 = parse_one(q1, dialect=dialect)
    ast_2 = parse_one(q2, dialect=dialect)
    diff = ast_diff(ast_1, ast_2, delta_only=True)
    non_move_diffs = [c for c in diff if not isinstance(c, Move)]
    return diff, non_move_diffs


# q = "SELECT COUNT(*) FROM _"

# print(get_ast_diff(q, q))

# ignore Moves in diff?
# only count Removes and Inserts?

# query = """
# SELECT a.name, b.age FROM users AS a
# JOIN logs AS b ON a.id = b.user_id
# WHERE b.timestamp > 2020 AND a.country = 'US'
# """

# # query = "SELECT count(name), count(*) FROM users WHERE age > 30 AND status = 'active'"


# print(skeletonize_sql(query))


# base_dir = "generated_data/spider/full_splits/standardized_v2"
# base_dir = "generated_data/satdb_from_spider_full_3x_simplified_v6/qq_few_shot_rephrased/standardized_v2"
# out_dir = os.path.join(base_dir, "skeletonized_queries")
# os.makedirs(out_dir, exist_ok=True)

# for split_fn in ["dev.json", "test.json", "train.json"]:
#     data = json.load(open(os.path.join(base_dir, split_fn), "r"))
#     for ex in data:
#         ex["query_skeleton"] = skeletonize_sql(ex["query"])

#     json.dump(data, open(os.path.join(out_dir, split_fn), "w"))


# COMPARE SKELETONS
def tokenize_skeleton(skeleton):
    return set(skeleton.lower().replace(",", "").split())


from datasketch import MinHash, MinHashLSH


def get_minhash(tokens, num_perm=128):
    m = MinHash(num_perm=num_perm)
    for token in tokens:
        m.update(token.encode("utf8"))
    return m


def jaccard_similarity(m1, m2):
    return m1.jaccard(m2)


MATCH_THRESHOLD = 0.1
# original
# spider_dir = "generated_data/spider/full_splits/standardized_v2/skeletonized_queries"
# satdb_dir = "generated_data/satdb_from_spider_full_3x_simplified_v6/qq_few_shot_rephrased/standardized_v2/skeletonized_queries"
# out_dir = "query_skeleton_check/satdb_3x_v6_simplified_v2_improved"


def main(spider_dir, satdb_dir, out_dir):
    # spider_dir = (
    #     "generated_data/spider/full_splits/standardized_v2/skeletonized_queries"
    # )
    # satdb_dir = "generated_data/satdb_from_spider_full_3x_simplified_v7/splits_clean/standardized"
    # out_dir = "query_skeleton_check/satdb_3x_simplified_v7"

    # checking bps for additional coverage
    # spider_dir = "query_skeleton_check/satdb_3x_v6_simplified_v2_improved/uncovered"
    # satdb_dir = (
    #     "generated_data/satdb_v6_from_bps/splits_clean/standardized_v2/skeletonized_queries"
    # )
    # out_dir = "query_skeleton_check/satdb_3x_v6_simplified_v2_improved/uncovered/bp_check"
    uncovered_out_dir = os.path.join(out_dir, "uncovered")
    covered_out_dir = os.path.join(out_dir, "covered")
    os.makedirs(uncovered_out_dir, exist_ok=True)
    os.makedirs(covered_out_dir, exist_ok=True)

    # for split_fn in ["dev.json", "test.json", "train.json"]:
    for split_fn in ["train.json"]:
        spider_data = json.load(open(os.path.join(spider_dir, split_fn), "r"))
        satdb_data = json.load(open(os.path.join(satdb_dir, split_fn), "r"))

        # token_lists = df["skeleton"].apply(tokenize_skeleton)
        # minhashes = token_lists.apply(get_minhash)

        if "query_skeleton" not in spider_data[0].keys():
            for ex in spider_data:
                ex["query_skeleton"] = skeletonize_sql(ex["query"]).sql()
        
        
        if "query_skeleton" not in satdb_data[0].keys():
            for ex in satdb_data:
                ex["query_skeleton"] = skeletonize_sql(ex["query"]).sql()

        satdb_hashes = [
            get_minhash(tokenize_skeleton(ex["query_skeleton"])) for ex in satdb_data
        ]

        # # Build LSH index
        lsh = MinHashLSH(threshold=MATCH_THRESHOLD, num_perm=128)

        for i, m in enumerate(satdb_hashes):
            # lsh.insert(f"q{i}", m)
            lsh.insert(i, m)

        # satdb_skeletons = set([ex["query_skeleton"] for ex in satdb_data])

        # print(len(satdb_skeletons))
        covered_exs = []
        uncovered_exs = []

        for ex in tqdm(spider_data):

            tmp_ex = {
                k: ex[k] for k in ["db_id", "question", "query", "query_skeleton"]
            }
            # Query similar skeletons
            query_tokens = tokenize_skeleton(ex["query_skeleton"])
            m_query = get_minhash(query_tokens)
            similar_ids = lsh.query(m_query)
            # print(len(similar_ids))
            if similar_ids:

                min_diff = 10000000
                most_similar_ex = None
                for tmp_id in sorted(
                    similar_ids,
                    key=lambda key: jaccard_similarity(m_query, satdb_hashes[key]),
                    reverse=True,
                )[:20]:
                    tmp_satdb_ex = satdb_data[tmp_id]
                    diffs, non_move_diffs = get_ast_diff(
                        tmp_ex["query_skeleton"], tmp_satdb_ex["query_skeleton"]
                    )
                    if len(non_move_diffs) < min_diff:
                        min_diff = len(non_move_diffs)
                        most_similar_ex = tmp_satdb_ex

                tmp_ex["most_similar_skeleton"] = most_similar_ex["query_skeleton"]
                if "base_plan" in most_similar_ex:
                    tmp_ex["base_plan"] = most_similar_ex["base_plan"]
                tmp_ex["n_diffs"] = min_diff
                if min_diff == 0:
                    covered_exs.append(tmp_ex)
                else:
                    uncovered_exs.append(tmp_ex)
            else:
                uncovered_exs.append(tmp_ex)

            # old - exact skeleton match
            # if ex["query_skeleton"] in satdb_skeletons:
            #     covered_exs.append(ex)
            # else:
            #     uncovered_exs.append(ex)

        print(split_fn)
        print(
            "covered:",
            len(covered_exs),
            f"({len(covered_exs) * 100 / len(spider_data) :.2f}%)",
        )
        print(
            "uncovered:",
            len(uncovered_exs),
            f"({len(uncovered_exs) * 100/ len(spider_data) :.2f}%)",
        )

        print(
            "avg diffs uncovered:",
            sum([ex["n_diffs"] for ex in uncovered_exs]) / len(uncovered_exs),
        )

        json.dump(
            sorted(uncovered_exs, key=lambda x: x["n_diffs"], reverse=True),
            open(os.path.join(uncovered_out_dir, split_fn), "w"),
        )
        json.dump(covered_exs, open(os.path.join(covered_out_dir, split_fn), "w"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--satdb_dir",
        default="generated_data/satdb_from_spider_full_3x_simplified_v7_improved/standardized",
    )
    parser.add_argument(
        "--output_dir",
        default="query_skeleton_check/satdb_3x_simplified_v7_improved_vs_synsql-5k-no-with",
    )

    parser.add_argument(
        "--spider_dir",
        # default="generated_data/spider/full_splits/standardized_v2/skeletonized_queries",
        default="generated_data/sql-r1/syn-sql-complex-5k/standardized_removing_with",
    )

    args = parser.parse_args()
    main(args.spider_dir, args.satdb_dir, args.output_dir)
