# for adding "query" key to each example generated with satyrn
# and removing unwanted metadata

import argparse
import json
import os
import random
import re


def cast_to_julian_day(q):
    p = re.compile(r"select ([^\s]+) - ([^\s]+) ", re.IGNORECASE)
    match = re.findall(p, q)[0]

    subst = f"select julianday({match[0]}) - julianday({match[1]}) "
    return re.subn(p, subst, q, count=1)[0]

SPLITS = ["train.json", "dev.json", "test.json"]

# SAMPLE_QUESTIONS = False
# SAMPLE_QUESTIONS = True
# TODO: sample one question per plan and save to one file, save rest to another file
# to avoid duplicated rephrasing


def clean_satdb_data(args):
    os.makedirs(args.output_dir, exist_ok=True)
    for fn in os.listdir(args.input_dir):
        # if fn.endswith(".json"):
        if fn in SPLITS:
            in_fn = os.path.join(args.input_dir, fn)
            data = json.load(open(in_fn, "r"))
            # data = data["data"]
            clean_data = []
            extra_data = []
            for ex in data:
                if "query" not in ex:
                    ex["query"] = ex.pop("sql")
                if "ring_id" in ex:
                    # ex["db_id"] = ex.pop("ring_id")
                    # for compatibility with spider's table.json
                    ex["db_id"] = ex["ring_id"].split("-")[0]
                
                # convert TimeElapsed plans to calculate day difference for sqlite
                if ex.get("base_plan", "") == "TimeElapsed":
                    ex["query"] = cast_to_julian_day(ex["query"])

                if "question" not in ex:
                    all_qs = ex.pop("questions")
                    sampled_q = all_qs.pop(random.randint(0, len(all_qs) - 1))
                    ex["question"] = sampled_q
                    clean_data.append(ex.copy())
                    for q in all_qs:
                        ex["question"] = q
                        extra_data.append(ex.copy())
                else:
                    clean_data.append(ex)
                # if SAMPLE_QUESTIONS:
                #     if "question" not in ex:
                #         ex["question"] = random.choice(ex.pop("questions"))
                #     clean_data.append(ex)
                # else:
                #     # expand to use all questions for each query
                #     # for now should double datasewt size
                #     for q in ex.pop["questions"]:
                #         ex["question"] = q
                #         clean_data.append(ex)

            out_fn = os.path.join(args.output_dir, fn)
            json.dump(clean_data, open(out_fn, "w"))
            if extra_data:
                extra_out_dir = args.output_dir.rstrip("/") + "_extra"
                os.makedirs(extra_out_dir, exist_ok=True)
                extra_out_fn = os.path.join(extra_out_dir, fn)
                json.dump(extra_data, open(extra_out_fn, "w"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", type=str)
    parser.add_argument("--output_dir", type=str)

    args = parser.parse_args()
    clean_satdb_data(args)
