# cluster examples based on questions for inspecting coverage lapses

import os
import json
from sentence_transformers import SentenceTransformer
from torch import cdist, float64, nn
import pandas as pd
from random import sample

THRESHOLD = 0.5

model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2", device="mps")
# model = SentenceTransformer(
# "Alibaba-NLP/gte-multilingual-base", trust_remote_code=True, device="mps"
# )
# model = SentenceTransformer(
#     "Alibaba-NLP/gte-Qwen2-1.5B-instruct",
#     trust_remote_code=True,
#     device="mps",
# )

base_dir = "generation/generated_data"

# SPIDER
spider_dir = os.path.join(base_dir, "spider/full_splits/skeletonized_questions")

dir_out = "generation/combined_skeletons/full_v5"
os.makedirs(dir_out, exist_ok=True)

# SATDB
satdb_dir = os.path.join(
    base_dir, "satdb_from_spider_full_v5/qq_few_shot_rephrased/skeletonized_questions"
)
# dir_out = "satdb_from_spider_full_v5/splits_clean/skeletonized_questions"


def combine_questions_for_split(split, spider_dir, satdb_dir, dir_out):
    spider_examples = json.load(open(os.path.join(spider_dir, split), "r"))
    satdb_examples = json.load(open(os.path.join(satdb_dir, split), "r"))
    all_examples = []
    for ex in spider_examples:
        ex["dataset"] = "spider"
        all_examples.append(ex)
    for ex in satdb_examples:
        ex["dataset"] = "satdb"
        all_examples.append(ex)

    json.dump(all_examples, open(os.path.join(dir_out, split), "w"))


def generate_embeddings(examples):
    # TODO: batch this?
    texts = [ex["skeletonized_question"] for ex in examples]
    # try with og question
    # texts = [ex["question"] for ex in examples]
    # print(len(texts))
    # print(texts)
    embeddings = model.encode(texts, convert_to_tensor=True, normalize_embeddings=True)
    # for instruct models
    # embeddings = model.encode(
    #     texts,
    #     convert_to_tensor=True,
    #     # normalize_embeddings=True,
    #     normalize_embeddings=False,
    #     # prompt="Instruct: Given a question about a database, describe the general type of the question while ignoring the specific tables, columns, or values presented. \nQuery: ",
    #     prompt="Instruct: Given a masked question about a database, classify the intent behind the question while ignoring any domain specific verbiage. \nQuery: ",
    #     # precision="float64",
    # )

    # embeddings = model.encode(texts, convert_to_tensor=True, normalize_embeddings=False)
    return embeddings


def compute_distance_matrix(embeddings, cosine_sim=False):
    if cosine_sim:
        print(embeddings.shape)
        # raise ValueError
        cols = embeddings[:, None, :].expand(-1, len(embeddings), -1)
        rows = embeddings[None, :, :].expand(len(embeddings), -1, -1)
        dists = 1 - nn.functional.cosine_similarity(rows, cols, dim=-1)
    else:
        dists = cdist(embeddings, embeddings, p=2)
        # print(dists.shape)
        # print(dists)
        dists.fill_diagonal_(0)
    return dists


def generate_prompt_for_cluster_summary(cluster_examples):
    # TODO: could maybe also use queries or unmasked questions?
    examples = [ex["question"] for ex in cluster_examples]
    # randomly sample up to 20 examples for shorter prompts?
    n_samples = 20
    if len(examples) > n_samples:
        examples = sample(examples, n_samples)
    return f"""Below is a list of masked database style analytical questions. \
Please provide a brief summary of the general type and linguistic style \
describing the given questions. For example, one list of questions could be \
focused on counts of things, while another could focus on things like most or \
least common categories. Please only provide a brief description (one or two \
sentences) that encompass as many of the provided questions as possible but \
make it as specific as possible.
    
    Questions: {examples}"""


# SPLITS = ["dev.json", "test.json", "train.json"]
# SPLITS = ["train.json"]
SPLITS = ["dev.json"]

if __name__ == "__main__":
    # split = "dev.json"
    # split = "dev.json"

    for split in SPLITS:
        # embed questions and prep dm for clustering
        combine_questions_for_split(split, spider_dir, satdb_dir, dir_out)
        examples = json.load(open(os.path.join(dir_out, split), "r"))
        embeddings = generate_embeddings(examples)

        # for gte modles to get clustering to converge
        # embeddings = embeddings.cpu().to(float64)

        print(len(examples))
        print(len(embeddings))
        print(embeddings.shape)
        print(embeddings.dtype)
        dists = compute_distance_matrix(embeddings, cosine_sim=True)
        print(dists.dtype)
        df = pd.DataFrame(dists.cpu().numpy())
        df.to_csv(
            os.path.join(dir_out, f"{split[:-5]}_distance_matrix.csv"),
            index=False,
            header=False,
        )

        # wait for input here to wait until clustering is run
        input(f"Press enter when clustering for split {split} is completed")
        # process clusters
        cluster_idxs = pd.read_csv(os.path.join(dir_out, split[:-5] + "_clusters.csv"))
        cluster_dict = {}
        cluster_idxs = cluster_idxs.to_numpy().reshape(-1).astype(str)
        for ex_idx, cluster in enumerate(cluster_idxs):
            if cluster not in cluster_dict.keys():
                cluster_dict[cluster] = {"examples": [examples[ex_idx]]}
            else:
                cluster_dict[cluster]["examples"].append(examples[ex_idx])

        summary = {}
        undercovered_clusters = []
        overcovered_clusters = []
        prompts = {}
        for k in cluster_dict.keys():
            exs = cluster_dict[k]["examples"]
            spider_exs = 0
            satdb_exs = 0
            for ex in exs:
                if ex["dataset"] == "spider":
                    spider_exs += 1
                else:
                    satdb_exs += 1
            summary[k] = {"satdb_exs": satdb_exs, "spider_exs": spider_exs}
            ratio = satdb_exs / spider_exs if spider_exs else 3
            if ratio < THRESHOLD:
                undercovered_clusters.append((k, ratio))
            elif ratio > (1 / THRESHOLD):
                overcovered_clusters.append((k, ratio))
            prompts[k] = generate_prompt_for_cluster_summary(exs)
            # cluster_dict[k]["summary"] = summary
            print(f"Cluster {k}: satdb: {satdb_exs}, spider: {spider_exs}")

        cluster_dict["summary"] = summary
        cluster_dict["undercovered_clusters"] = undercovered_clusters
        cluster_dict["overcovered_clusters"] = overcovered_clusters
        cluster_dict["summary_prompts"] = prompts
        json.dump(
            cluster_dict,
            open(os.path.join(dir_out, split[:-5] + "_full_clusters.json"), "w"),
        )
