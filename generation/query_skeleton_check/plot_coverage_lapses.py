import json
import argparse
import os
import matplotlib.pyplot as plt
import numpy as np

# base_dir = "satdb_3x_simplified_v7_improved"
# base_dir = "satdb_3x_v6_simplified_v2_improved"
base_dir = "satdb_from_spider_full_3x_simplified_v7_improved"

uncovered_dir = os.path.join(base_dir, "uncovered")

for split in ["test", "dev", "train"]:
    data = json.load(open(os.path.join(uncovered_dir, split + ".json"), "r"))
    num_diffs = [ex["n_diffs"] for ex in data]
    plt.cla()
    plt.hist(num_diffs, bins=max(num_diffs))
    plt.title(f"Number of Differences to Nearest SatDB Example {split}")
    summary_stat_str = f"Total Count: {len(num_diffs)}\nMean Diff: {np.mean(num_diffs):.2f}\nMedian Diff: {np.median(num_diffs)}\nMax Diff: {max(num_diffs)}"
    plt.text(
        0.7 * max(num_diffs), 0.85 * sum([d == 1 for d in num_diffs]), summary_stat_str
    )
    # plt.show()
    plt.savefig(os.path.join(uncovered_dir, split + ".png"))
