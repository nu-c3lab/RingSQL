import json
import sqlglot
from sqlglot import exp
import os


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
        return anonymized.sql(pretty=False, dialect=dialect)
    except Exception as e:
        return f"-- Error parsing SQL: {e}"


# query = """
# SELECT a.name, b.age FROM users AS a
# JOIN logs AS b ON a.id = b.user_id
# WHERE b.timestamp > 2020 AND a.country = 'US'
# """

# # query = "SELECT count(name), count(*) FROM users WHERE age > 30 AND status = 'active'"


# print(skeletonize_sql(query))


# base_dir = "generated_data/spider/full_splits/standardized_v2"
# base_dir = "generated_data/satdb_from_spider_full_3x_simplified_v6/qq_few_shot_rephrased/standardized_v2"
base_dir = "generated_data/satdb_v6_from_bps/splits_clean/standardized_v2"
out_dir = os.path.join(base_dir, "skeletonized_queries")
os.makedirs(out_dir, exist_ok=True)

for split_fn in ["dev.json", "test.json", "train.json"]:
    data = json.load(open(os.path.join(base_dir, split_fn), "r"))
    for ex in data:
        ex["query_skeleton"] = skeletonize_sql(ex["query"])

    json.dump(data, open(os.path.join(out_dir, split_fn), "w"))


# # COMPARE SKELETONS
# def tokenize_skeleton(skeleton):
#     return set(skeleton.lower().replace(",", "").split())


# from datasketch import MinHash, MinHashLSH


# def get_minhash(tokens, num_perm=128):
#     m = MinHash(num_perm=num_perm)
#     for token in tokens:
#         m.update(token.encode("utf8"))
#     return m


# MATCH_THRESHOLD = 0.7
# spider_dir = "generated_data/spider/full_splits/standardized_v2/skeletonized_queries"
# satdb_dir = "generated_data/satdb_from_spider_full_3x_simplified_v6/qq_few_shot_rephrased/standardized_v2/skeletonized_queries"
# out_dir = "query_skeleton_check/satdb_3x_v6_simplified_v2"
# uncovered_out_dir = os.path.join(out_dir, "uncovered")
# covered_out_dir = os.path.join(out_dir, "covered")
# os.makedirs(uncovered_out_dir, exist_ok=True)
# os.makedirs(covered_out_dir, exist_ok=True)

# for split_fn in ["dev.json", "test.json", "train.json"]:
#     spider_data = json.load(open(os.path.join(spider_dir, split_fn), "r"))
#     satdb_data = json.load(open(os.path.join(satdb_dir, split_fn), "r"))

#     # token_lists = df["skeleton"].apply(tokenize_skeleton)
#     # minhashes = token_lists.apply(get_minhash)

#     satdb_hashes = [
#         get_minhash(tokenize_skeleton(ex["query_skeleton"])) for ex in satdb_data
#     ]

#     # Build LSH index
#     lsh = MinHashLSH(threshold=MATCH_THRESHOLD, num_perm=128)

#     for i, m in enumerate(satdb_hashes):
#         # lsh.insert(f"q{i}", m)
#         lsh.insert(i, m)

#     # satdb_skeletons = set([ex["query_skeleton"] for ex in satdb_data])

#     # print(len(satdb_skeletons))
#     covered_exs = []
#     uncovered_exs = []

#     for ex in spider_data:

#         tmp_ex = {k: ex[k] for k in ["db_id", "question", "query", "query_skeleton"]}
#         # Query similar skeletons
#         query_tokens = tokenize_skeleton(ex["query_skeleton"])
#         m_query = get_minhash(query_tokens)
#         similar_ids = lsh.query(m_query)
#         # print(similar_ids)
#         if similar_ids:
#             tmp_ex["most_similar_skeleton"] = satdb_data[similar_ids[0]][
#                 "query_skeleton"
#             ]
#             covered_exs.append(tmp_ex)
#         else:
#             uncovered_exs.append(tmp_ex)

#         # old - exact skeleton match
#         # if ex["query_skeleton"] in satdb_skeletons:
#         #     covered_exs.append(ex)
#         # else:
#         #     uncovered_exs.append(ex)

#     print(split_fn)
#     print(
#         "covered:",
#         len(covered_exs),
#         f"({len(covered_exs) * 100 / len(spider_data) :.2f}%)",
#     )
#     print(
#         "uncovered:",
#         len(uncovered_exs),
#         f"({len(uncovered_exs) * 100/ len(spider_data) :.2f}%)",
#     )

#     json.dump(uncovered_exs, open(os.path.join(uncovered_out_dir, split_fn), "w"))
#     json.dump(covered_exs, open(os.path.join(covered_out_dir, split_fn), "w"))
