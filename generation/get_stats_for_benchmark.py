import os
import json
import argparse
from typing import Dict, List
from collections import defaultdict

def get_json_files(directory: str):
    # List all files in the directory
    files = os.listdir(directory)

    # Filter the list to include only .json files
    json_files = [f for f in files if f.endswith('.json')]

    return json_files

def get_stats_for_split(split_directory: str) -> Dict:
    json_files = get_json_files(split_directory)

    stats = defaultdict(int)
    base_plan_stats = defaultdict(int)
    for j in json_files:
        file_path = os.path.join(split_directory, j)
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
            # Get the stats relating to the base plan generations
            for bp_type, count in data['metadata']['base_plan_distribution'].items():
                base_plan_stats[bp_type] += count

            # Get all the other stats
            keys = ['total_questions', 'total_generated_sqr', 'total_compiled_sqr', 'total_sql']
            for k in keys:
                stats[k] += data['metadata'][k]

    # Create the final dict
    stats["base_plan_distribution"] = base_plan_stats
    return stats

def get_cumulative_stats(stat_dicts: List[Dict]) -> Dict:

    stats = defaultdict(int)
    base_plan_stats = defaultdict(int)
    for d in stat_dicts:
        # Get the stats relating to the base plan generations
        for bp_type, count in d['base_plan_distribution'].items():
            base_plan_stats[bp_type] += count

        # Get all the other stats
        keys = ['total_questions', 'total_generated_sqr', 'total_compiled_sqr', 'total_sql']
        for k in keys:
            stats[k] += d[k]

    # Create the final dict
    stats["base_plan_distribution"] = base_plan_stats
    return stats

def main(benchmark_directory: str):

    INPUT_DIRS = {
        "train": os.path.join(benchmark_directory, "train"),
        "dev": os.path.join(benchmark_directory, "dev"),
        "test": os.path.join(benchmark_directory, "test")
    }

    train_stats = get_stats_for_split(INPUT_DIRS['train'])
    dev_stats = get_stats_for_split(INPUT_DIRS['dev'])
    test_stats = get_stats_for_split(INPUT_DIRS['test'])
    cumulative_stats = get_cumulative_stats([train_stats, dev_stats, test_stats])

    all_stats = {
        "full_dataset_stats": cumulative_stats,
        "train_stats": train_stats,
        "dev_stats": dev_stats,
        "test_stats": test_stats
    }

    # Save the JSON with the cumulative metadata / dataset statistics
    output_path = os.path.join(benchmark_directory, "dataset_statistics.json")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(all_stats, indent=4))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("benchmark_directory", type=str)

    args = parser.parse_args()

    main(args.benchmark_directory)
