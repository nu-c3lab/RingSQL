import json
import requests
import os
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# USE FORN REPHRASING CLEANED DATA

URL = "http://127.0.0.1:5000/api/rephrase_question/"

# prompt_type = "question_only"
# prompt_type = "question_cot"
# prompt_type = "question_query_cot"
# prompt_type = "question_query_data_cot"

query_key = "query"
# query_key = "sql_original_aliases"

# data_fn = "generated_data/full_plans_test/NFLSampleForRephrasing.json"
# out_fn = f"generated_data/full_plans_test/rephrased/{prompt_type}_{query_key}.json"


SPLITS = ["dev.json", "test.json", "train.json"]
# SPLITS = ["dev.json", "train.json"]
# SPLITS = ["dev.json"]
# SPLITS = ["test.json", "train.json"]
# SPLITS = ["test.json"]
# SPLITS = ["train.json"]
# SPLITS = ["augmenting_train_data.json"]
# SPLITS = ["dev.json", "train.json"]


def rephrase_example(ex, split, prompt_type):
    # for normal
    question = ex["question"]
    # for issues with timeouts on rephrasing
    # question = ex["og_question"]
    ex["og_question"] = question
    query = ex[query_key]
    ring_id = ex["ring_id"]
    # call rephraser
    db_id = ex["db_id"]
    res = requests.post(
        URL,
        json={
            "prompt_type": prompt_type,
            # "ring_id": ring_id,
            "question": question,
            "query": query,
            "split": split,
            "db_id": db_id,
            "ring_id": ring_id,
        },
    )
    # print(res.content)
    # print(res.json())
    try:
        ex["question"] = res.json()["rephrased_question"]
    except:
        ex["question"] = ""
    logging.info(f"EXAMPLE: {json.dumps(ex)}")
    return ex


def rephrase_dataset_questions(args):
    for fn in os.listdir(args.dir_in):
        # if fn.endswith(".json") and fn != "tables.json":
        if fn in SPLITS:
            split = fn[:-5]
            in_fn = os.path.join(args.dir_in, fn)
            logging.info(f"FILE: {fn}")
            examples = json.load(open(in_fn, "r"))
            # for 3x rephrasing on added spider data
            # examples = sum([[item] * 3 for item in examples], [])
            # for testing a few examples
            # examples = json.load(open(in_fn, "r"))[:5]

            # for issues with timeouts on rephrasing
            # rephrased_examples = [ex for ex in examples if ex["question"] != ""]
            # for normal
            rephrased_examples = []

            with ThreadPoolExecutor(max_workers=20) as executor:

                future_to_example = {
                    executor.submit(
                        rephrase_example, ex, split, args.prompt_type
                    ): ex
                    # executor.submit(rephrase_example, ex, "train", args.prompt_type): ex
                    # for issues with tiemouts on rephrasing
                    # for ex in examples
                    # if ex["question"] == ""
                    # for normal
                    for ex in examples
                }
                for future in as_completed(future_to_example):
                    rephrased_ex = future.result()
                    rephrased_examples.append(rephrased_ex)
            # for ex in examples[:1]:
            # for ex in examples:
            #     # question = ex["question"]
            #     # query = ex[query_key]
            #     # ring_id = ex["db_id"]
            #     # # call rephraser
            #     # res = requests.post(
            #     #     URL,
            #     #     json={
            #     #         "prompt_type": args.prompt_type,
            #     #         "ring_id": ring_id,
            #     #         "question": question,
            #     #         "query": query,
            #     #     },
            #     # )
            #     # # print(res.content)
            #     # # print(res.json())
            #     # ex["question"] = res.json()["rephrased_question"]
            #     ex = rephrase_example(ex)
            #     # ex["original_question"] = question
            #     rephrased_examples.append(ex)
            #     # log each repohrased example to reduce cost in event of internet outage

            out_fn = os.path.join(args.dir_out, fn)
            json.dump(rephrased_examples, open(out_fn, "w"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir_in", type=str)
    parser.add_argument("--dir_out", type=str)
    parser.add_argument(
        "--prompt_type",
        type=str,
        default="question_query_cot_few_shot_with_db_summary",
    )

    args = parser.parse_args()
    os.makedirs(args.dir_out, exist_ok=True)
    # set up loggging in case of internet loss
    logging.basicConfig(
        level=logging.INFO,
        filename=os.path.join(args.dir_out, "rephrasing_log.txt"),
    )
    rephrase_dataset_questions(args)
