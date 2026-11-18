import json
import matplotlib.pyplot as plt
import pandas as pd
import os

# TODO: fix all this???
# TODO: check coverage - find examples with low sim scores and see if we cover them

base_dir = (
    "../generated_data/satdb_from_spider_full_3x_simplified/question_similarity_check"
)

data_fn = "spider_most_similar_qs.json"
# eval_fn = "satdb_TRAIN_eval_results.json"
eval_fn = "../generated_data/satdb_from_spider_full_coverage_check/satdb_TRAIN_eval_results.json"

out_fn = "spider_unmatched_qs.json"

data = json.load(open(os.path.join(base_dir, data_fn), "r"))
eval_data = json.load(open(eval_fn, "r"))["examples"]


def get_sim_score(ex):
    return ex["satdb_comp"]["similarity"]


def get_eval_score(ex):
    return ex["result_exact_match_score"]


sim_scores = [get_sim_score(ex) for ex in data]
eval_scores = [get_eval_score(ex) for ex in eval_data]


df = pd.DataFrame(zip(sim_scores, eval_scores), columns=["sim_score", "eval_score"])
print(df.describe())
df = df.fillna(-2.0)
colors = {
    1.0: "green",
    -1.0: "red",
    0.0: "red",
    -2.0: "red",
}

grouped = df.groupby("eval_score")
# grouped["sim_score"].hist()

fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(8, 8))

# Flatten the axes array (makes it easier to iterate over)
axes = axes.flatten()
plt.subplots_adjust(wspace=0.4, hspace=0.4)

for i, (name, group) in enumerate(grouped):
    # plt.figure()
    group["sim_score"].hist(ax=axes[i], bins=100)
    axes[i].set_title(f"Eval Score: {name}")
    axes[i].set_xlabel("cosine similarity")
    axes[i].set_ylabel("count")

# print(list(df["eval_score"].unique()))

# plt.hist(df["sim_score"], bins=1000, color=df["eval_score"].apply(lambda x: colors[x]))
# df["sim_score"].plot(
#     kind="hist",
#     # label=list(df["eval_score"].unique()),
# )
# plt.legend(list(df["eval_score"].unique()))
plt.show()

low_bound = 0.7

mismatched_examples = []
for ex, sim_score, eval_score in zip(data, sim_scores, eval_scores):
    if sim_score <= low_bound:
        ex["result_exact_match_score"] = eval_score
        mismatched_examples.append(ex)

mismatched_examples = list(sorted(mismatched_examples, key=get_sim_score))
json.dump(mismatched_examples, open(os.path.join(base_dir, out_fn), "w"))
