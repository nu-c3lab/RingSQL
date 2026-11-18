import os
import json
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from spellchecker import SpellChecker
import re

# use this first time
# nltk.download("punkt")
# nltk.download("wordnet")
# nltk.download("averaged_perceptron_tagger_eng")
# nltk.download("universal_tagset")

mask = "<mask>"

lemmatizer = WordNetLemmatizer()
spell = SpellChecker()


def lemmatize_with_typo_handling(text):
    words = word_tokenize(text)
    corrected_words = [spell.correction(word) or word for word in words]
    lemmatized_words = [lemmatizer.lemmatize(word) for word in corrected_words]
    return " ".join(lemmatized_words)


def get_db_dict(tables_data, lemmatize=True):
    # TODO: maybe include originals??
    d = {
        t["db_id"]: sorted(
            (
                lemmatize_with_typo_handling(
                    " ".join(
                        t["table_names"] + list(map(lambda x: x[1], t["column_names"]))
                    ),
                ).split(" ")
                if lemmatize
                else t["table_names"] + list(map(lambda x: x[1], t["column_names"]))
            ),
            key=lambda s: len(s),
            reverse=True,
        )
        for t in tables_data
    }

    return d


def simplify_masks(q):
    return re.subn(r"(?:<mask>[\s]*)+", mask + " ", q)[0]


# TODO: handle synonyms? maybe use nltk
def skeletonize_question(ex, tables):
    # print(ex["db_id"])
    # TODO: remove db values
    schema_items = tables[ex["db_id"]]
    q = lemmatize_with_typo_handling(ex["question"].lower())

    # remove lemmatized schema items form question
    for s in schema_items:
        q = q.replace(s + "s", mask)
        q = q.replace(s, mask)

    # replace string vals used in query from question - may cause issues for sinlge chars?
    sql = ex["query"]
    string_vals = re.findall(r"((?:(?:\")[^\"]+(?:\"))|(?:(?:\')[^\']+(?:\')))", sql)
    # print(string_vals)
    for v in string_vals:
        q = q.replace(" " + v.lower().replace("%", ""), " " + mask)
        q = q.replace(" " + v.lower().strip("%\"'"), " " + mask)

    # remove numbers from question
    q = re.subn(r"[0-9]+", mask, q)[0]

    # TODO: combine multiple _s

    return simplify_masks(q)


masked_pos = set(["ADJ", "NOUN", "NUM", "PROPN", "SYM"])
unmaskables = set(
    [
        "many",
        "list",
        "most",
        "least",
        "different",
        "distinct",
        "unique",
        "information",
        "more",
        "less",
        "number",
        "count",
        "amount",
    ]
)


def skeletonize_question_pos(ex, tables):
    # print(ex["db_id"])
    # TODO: remove db values
    schema_items = tables[ex["db_id"]]
    # q = lemmatize_with_typo_handling(ex["question"].lower())
    q = ex["question"].lower()

    tagged_toks = pos_tag(word_tokenize(q), tagset="universal")
    # TODO: may need better way of combining toks
    q = " ".join(
        [
            tok if pos not in masked_pos or tok in unmaskables else mask
            for tok, pos in tagged_toks
        ]
    )

    # remove lemmatized schema items form question
    # for s in schema_items:
    #     q = q.replace(s + "s", mask)
    #     q = q.replace(s, mask)

    # replace string vals used in query from question - may cause issues for sinlge chars?
    # sql = ex["query"]
    # string_vals = re.findall(r"((?:(?:\")[^\"]+(?:\"))|(?:(?:\')[^\']+(?:\')))", sql)
    # print(string_vals)
    # for v in string_vals:
    # q = q.replace(" " + v.replace("%", ""), " " + mask)
    # q = q.replace(" " + v.strip("%\"'"), " " + mask)

    # remove numbers from question
    q = re.subn(r"[0-9]+", mask, q)[0]

    # TODO: combine multiple _s

    return simplify_masks(q)


base_dir = "generation/generated_data"

# SPIDER
# dir_in = "spider/full_splits"
# dir_out = "spider/full_splits/skeletonized_questions"

# SATDB
# dir_in = "satdb_from_spider_full_v5/splits_clean"
# dir_out = "satdb_from_spider_full_v5/splits_clean/skeletonized_questions"


tables_path = "spider/full_splits/tables.json"

SPLITS = ["test.json", "dev.json", "train.json"]
# SPLITS = ["dev.json"]


if __name__ == "__main__":
    tables_info = json.load(open(os.path.join(base_dir, tables_path), "r"))
    schemas_by_db = get_db_dict(
        tables_info,
        # for pos masking
        lemmatize=False,
    )
    # print(sorted(schemas_by_db.keys()))
    for dir_in, dir_out in [
        ("spider/full_splits", "spider/full_splits/skeletonized_questions"),
        (
            "satdb_from_spider_full_v5/qq_few_shot_rephrased",
            "satdb_from_spider_full_v5/qq_few_shot_rephrased/skeletonized_questions",
        ),
    ]:
        os.makedirs(os.path.join(base_dir, dir_out), exist_ok=True)
        for split in SPLITS:
            print(split)
            data = json.load(open(os.path.join(base_dir, dir_in, split), "r"))
            # TODO: skeletonize questions
            skeletonized_data = []
            for ex in data:
                # ex["skeletonized_question"] = skeletonize_question(ex, schemas_by_db)
                ex["skeletonized_question"] = skeletonize_question_pos(
                    ex, schemas_by_db
                )
                skeletonized_data.append(
                    {
                        k: ex[k]
                        for k in ["db_id", "query", "question", "skeletonized_question"]
                    }
                )

            json.dump(
                skeletonized_data, open(os.path.join(base_dir, dir_out, split), "w")
            )
