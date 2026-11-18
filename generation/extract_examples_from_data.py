import os
import json
import argparse

# combines data from all files in a split into one file per split


def extract_examples_from_file(fn):
    data = json.loads(open(fn, "r").read())
    examples = []
    for ex in data["data"]:
        sqr = ex["compiled_plan"]
        bp = ex["base_plan"]
        db_id = ex["ring_id"]
        query = ex["sql"]
        if not query:
            continue
        for q in ex["questions"]:
            examples.append(
                {
                    "question": q,
                    "db_id": db_id,
                    "query": query,
                    "sqr": sqr,
                }
            )
    return examples


def extract_examples_for_split(split_name, data_dir, out_dir):
    examples = []
    for fn in os.listdir(os.path.join(data_dir, split_name)):
        if fn.endswith(".json"):
            examples.extend(
                extract_examples_from_file(os.path.join(data_dir, split_name, fn))
            )
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    out_f = open(os.path.join(out_dir, f"{split}.json"), "w")
    out_f.write(json.dumps(examples))
    out_f.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset_dir", type=str)
    parser.add_argument("--output_dir", type=str)

    args = parser.parse_args()

    # assumes dataset_dir contains folders for each split of the dataset
    for split in os.listdir(args.dataset_dir):
        if not split.startswith("."):
            extract_examples_for_split(
                split,
                args.dataset_dir,
                args.output_dir,
            )
