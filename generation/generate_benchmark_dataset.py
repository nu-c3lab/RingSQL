import os
import argparse
import datetime
from typing import Dict

from generate_training_data import generate_data

################################################################################
#                                   TODO List
#
# - TODO: Add flags for which splits to generate
# - TODO: Determine if we can use just one config per ring by combining the entities lists
#
################################################################################

GENERATION_ROOT_DIR = ""

GLOBAL_PLANS_PER_BASE_PLAN = 20
GLOBAL_NUM_RETRIEVAL_PLANS = 100
GLOBAL_PLANS_PER_ACCESS_PLAN = 10
GLOBAL_NUM_GROUPING_PLANS = 100
GLOBAL_FILTER_PROPORTION = 0.95

CONFIGS = [
    # =============================================
    # TRAINING SET RINGS
    #
    # - SCALES
    # - Illinois Report Card (Education)
    # - Wildfire
    # - Used Cars
    # - Zillow
    # - Stocks
    # - Illinois Poverty and Labor Statistics (income_disparity)
    #
    # =============================================
    {
        "ring_id": "SCALES-1467-4a02-8785-ec251e78d5be",
        "entities": ["Case"],
        "num_plans_per_base_plan_per_entity": GLOBAL_PLANS_PER_BASE_PLAN,
        "num_retrieval_plans_per_entity": GLOBAL_NUM_RETRIEVAL_PLANS,
        "num_grouping_plans_per_entity": GLOBAL_NUM_GROUPING_PLANS,
        "num_access_plans_per_attribute": GLOBAL_PLANS_PER_ACCESS_PLAN,
        "filter_proportion": GLOBAL_FILTER_PROPORTION,
        "split": "train"
    },
    {
        "ring_id": "SCALES-1467-4a02-8785-ec251e78d5be",
        "entities": ["Judge"],
        "num_plans_per_base_plan_per_entity": GLOBAL_PLANS_PER_BASE_PLAN,
        "num_retrieval_plans_per_entity": GLOBAL_NUM_RETRIEVAL_PLANS,
        "num_grouping_plans_per_entity": GLOBAL_NUM_GROUPING_PLANS,
        "num_access_plans_per_attribute": GLOBAL_PLANS_PER_ACCESS_PLAN,
        "filter_proportion": GLOBAL_FILTER_PROPORTION,
        "split": "train"
    },
    {
        "ring_id": "education-1467-4a02-8785-ec251e78d5be",
        "entities": ["School"],
        "num_plans_per_base_plan_per_entity": GLOBAL_PLANS_PER_BASE_PLAN,
        "num_retrieval_plans_per_entity": GLOBAL_NUM_RETRIEVAL_PLANS,
        "num_grouping_plans_per_entity": GLOBAL_NUM_GROUPING_PLANS,
        "num_access_plans_per_attribute": GLOBAL_PLANS_PER_ACCESS_PLAN,
        "filter_proportion": GLOBAL_FILTER_PROPORTION,
        "split": "train"
    },
    {
        "ring_id": "education-1467-4a02-8785-ec251e78d5be",
        "entities": ["District"],
        "num_plans_per_base_plan_per_entity": GLOBAL_PLANS_PER_BASE_PLAN,
        "num_retrieval_plans_per_entity": GLOBAL_NUM_RETRIEVAL_PLANS,
        "num_grouping_plans_per_entity": GLOBAL_NUM_GROUPING_PLANS,
        "num_access_plans_per_attribute": GLOBAL_PLANS_PER_ACCESS_PLAN,
        "filter_proportion": GLOBAL_FILTER_PROPORTION,
        "split": "train"
    },
    {
        "ring_id": "CarPricing-1467-7b152-1275-ec251e78d5be",
        "entities": ["UsedCar"],
        "num_plans_per_base_plan_per_entity": GLOBAL_PLANS_PER_BASE_PLAN,
        "num_retrieval_plans_per_entity": GLOBAL_NUM_RETRIEVAL_PLANS,
        "num_grouping_plans_per_entity": GLOBAL_NUM_GROUPING_PLANS,
        "num_access_plans_per_attribute": GLOBAL_PLANS_PER_ACCESS_PLAN,
        "filter_proportion": GLOBAL_FILTER_PROPORTION,
        "split": "train"
    },
    {
        "ring_id": "Toxic-3418-r4hu-4289-38jd93k29s",
        "entities": ["State"],
        "num_plans_per_base_plan_per_entity": GLOBAL_PLANS_PER_BASE_PLAN,
        "num_retrieval_plans_per_entity": GLOBAL_NUM_RETRIEVAL_PLANS,
        "num_grouping_plans_per_entity": GLOBAL_NUM_GROUPING_PLANS,
        "num_access_plans_per_attribute": GLOBAL_PLANS_PER_ACCESS_PLAN,
        "filter_proportion": GLOBAL_FILTER_PROPORTION,
        "split": "train"
    },
    {
        "ring_id": "Toxic-3418-r4hu-4289-38jd93k29s",
        "entities": ["Wildfire"],
        "num_plans_per_base_plan_per_entity": GLOBAL_PLANS_PER_BASE_PLAN,
        "num_retrieval_plans_per_entity": GLOBAL_NUM_RETRIEVAL_PLANS,
        "num_grouping_plans_per_entity": GLOBAL_NUM_GROUPING_PLANS,
        "num_access_plans_per_attribute": GLOBAL_PLANS_PER_ACCESS_PLAN,
        "filter_proportion": GLOBAL_FILTER_PROPORTION,
        "split": "train"
    },
    {
        "ring_id": "Zillow8-1467-4a02-8785-ec251e78d5be",
        "entities": ["Region"],
        "num_plans_per_base_plan_per_entity": GLOBAL_PLANS_PER_BASE_PLAN,
        "num_retrieval_plans_per_entity": GLOBAL_NUM_RETRIEVAL_PLANS,
        "num_grouping_plans_per_entity": GLOBAL_NUM_GROUPING_PLANS,
        "num_access_plans_per_attribute": GLOBAL_PLANS_PER_ACCESS_PLAN,
        "filter_proportion": GLOBAL_FILTER_PROPORTION,
        "split": "train"
    },
    {
        "ring_id": "Zillow8-1467-4a02-8785-ec251e78d5be",
        "entities": ["RentRate"],
        "num_plans_per_base_plan_per_entity": GLOBAL_PLANS_PER_BASE_PLAN,
        "num_retrieval_plans_per_entity": GLOBAL_NUM_RETRIEVAL_PLANS,
        "num_grouping_plans_per_entity": GLOBAL_NUM_GROUPING_PLANS,
        "num_access_plans_per_attribute": GLOBAL_PLANS_PER_ACCESS_PLAN,
        "filter_proportion": GLOBAL_FILTER_PROPORTION,
        "split": "train"
    },
    {
        "ring_id": "Stocks-fe5b7728-b527-4817-b407-d33a679ff218",
        "entities": ["Security"],
        "num_plans_per_base_plan_per_entity": GLOBAL_PLANS_PER_BASE_PLAN,
        "num_retrieval_plans_per_entity": GLOBAL_NUM_RETRIEVAL_PLANS,
        "num_grouping_plans_per_entity": GLOBAL_NUM_GROUPING_PLANS,
        "num_access_plans_per_attribute": GLOBAL_PLANS_PER_ACCESS_PLAN,
        "filter_proportion": GLOBAL_FILTER_PROPORTION,
        "split": "train"
    },
    {
        "ring_id": "Stocks-fe5b7728-b527-4817-b407-d33a679ff218",
        "entities": ["SecurityRecord"],
        "num_plans_per_base_plan_per_entity": GLOBAL_PLANS_PER_BASE_PLAN,
        "num_retrieval_plans_per_entity": GLOBAL_NUM_RETRIEVAL_PLANS,
        "num_grouping_plans_per_entity": GLOBAL_NUM_GROUPING_PLANS,
        "num_access_plans_per_attribute": GLOBAL_PLANS_PER_ACCESS_PLAN,
        "filter_proportion": GLOBAL_FILTER_PROPORTION,
        "split": "train"
    },
    {
        "ring_id": "money-1467-4a02-8785-ec251e78d5be",
        "entities": ["County"],
        "num_plans_per_base_plan_per_entity": GLOBAL_PLANS_PER_BASE_PLAN,
        "num_retrieval_plans_per_entity": GLOBAL_NUM_RETRIEVAL_PLANS,
        "num_grouping_plans_per_entity": GLOBAL_NUM_GROUPING_PLANS,
        "num_access_plans_per_attribute": GLOBAL_PLANS_PER_ACCESS_PLAN,
        "filter_proportion": GLOBAL_FILTER_PROPORTION,
        "split": "train"
    },
    {
        "ring_id": "money-1467-4a02-8785-ec251e78d5be",
        "entities": ["IncomeRecord"],
        "num_plans_per_base_plan_per_entity": GLOBAL_PLANS_PER_BASE_PLAN,
        "num_retrieval_plans_per_entity": GLOBAL_NUM_RETRIEVAL_PLANS,
        "num_grouping_plans_per_entity": GLOBAL_NUM_GROUPING_PLANS,
        "num_access_plans_per_attribute": GLOBAL_PLANS_PER_ACCESS_PLAN,
        "filter_proportion": GLOBAL_FILTER_PROPORTION,
        "split": "train"
    },

    # =============================================
    # DEV SET RINGS
    #
    # - MIMIC
    # - Exonerations
    # - Missing Migrants
    #
    # =============================================

    {
        "ring_id": "mimic9f2-1467-4a02-8785-ec251e78d5be",
        "entities": ["Subject"],
        "num_plans_per_base_plan_per_entity": GLOBAL_PLANS_PER_BASE_PLAN,
        "num_retrieval_plans_per_entity": GLOBAL_NUM_RETRIEVAL_PLANS,
        "num_grouping_plans_per_entity": GLOBAL_NUM_GROUPING_PLANS,
        "num_access_plans_per_attribute": GLOBAL_PLANS_PER_ACCESS_PLAN,
        "filter_proportion": GLOBAL_FILTER_PROPORTION,
        "split": "dev"
    },
    {
        "ring_id": "mimic9f2-1467-4a02-8785-ec251e78d5be",
        "entities": ["EDstay"],
        "num_plans_per_base_plan_per_entity": GLOBAL_PLANS_PER_BASE_PLAN,
        "num_retrieval_plans_per_entity": GLOBAL_NUM_RETRIEVAL_PLANS,
        "num_grouping_plans_per_entity": GLOBAL_NUM_GROUPING_PLANS,
        "num_access_plans_per_attribute": GLOBAL_PLANS_PER_ACCESS_PLAN,
        "filter_proportion": GLOBAL_FILTER_PROPORTION,
        "split": "dev"
    },
    {
        "ring_id": "Exonerations12-5732-8b01-9634-fa492d67c8af",
        "entities": ["State"],
        "num_plans_per_base_plan_per_entity": GLOBAL_PLANS_PER_BASE_PLAN,
        "num_retrieval_plans_per_entity": GLOBAL_NUM_RETRIEVAL_PLANS,
        "num_grouping_plans_per_entity": GLOBAL_NUM_GROUPING_PLANS,
        "num_access_plans_per_attribute": GLOBAL_PLANS_PER_ACCESS_PLAN,
        "filter_proportion": GLOBAL_FILTER_PROPORTION,
        "split": "dev"
    },
    {
        "ring_id": "Exonerations12-5732-8b01-9634-fa492d67c8af",
        "entities": ["Exoneration"],
        "num_plans_per_base_plan_per_entity": GLOBAL_PLANS_PER_BASE_PLAN,
        "num_retrieval_plans_per_entity": GLOBAL_NUM_RETRIEVAL_PLANS,
        "num_grouping_plans_per_entity": GLOBAL_NUM_GROUPING_PLANS,
        "num_access_plans_per_attribute": GLOBAL_PLANS_PER_ACCESS_PLAN,
        "filter_proportion": GLOBAL_FILTER_PROPORTION,
        "split": "dev"
    },
    {
        "ring_id": "MissingMigrantsData",
        "entities": ["Country"],
        "num_plans_per_base_plan_per_entity": GLOBAL_PLANS_PER_BASE_PLAN,
        "num_retrieval_plans_per_entity": GLOBAL_NUM_RETRIEVAL_PLANS,
        "num_grouping_plans_per_entity": GLOBAL_NUM_GROUPING_PLANS,
        "num_access_plans_per_attribute": GLOBAL_PLANS_PER_ACCESS_PLAN,
        "filter_proportion": GLOBAL_FILTER_PROPORTION,
        "split": "dev"
    },
    {
        "ring_id": "MissingMigrantsData",
        "entities": ["Event"],
        "num_plans_per_base_plan_per_entity": GLOBAL_PLANS_PER_BASE_PLAN,
        "num_retrieval_plans_per_entity": GLOBAL_NUM_RETRIEVAL_PLANS,
        "num_grouping_plans_per_entity": GLOBAL_NUM_GROUPING_PLANS,
        "num_access_plans_per_attribute": GLOBAL_PLANS_PER_ACCESS_PLAN,
        "filter_proportion": GLOBAL_FILTER_PROPORTION,
        "split": "dev"
    },

    # =============================================
    # TEST SET RINGS
    #
    # - Yelp
    # - School Shootings
    # - Crop Yields
    #
    # =============================================
    {
        "ring_id": "dcac39f2-1467-4a02-8785-ec251e78d5be",
        "entities": ["Business"],
        "num_plans_per_base_plan_per_entity": GLOBAL_PLANS_PER_BASE_PLAN,
        "num_retrieval_plans_per_entity": GLOBAL_NUM_RETRIEVAL_PLANS,
        "num_grouping_plans_per_entity": GLOBAL_NUM_GROUPING_PLANS,
        "num_access_plans_per_attribute": GLOBAL_PLANS_PER_ACCESS_PLAN,
        "filter_proportion": GLOBAL_FILTER_PROPORTION,
        "split": "test"
    },
    {
        "ring_id": "shooting-1467-4a02-8785-ec251e78d5be",
        "entities": ["Incident"],
        "num_plans_per_base_plan_per_entity": GLOBAL_PLANS_PER_BASE_PLAN,
        "num_retrieval_plans_per_entity": GLOBAL_NUM_RETRIEVAL_PLANS,
        "num_grouping_plans_per_entity": GLOBAL_NUM_GROUPING_PLANS,
        "num_access_plans_per_attribute": GLOBAL_PLANS_PER_ACCESS_PLAN,
        "filter_proportion": GLOBAL_FILTER_PROPORTION,
        "split": "test"
    },
    {
        "ring_id": "shooting-1467-4a02-8785-ec251e78d5be",
        "entities": ["State"],
        "num_plans_per_base_plan_per_entity": GLOBAL_PLANS_PER_BASE_PLAN,
        "num_retrieval_plans_per_entity": GLOBAL_NUM_RETRIEVAL_PLANS,
        "num_grouping_plans_per_entity": GLOBAL_NUM_GROUPING_PLANS,
        "num_access_plans_per_attribute": GLOBAL_PLANS_PER_ACCESS_PLAN,
        "filter_proportion": GLOBAL_FILTER_PROPORTION,
        "split": "test"
    },
    {
        "ring_id": "CropYield-bf90b954-cef1-44a4-aa37-d2fbf2622671",
        "entities": ["Country"],
        "num_plans_per_base_plan_per_entity": GLOBAL_PLANS_PER_BASE_PLAN,
        "num_retrieval_plans_per_entity": GLOBAL_NUM_RETRIEVAL_PLANS,
        "num_grouping_plans_per_entity": GLOBAL_NUM_GROUPING_PLANS,
        "num_access_plans_per_attribute": GLOBAL_PLANS_PER_ACCESS_PLAN,
        "filter_proportion": GLOBAL_FILTER_PROPORTION,
        "split": "test"
    },
    {
        "ring_id": "CropYield-bf90b954-cef1-44a4-aa37-d2fbf2622671",
        "entities": ["CropYield"],
        "num_plans_per_base_plan_per_entity": GLOBAL_PLANS_PER_BASE_PLAN,
        "num_retrieval_plans_per_entity": GLOBAL_NUM_RETRIEVAL_PLANS,
        "num_grouping_plans_per_entity": GLOBAL_NUM_GROUPING_PLANS,
        "num_access_plans_per_attribute": GLOBAL_PLANS_PER_ACCESS_PLAN,
        "filter_proportion": GLOBAL_FILTER_PROPORTION,
        "split": "test"
    }
]

def create_filename(config: Dict) -> str:
    return "_".join(config["entities"] + [config["ring_id"]]) + str(datetime.datetime.now()).replace(" ", "_") + ".json"

def main():

    # Determine the output directory paths for each of the splits
    ts = str(datetime.datetime.now()).replace(" ", "_")
    output_dir_name = f"benchmark_dataset_{ts}"
    output_directory = os.path.join(GENERATION_ROOT_DIR, "generated_data", output_dir_name)
    os.mkdir(output_directory)

    # Determine the name of a new directory that will be generated the benchmark dataset
    OUTPUT_DIRS = {
        "train": os.path.join(output_directory, "train"),
        "dev": os.path.join(output_directory, "dev"),
        "test": os.path.join(output_directory, "test")
    }

    # Make sure the output directories exist
    for path in OUTPUT_DIRS.values():
        os.mkdir(path)

    # Loop over each of the data generation configs to create the data
    for c in CONFIGS:
        generate_data(ring_id=c["ring_id"],
                      num_plans_per_base_plan_per_entity=c["num_plans_per_base_plan_per_entity"],
                      num_retrieval_plans_per_entity=c["num_retrieval_plans_per_entity"],
                      num_grouping_plans_per_entity=c["num_grouping_plans_per_entity"],
                      num_access_plans_per_attribute=c["num_access_plans_per_attribute"],
                      filter_proportion=c["filter_proportion"],
                      entities=c["entities"],
                      base_plans=[],
                      ignore_base_plans=[],
                      output_directory=OUTPUT_DIRS[c["split"]],
                      output_filename=create_filename(c),
                      save_intermediate_output=False)

    print(f'Finished at {str(datetime.datetime.now()).replace(" ", "_")}')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    main()
