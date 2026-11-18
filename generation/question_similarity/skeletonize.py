import json
import re
import os

base_dir = (
    "../generated_data/satdb_from_spider_full_3x_simplified/question_similarity_check"
)

fns = ["spider_train.json", "all_satdb_train.json"]

mask = "<mask>"


def mask_question(ex):
    q = ex["question"].lower()
    sql = ex["query"]

    string_vals = re.findall(
        r"((?:(?:\")[^\"]+(?:\"))|(?:(?:\')[^\']+(?:\')))",
        # r"((?:\')[^\']+(?:\'))",
        sql,
    )
    # TODO: may need some better handling for this
    for v in string_vals:
        # skip single chars? - may want to do this better
        if len(v.strip("%'\" ")) > 1:
            q = q.replace(v.lower().replace("%", ""), mask)
            q = q.replace(v.lower().strip("%\"'"), mask)

    # remove numbers from question
    q = re.subn(
        # r"[0-9]+(?:[,.][0-9]+)?",
        # r"(\d*\.?\d+|\d{1,3}(,\d{3})*(\.\d+)?)",
        r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b|\b\d+(?:\.\d+)?\b",
        mask,
        q,
    )[0]

    return re.subn(r"(?:<mask>[\s]*)+", mask + " ", q)[0]


for fn in fns:
    masked_exs = []
    data = json.load(open(os.path.join(base_dir, fn), "r"))
    for ex in data:
        tmp_ex = {k: ex[k] for k in ["db_id", "question", "query"]}
        tmp_ex["masked_question"] = mask_question(tmp_ex)
        masked_exs.append(tmp_ex)
    json.dump(masked_exs, open(os.path.join(base_dir, "masked_" + fn), "w"))
