import os
import argparse
import datetime
from typing import Dict
import json
from generate_training_data import (
    generate_data_with_access_plans,
    generate_data_with_base_plans,
    generate_data_with_grouping_plans,
    generate_data_with_in_operation_plans,
    generate_data_with_retrieval_plans,
    generate_data_with_set_operation_plans,
    generate_data_with_multi_join_plans,
    generate_data_with_simple_join_plans,
    generate_data_with_simple_aggregation_plans,
    generate_data_with_simple_sql_plans,
    compile_plans,
    generate_sql,
    build_metadata,
)
import random
from wasabi import msg
from typing import List
import logging
import math

# SET SEED
random.seed(0)


################################################################################
#                                   TODO List
#
# - TODO: Add flags for which splits to generate
# - TODO: Determine if we can use just one config per ring by combining the entities lists
#
################################################################################

GENERATION_ROOT_DIR = ""


GLOBAL_PLANS_PER_BASE_PLAN = 0

# TODO- generate 20% with each generator except bps? and evenly for each entity in a ring?

# GLOBAL_NUM_RETRIEVAL_PLANS = 100
# GLOBAL_PLANS_PER_ACCESS_PLAN = 10
# GLOBAL_NUM_GROUPING_PLANS = 100
# GLOBAL_NUM_SET_OP_PLANS = 100
# GLOBAL_NUM_IN_OP_PLANS = 100

# made these numbers larger due to small samples for each ring and entity
# GLOBAL_FILTER_PROPORTION = (
#     0.5  # need to sdjust this if only 1 plan? - may want this lower
# )

#

# GLOBAL_FILTER_PROPORTION = 0.5
# GLOBAL_IN_AND_SET_FILTER_PROPORTION = 0.1
# GLOBAL_IN_OP_NEGATE_PROPORTION = 0.75
# GLOBAL_RETRIEVAL_DISTINCT_PROPORTION = 0.75
# GLOBAL_GROUPING_HAVING_PROPORTION = 0.75
# GLOBAL_AUGMENT_WITH_ORDER_BY_PROPORTION = 0.8
# GLOBAL_JOIN_ORDER_BY_PROPORTION = 0.45
# generate N times as much data as in spider
DATASET_SCALE = 5
# DATASET_SCALE = 1


# chosen based on spider ops dist
# order: access, retrieval, grouping, set, in, multi_join, simple_aggs, simple_sql
# GLOBAL_GENERATOR_SAMPLE_WEIGHTS = [0.0, 0.2, 0.15, 0.1, 0.1, 0.2, 0.15, 0.1]
# up sample multi joins and grouping plans for better coverage
# full v0
# GLOBAL_GENERATOR_SAMPLE_WEIGHTS = [0.0, 0.15, 0.25, 0.075, 0.075, 0.25, 0.1, 0.1]

# order: access, retrieval, grouping, set, in, multi_join, simple_aggs, simple_sql, simple_joins
# full_v0_2x
# GLOBAL_GENERATOR_SAMPLE_WEIGHTS = [0.0, 0.08, 0.08, 0.12, 0.07, 0.16, 0.15, 0.0, 0.34]

LEN_SPIDER_TRAIN = 7000
# assuming no failures, proportions should be close to this
# GLOBAL_GENERATOR_SAMPLE_WEIGHTS = [
#     0.0,  # access plans
#     1728 / LEN_SPIDER_TRAIN,  # retrieval plans
#     469 / LEN_SPIDER_TRAIN,  # grouping plans
#     526 / LEN_SPIDER_TRAIN,  # set plans
#     272 / LEN_SPIDER_TRAIN,  # in plans
#     827 / LEN_SPIDER_TRAIN,  # multijoin plans
#     469 / LEN_SPIDER_TRAIN,  # simple_agg plans
#     715 / LEN_SPIDER_TRAIN,  # simple sql plans
#     1994 / LEN_SPIDER_TRAIN,  # simple join plans
# ]
# adjusting for failures
# GLOBAL_GENERATOR_SAMPLE_WEIGHTS = [
#     0.0,  # access plans
#     250 / LEN_SPIDER_TRAIN,  # retrieval plans
#     344 / LEN_SPIDER_TRAIN,  # grouping plans
#     526 / LEN_SPIDER_TRAIN,  # set plans
#     272 / LEN_SPIDER_TRAIN,  # in plans
#     1574 / LEN_SPIDER_TRAIN,  # multijoin plans
#     844 / LEN_SPIDER_TRAIN,  # simple_agg plans
#     200 / LEN_SPIDER_TRAIN,  # simple sql plans
#     2991 / LEN_SPIDER_TRAIN,  # simple join plans
# ]


# GLOBAL_GENERATOR_SAMPLE_WEIGHTS = [
#     0.0,  # access plans
#     200 / LEN_SPIDER_TRAIN,  # retrieval plans
#     244 / LEN_SPIDER_TRAIN,  # grouping plans
#     556 / LEN_SPIDER_TRAIN,  # set plans
#     202 / LEN_SPIDER_TRAIN,  # in plans
#     1914 / LEN_SPIDER_TRAIN,  # multijoin plans
#     744 / LEN_SPIDER_TRAIN,  # simple_agg plans
#     150 / LEN_SPIDER_TRAIN,  # simple sql plans
#     2991 / LEN_SPIDER_TRAIN,  # simple join plans
# ]

# # 938 total group by - not including join plans - split between grouping and simple aggs
# # TODO: tune proportional params better
# GLOBAL_FILTER_PROPORTION = 0.5
# GLOBAL_IN_AND_SET_FILTER_PROPORTION = 0.1
# GLOBAL_IN_OP_NEGATE_PROPORTION = 0.85
# GLOBAL_RETRIEVAL_DISTINCT_PROPORTION = 0.75
# GLOBAL_GROUPING_HAVING_PROPORTION = 0.75
# GLOBAL_AUGMENT_WITH_ORDER_BY_PROPORTION = 0.85
# GLOBAL_JOIN_ORDER_BY_PROPORTION = 0.45


# REPLCED SET OPS WITH BP AND ADDED IN CONDITIONS TO FILTER TEMPLATES
GLOBAL_GENERATOR_SAMPLE_WEIGHTS = [
    0.0,  # access plans
    200 / LEN_SPIDER_TRAIN,  # retrieval plans
    244 / LEN_SPIDER_TRAIN,  # grouping plans
    556 / LEN_SPIDER_TRAIN,  # set plans
    # 202 / LEN_SPIDER_TRAIN,  # in plans
    0,
    2015 / LEN_SPIDER_TRAIN,  # multijoin plans
    744 / LEN_SPIDER_TRAIN,  # simple_agg plans
    150 / LEN_SPIDER_TRAIN,  # simple sql plans
    3092 / LEN_SPIDER_TRAIN,  # simple join plans
]

# 938 total group by - not including join plans - split between grouping and simple aggs
# TODO: tune proportional params better
GLOBAL_FILTER_PROPORTION = 0.5
GLOBAL_IN_AND_SET_FILTER_PROPORTION = 0.1
GLOBAL_IN_OP_NEGATE_PROPORTION = 0.85
GLOBAL_RETRIEVAL_DISTINCT_PROPORTION = 0.75
GLOBAL_GROUPING_HAVING_PROPORTION = 0.75
GLOBAL_AUGMENT_WITH_ORDER_BY_PROPORTION = 0.85
GLOBAL_JOIN_ORDER_BY_PROPORTION = 0.45

# CONFIGS = [
#     # =============================================
#     # TRAINING SET RINGS
#     #
#     # - SCALES
#     # - Illinois Report Card (Education)
#     # - Wildfire
#     # - Used Cars
#     # - Zillow
#     # - Stocks
#     # - Illinois Poverty and Labor Statistics (income_disparity)
#     #
#     # =============================================
#     {
#         "ring_id": "SCALES-1467-4a02-8785-ec251e78d5be",
#         "entities": ["Case"],
#         "num_plans_per_base_plan_per_entity": 20,
#         "num_retrieval_plans_per_entity": 100,
#         "num_access_plans_per_attribute": 10,
#         "filter_proportion": 0.95,
#         "split": "train",
#     },
#     {
#         "ring_id": "SCALES-1467-4a02-8785-ec251e78d5be",
#         "entities": ["Judge"],
#         "num_plans_per_base_plan_per_entity": 20,
#         "num_retrieval_plans_per_entity": 100,
#         "num_access_plans_per_attribute": 10,
#         "filter_proportion": 0.95,
#         "split": "train",
#     },
#     {
#         "ring_id": "education-1467-4a02-8785-ec251e78d5be",
#         "entities": ["School"],
#         "num_plans_per_base_plan_per_entity": 20,
#         "num_retrieval_plans_per_entity": 100,
#         "num_access_plans_per_attribute": 10,
#         "filter_proportion": 0.95,
#         "split": "train",
#     },
#     {
#         "ring_id": "education-1467-4a02-8785-ec251e78d5be",
#         "entities": ["District"],
#         "num_plans_per_base_plan_per_entity": 20,
#         "num_retrieval_plans_per_entity": 100,
#         "num_access_plans_per_attribute": 10,
#         "filter_proportion": 0.95,
#         "split": "train",
#     },
#     {
#         "ring_id": "CarPricing-1467-7b152-1275-ec251e78d5be",
#         "entities": ["UsedCar"],
#         "num_plans_per_base_plan_per_entity": 20,
#         "num_retrieval_plans_per_entity": 100,
#         "num_access_plans_per_attribute": 10,
#         "filter_proportion": 0.95,
#         "split": "train",
#     },
#     {
#         "ring_id": "Toxic-3418-r4hu-4289-38jd93k29s",
#         "entities": ["State"],
#         "num_plans_per_base_plan_per_entity": 20,
#         "num_retrieval_plans_per_entity": 100,
#         "num_access_plans_per_attribute": 10,
#         "filter_proportion": 0.95,
#         "split": "train",
#     },
#     {
#         "ring_id": "Toxic-3418-r4hu-4289-38jd93k29s",
#         "entities": ["Wildfire"],
#         "num_plans_per_base_plan_per_entity": 20,
#         "num_retrieval_plans_per_entity": 100,
#         "num_access_plans_per_attribute": 10,
#         "filter_proportion": 0.95,
#         "split": "train",
#     },
#     {
#         "ring_id": "Zillow8-1467-4a02-8785-ec251e78d5be",
#         "entities": ["Region"],
#         "num_plans_per_base_plan_per_entity": 20,
#         "num_retrieval_plans_per_entity": 100,
#         "num_access_plans_per_attribute": 10,
#         "filter_proportion": 0.95,
#         "split": "train",
#     },
#     {
#         "ring_id": "Zillow8-1467-4a02-8785-ec251e78d5be",
#         "entities": ["RentRate"],
#         "num_plans_per_base_plan_per_entity": 20,
#         "num_retrieval_plans_per_entity": 100,
#         "num_access_plans_per_attribute": 10,
#         "filter_proportion": 0.95,
#         "split": "train",
#     },
#     {
#         "ring_id": "Stocks-fe5b7728-b527-4817-b407-d33a679ff218",
#         "entities": ["Security"],
#         "num_plans_per_base_plan_per_entity": 20,
#         "num_retrieval_plans_per_entity": 100,
#         "num_access_plans_per_attribute": 10,
#         "filter_proportion": 0.95,
#         "split": "train",
#     },
#     {
#         "ring_id": "Stocks-fe5b7728-b527-4817-b407-d33a679ff218",
#         "entities": ["SecurityRecord"],
#         "num_plans_per_base_plan_per_entity": 20,
#         "num_retrieval_plans_per_entity": 100,
#         "num_access_plans_per_attribute": 10,
#         "filter_proportion": 0.95,
#         "split": "train",
#     },
#     {
#         "ring_id": "money-1467-4a02-8785-ec251e78d5be",
#         "entities": ["County"],
#         "num_plans_per_base_plan_per_entity": 20,
#         "num_retrieval_plans_per_entity": 100,
#         "num_access_plans_per_attribute": 10,
#         "filter_proportion": 0.95,
#         "split": "train",
#     },
#     {
#         "ring_id": "money-1467-4a02-8785-ec251e78d5be",
#         "entities": ["IncomeRecord"],
#         "num_plans_per_base_plan_per_entity": 20,
#         "num_retrieval_plans_per_entity": 100,
#         "num_access_plans_per_attribute": 10,
#         "filter_proportion": 0.95,
#         "split": "train",
#     },
#     # =============================================
#     # DEV SET RINGS
#     #
#     # - MIMIC
#     # - Exonerations
#     # - Missing Migrants
#     #
#     # =============================================
#     {
#         "ring_id": "mimic9f2-1467-4a02-8785-ec251e78d5be",
#         "entities": ["Subject"],
#         "num_plans_per_base_plan_per_entity": 20,
#         "num_retrieval_plans_per_entity": 100,
#         "num_access_plans_per_attribute": 10,
#         "filter_proportion": 0.95,
#         "split": "dev",
#     },
#     {
#         "ring_id": "mimic9f2-1467-4a02-8785-ec251e78d5be",
#         "entities": ["EDstay"],
#         "num_plans_per_base_plan_per_entity": 20,
#         "num_retrieval_plans_per_entity": 100,
#         "num_access_plans_per_attribute": 10,
#         "filter_proportion": 0.95,
#         "split": "dev",
#     },
#     {
#         "ring_id": "Exonerations12-5732-8b01-9634-fa492d67c8af",
#         "entities": ["State"],
#         "num_plans_per_base_plan_per_entity": 20,
#         "num_retrieval_plans_per_entity": 100,
#         "num_access_plans_per_attribute": 10,
#         "filter_proportion": 0.95,
#         "split": "dev",
#     },
#     {
#         "ring_id": "Exonerations12-5732-8b01-9634-fa492d67c8af",
#         "entities": ["Exoneration"],
#         "num_plans_per_base_plan_per_entity": 20,
#         "num_retrieval_plans_per_entity": 100,
#         "num_access_plans_per_attribute": 10,
#         "filter_proportion": 0.95,
#         "split": "dev",
#     },
#     {
#         "ring_id": "MissingMigrantsData",
#         "entities": ["Country"],
#         "num_plans_per_base_plan_per_entity": 20,
#         "num_retrieval_plans_per_entity": 100,
#         "num_access_plans_per_attribute": 10,
#         "filter_proportion": 0.95,
#         "split": "dev",
#     },
#     {
#         "ring_id": "MissingMigrantsData",
#         "entities": ["Event"],
#         "num_plans_per_base_plan_per_entity": 20,
#         "num_retrieval_plans_per_entity": 100,
#         "num_access_plans_per_attribute": 10,
#         "filter_proportion": 0.95,
#         "split": "dev",
#     },
#     # =============================================
#     # TEST SET RINGS
#     #
#     # - Yelp
#     # - School Shootings
#     # - Crop Yields
#     #
#     # =============================================
#     {
#         "ring_id": "dcac39f2-1467-4a02-8785-ec251e78d5be",
#         "entities": ["Business"],
#         "num_plans_per_base_plan_per_entity": 20,
#         "num_retrieval_plans_per_entity": 100,
#         "num_access_plans_per_attribute": 10,
#         "filter_proportion": 0.95,
#         "split": "test",
#     },
#     {
#         "ring_id": "shooting-1467-4a02-8785-ec251e78d5be",
#         "entities": ["Incident"],
#         "num_plans_per_base_plan_per_entity": 20,
#         "num_retrieval_plans_per_entity": 100,
#         "num_access_plans_per_attribute": 10,
#         "filter_proportion": 0.95,
#         "split": "test",
#     },
#     {
#         "ring_id": "shooting-1467-4a02-8785-ec251e78d5be",
#         "entities": ["State"],
#         "num_plans_per_base_plan_per_entity": 20,
#         "num_retrieval_plans_per_entity": 100,
#         "num_access_plans_per_attribute": 10,
#         "filter_proportion": 0.95,
#         "split": "test",
#     },
#     {
#         "ring_id": "CropYield-bf90b954-cef1-44a4-aa37-d2fbf2622671",
#         "entities": ["Country"],
#         "num_plans_per_base_plan_per_entity": 20,
#         "num_retrieval_plans_per_entity": 100,
#         "num_access_plans_per_attribute": 10,
#         "filter_proportion": 0.95,
#         "split": "test",
#     },
#     {
#         "ring_id": "CropYield-bf90b954-cef1-44a4-aa37-d2fbf2622671",
#         "entities": ["CropYield"],
#         "num_plans_per_base_plan_per_entity": 20,
#         "num_retrieval_plans_per_entity": 100,
#         "num_access_plans_per_attribute": 10,
#         "filter_proportion": 0.95,
#         "split": "test",
#     },
# ]

split_info_fn = "generated_data/spider/full_splits/split_info.json"
SPLIT_INFO = json.load(open(split_info_fn, "r"))

# RING_DIR = "../../satyrn-rings/spider"
# RING_DIR = "../../satyrn-rings/spider_manual"
# RING_DIR = "../../satyrn-rings/spider_manual_simplified"
RING_DIR = "../../satyrn-rings/spider_auto_simplified_fixed_dts"


# TODO: may want to generate lots more plans then sample at entity level?
# may be slow to do that tho
def reweight_and_sample(n_plans, sample_weights, empty_idx):
    # sample_weights = sample_weights.copy()

    total = sum(sample_weights) - sample_weights[empty_idx]
    sample_weights = [w / total for w in sample_weights]
    sample_weights[empty_idx] = 0
    sampled_idxs = random.choices(
        range(0, len(sample_weights)),
        weights=sample_weights,
        k=n_plans,
    )
    return sample_weights, sampled_idxs


def generate_plans(rid, ent, n_plans, max_retries=3, sample=True):
    # print(ent)
    logging.info(n_plans)
    if sample:
        sample_weights = GLOBAL_GENERATOR_SAMPLE_WEIGHTS
        sampled_gens = random.choices(
            range(0, len(sample_weights)),
            weights=sample_weights,
            k=n_plans,
        )
        # n_random = n_plans % 5
        # additional_sampled_plans = random.sample(range(5), k=n_random)
        # print(n_random)
        # print(additional_sampled_plans)
        # n_plans_by_generator = [n_plans // 5] * 5
        # for i in additional_sampled_plans:
        # n_plans_by_generator[i] += 1
        # print(n_plans_by_generator)
        # assert sum(n_plans_by_generator) == n_plans

        n_plans_by_generator = [
            sampled_gens.count(i) for i in range(0, len(sample_weights))
        ]
    else:
        n_plans_by_generator = [
            math.ceil(n_plans / len(GLOBAL_GENERATOR_SAMPLE_WEIGHTS) - 1)
            for _ in GLOBAL_GENERATOR_SAMPLE_WEIGHTS
        ]

    logging.info(n_plans_by_generator)

    # in_plans = generate_data_with_in_operation_plans(
    #     ring_id=rid,
    #     num_in_operation_plans_per_entity=n_plans_by_generator[4],
    #     filter_proportion=(
    #         1 if n_plans_by_generator[4] < 2 else GLOBAL_FILTER_PROPORTION
    #     ),
    #     in_op_negate_proportion=GLOBAL_IN_OP_NEGATE_PROPORTION,
    #     entities=[ent],
    # )

    logging.info("generating grouping plans")
    grouping_plans = []
    grouping_plan_attempts = 0
    while not grouping_plans and grouping_plan_attempts < max_retries:
        try:
            grouping_plan_attempts += 1
            grouping_plans = generate_data_with_grouping_plans(
                ring_id=rid,
                num_grouping_plans_per_entity=n_plans_by_generator[2],
                filter_proportion=(
                    1
                    if n_plans_by_generator[2] < 2
                    else GLOBAL_FILTER_PROPORTION
                ),
                having_porportion=GLOBAL_GROUPING_HAVING_PROPORTION,
                entities=[ent],
                augment_with_order_by_proportion=GLOBAL_AUGMENT_WITH_ORDER_BY_PROPORTION,
            )
        except:
            logging.warning(
                f"Error generating grouping plans for ring {rid} for entity {ent}."
            )
    # if len(grouping_plans) < n_plans_by_generator[2]:
    # want to always set sample weights of already generated plans to 0
    if sample:
        sample_weights, additional_sample_idxs = reweight_and_sample(
            n_plans_by_generator[2] - len(grouping_plans),
            sample_weights=sample_weights,
            empty_idx=2,
        )
        n_plans_by_generator[2] = len(grouping_plans)
        for i in range(0, len(sample_weights)):
            n_plans_by_generator[i] += additional_sample_idxs.count(i)

    logging.info("generating multi-join plans")
    multi_join_plans = []
    multi_join_plan_attempts = 0
    while not multi_join_plans and multi_join_plan_attempts < max_retries:
        try:
            multi_join_plan_attempts += 1
            multi_join_plans = generate_data_with_multi_join_plans(
                ring_id=rid,
                num_multi_join_plans_per_entity=n_plans_by_generator[5],
                filter_proportion=(
                    1
                    if n_plans_by_generator[5] < 2
                    else GLOBAL_FILTER_PROPORTION
                ),
                entities=[ent],
                augment_with_order_by_proportion=GLOBAL_AUGMENT_WITH_ORDER_BY_PROPORTION,
            )
        except:
            logging.warning(
                f"Error generating multi-join plans for ring {rid} for entity {ent}."
            )

    # if len(multi_join_plans) < n_plans_by_generator[5]:
    # want to always set sample weights of already generated plans to 0
    if sample:
        sample_weights, additional_sample_idxs = reweight_and_sample(
            n_plans_by_generator[5] - len(multi_join_plans),
            sample_weights=sample_weights,
            empty_idx=5,
        )
        n_plans_by_generator[5] = len(multi_join_plans)
        for i in range(0, len(sample_weights)):
            n_plans_by_generator[i] += additional_sample_idxs.count(i)

    logging.info("generating simple-join plans")
    simple_join_plans = []
    simple_join_plan_attempts = 0
    while not simple_join_plans and simple_join_plan_attempts < max_retries:
        try:
            simple_join_plan_attempts += 1
            simple_join_plans = generate_data_with_simple_join_plans(
                ring_id=rid,
                num_simple_join_plans_per_entity=n_plans_by_generator[8],
                filter_proportion=(
                    1
                    if n_plans_by_generator[8] < 2
                    else GLOBAL_FILTER_PROPORTION
                ),
                entities=[ent],
                # augment_with_order_by_proportion=GLOBAL_AUGMENT_WITH_ORDER_BY_PROPORTION,
                augment_with_order_by_proportion=GLOBAL_JOIN_ORDER_BY_PROPORTION,
            )
        except:
            logging.warning(
                f"Error generating simple-join plans for ring {rid} for entity {ent}."
            )

    # if len(simple_join_plans) < n_plans_by_generator[8]:
    if sample:
        sample_weights, additional_sample_idxs = reweight_and_sample(
            n_plans_by_generator[8] - len(simple_join_plans),
            sample_weights=sample_weights,
            empty_idx=8,
        )
        n_plans_by_generator[8] = len(simple_join_plans)
        for i in range(0, len(sample_weights)):
            n_plans_by_generator[i] += additional_sample_idxs.count(i)

    # set_plans = generate_data_with_set_operation_plans(
    #     ring_id=rid,
    #     num_set_operation_plans_per_entity=n_plans_by_generator[3],
    #     filter_proportion=(
    #         1 if n_plans_by_generator[3] < 2 else GLOBAL_FILTER_PROPORTION
    #     ),
    #     entities=[ent],
    # )

    logging.info("generating in plans")
    in_plans = []
    in_plan_attempts = 0
    while not in_plans and in_plan_attempts < max_retries:
        try:
            in_plan_attempts += 1
            in_plans = generate_data_with_in_operation_plans(
                ring_id=rid,
                num_in_operation_plans_per_entity=n_plans_by_generator[4],
                filter_proportion=(
                    # 1 if n_plans_by_generator[4] < 2 else GLOBAL_FILTER_PROPORTION
                    GLOBAL_IN_AND_SET_FILTER_PROPORTION
                ),
                in_op_negate_proportion=GLOBAL_IN_OP_NEGATE_PROPORTION,
                entities=[ent],
                augment_with_order_by_proportion=GLOBAL_AUGMENT_WITH_ORDER_BY_PROPORTION,
            )
        except:
            logging.warning(
                f"Error generating in plans for ring {rid} for entity {ent}."
            )

    # if len(in_plans) < n_plans_by_generator[4]:
    if sample:
        sample_weights, additional_sample_idxs = reweight_and_sample(
            n_plans_by_generator[4] - len(in_plans),
            sample_weights=sample_weights,
            empty_idx=4,
        )
        n_plans_by_generator[4] = len(in_plans)
        for i in range(0, len(sample_weights)):
            n_plans_by_generator[i] += additional_sample_idxs.count(i)

    logging.info("generating set plans")
    set_plans = []
    set_plan_attempts = 0
    while not set_plans and set_plan_attempts < max_retries:
        try:
            set_plan_attempts += 1
            # python generator
            set_plans = generate_data_with_set_operation_plans(
                ring_id=rid,
                num_set_operation_plans_per_entity=n_plans_by_generator[3] // 2,
                filter_proportion=(
                    # 1 if n_plans_by_generator[3] < 2 else GLOBAL_FILTER_PROPORTION
                    GLOBAL_IN_AND_SET_FILTER_PROPORTION
                ),
                entities=[ent],
                augment_with_order_by_proportion=GLOBAL_AUGMENT_WITH_ORDER_BY_PROPORTION,
            )

            # set op baseplans - need to improve coverage with a few templates?
            set_plans.extend(
                generate_data_with_base_plans(
                    rid,
                    num_plans_per_base_plan_per_entity=(
                        n_plans_by_generator[3] + 1
                    )
                    // 2,
                    filter_proportion=GLOBAL_FILTER_PROPORTION,
                    entities=[ent],
                    desired_base_plans=["GeneralSetOp"],
                    ignored_base_plans=[],
                )
            )
        except:
            logging.warning(
                f"Error generating set plans for ring {rid} for entity {ent}."
            )

    # if len(set_plans) < n_plans_by_generator[3]:
    if sample:
        sample_weights, additional_sample_idxs = reweight_and_sample(
            n_plans_by_generator[3] - len(set_plans),
            sample_weights=sample_weights,
            empty_idx=3,
        )
        n_plans_by_generator[3] = len(set_plans)
        for i in range(0, len(sample_weights)):
            n_plans_by_generator[i] += additional_sample_idxs.count(i)

    logging.info("generating retrieval plans")
    retrieval_plans = []
    retrieval_plan_attempts = 0
    while not retrieval_plans and retrieval_plan_attempts < max_retries:
        try:
            retrieval_plan_attempts += 1
            retrieval_plans = generate_data_with_retrieval_plans(
                ring_id=rid,
                num_retrieval_plans_per_entity=n_plans_by_generator[1],
                filter_proportion=(
                    1
                    if n_plans_by_generator[1] < 2
                    else GLOBAL_FILTER_PROPORTION
                ),
                distinct_proportion=GLOBAL_RETRIEVAL_DISTINCT_PROPORTION,
                entities=[ent],
                augment_with_order_by_proportion=GLOBAL_AUGMENT_WITH_ORDER_BY_PROPORTION,
            )
        except:
            logging.warning(
                f"Error generating retrieval plans for ring {rid} for entity {ent}."
            )

    logging.info("generating simple agg plans")
    simple_agg_plans = []
    simple_agg_plan_attempts = 0
    while not simple_agg_plans and simple_agg_plan_attempts < max_retries:
        try:
            simple_agg_plan_attempts += 1
            simple_agg_plans = generate_data_with_simple_aggregation_plans(
                ring_id=rid,
                num_simple_aggregation_plans_per_entity=n_plans_by_generator[6],
                filter_proportion=(
                    1
                    if n_plans_by_generator[6] < 2
                    else GLOBAL_FILTER_PROPORTION
                ),
                entities=[ent],
                augment_with_order_by_proportion=GLOBAL_AUGMENT_WITH_ORDER_BY_PROPORTION,
            )
        except:
            logging.warning(
                f"Error generating simple agg plans for ring {rid} for entity {ent}."
            )

    generated_plans = (
        retrieval_plans
        + grouping_plans
        + set_plans
        + in_plans
        + multi_join_plans
        + simple_agg_plans
        + simple_join_plans
    )

    # instead of using access plans, try filling things with more simple_sql plans
    # this should allow all rings to have a the desired number of plans
    logging.info("generating simple sql plans")
    if sample:
        n_plans_by_generator[7] = n_plans - len(generated_plans)
    try:
        simple_sql_plans = generate_data_with_simple_sql_plans(
            rid,
            n_plans_by_generator[7],
            GLOBAL_FILTER_PROPORTION if n_plans_by_generator[7] > 1 else 1,
            [ent],
        )
    except:
        logging.warning(
            f"Error generating simple sql plans for ring {rid} for entity {ent}."
        )
        simple_sql_plans = []
    # print(len(generated_plans))
    # print(len(simple_sql_plans))
    # print(simple_sql_plans)

    # in case of some plans not being compatible or generated, use more access plans
    # n_plans_by_generator[0] = n_plans - len(generated_plans) - len(simple_sql_plans)
    # if n_plans_by_generator[0]:

    #     logging.info("generating access plans")
    #     try:
    #         access_plans = generate_data_with_access_plans(
    #             ring_id=rid,
    #             num_access_plans_per_attribute=1,
    #             filter_proportion=GLOBAL_FILTER_PROPORTION,
    #             entities=[ent],
    #             augment_with_order_by_proportion=GLOBAL_AUGMENT_WITH_ORDER_BY_PROPORTION,
    #         )
    #         while len(access_plans) < n_plans_by_generator[0]:
    #             access_plans.extend(
    #                 generate_data_with_access_plans(
    #                     ring_id=rid,
    #                     num_access_plans_per_attribute=1,
    #                     filter_proportion=1,
    #                     entities=[ent],
    #                     augment_with_order_by_proportion=GLOBAL_AUGMENT_WITH_ORDER_BY_PROPORTION,
    #                 )
    #             )
    #         # print(len(access_plans))
    #         # print(n_plans_by_generator)
    #         sampled_access_plans = random.sample(
    #             access_plans, k=n_plans_by_generator[0]
    #         )
    #         generated_plans.extend(sampled_access_plans)
    #     except:
    #         logging.warning(
    #             f"Error generating access plans for ring {rid} for entity {ent}."
    #         )
    #         sampled_access_plans = []
    # print(len(sampled_access_plans))
    logging.info(len(generated_plans))
    if not generated_plans and n_plans:
        logging.error(
            f"Could not generate any plans for ring {rid} for entity {ent}."
        )
    return generated_plans, simple_sql_plans


# N_PLANS_PER_DB = 250


def generate_data_for_spider_dbs():
    ps_and_qs_by_split = {}
    plans_with_no_sql_by_ring = {}
    for fn in os.listdir(RING_DIR):
        # use this for original subset of spider rings
        # ring_fn = os.path.join(RING_DIR, d, "ring.json")
        # if os.path.exists(ring_fn):
        d = fn.split(".")[0]
        ring_fn = os.path.join(RING_DIR, fn)
        ring = json.load(open(ring_fn, "r"))
        rid = ring["rid"]
        ents = [e["name"] for e in ring["ontology"]["entities"]]
        logging.info(f"{rid}, {ents}")
        num_plans = int(SPLIT_INFO["num_db_examples"][d] * DATASET_SCALE)
        for k, dbs in SPLIT_INFO["db_splits"].items():
            if d in dbs:
                split = k

        logging.info(split)
        logging.info(num_plans)
        plans_for_ring = []
        simple_sql_plans_for_ring = []
        # print(num_plans // len(ents))
        sampled_ents = random.choices(range(len(ents)), k=num_plans)
        n_plans_by_ent = [sampled_ents.count(i) for i in range(0, len(ents))]
        for i, (ent, n_ent_plans) in enumerate(zip(ents, n_plans_by_ent)):
            logging.info(ent)
            if n_ent_plans:
                plans, simple_sql_plans = generate_plans(
                    rid,
                    ent,
                    n_ent_plans,
                    # TODO: remove - only for checking coverage and uncomment above
                    # math.ceil(N_PLANS_PER_DB / len(ents)),
                    # TODO: remove - only for checking coverage
                    # sample=False,
                )
                plans_for_ring.extend(plans)
                simple_sql_plans_for_ring.extend(simple_sql_plans)
        logging.info(len(plans_for_ring))
        if not plans_for_ring:
            logging.error(f"Could not generate plans for ring {rid}.")
            print(f"Could not generate plans for ring {rid}.")
        logging.info("Compiling...")
        plans_for_ring = compile_plans(plans_for_ring)
        logging.info("Finished compiling the SQR plans.")

        logging.info("Generating corresponding SQL queries...")
        plans_for_ring = generate_sql(plans_for_ring, rid)

        n_total_plans = len(plans_for_ring)

        plans_for_ring_with_no_sql = [p for p in plans_for_ring if not p["sql"]]
        plans_for_ring = [p for p in plans_for_ring if p["sql"]]
        if plans_for_ring_with_no_sql:
            logging.error(
                f"For ring {rid}, {len(plans_for_ring_with_no_sql)} plans do not have sql plans"
            )
            plans_with_no_sql_by_ring[rid] = plans_for_ring_with_no_sql
        if not plans_for_ring:
            logging.error(f"Could not generate sql for ring {rid}.")
            print(f"Could not generate sql for ring {rid}.")

        logging.info("Finished generating the SQL queries.")
        plans_for_ring.extend(simple_sql_plans_for_ring)
        if split in ps_and_qs_by_split.keys():
            ps_and_qs_by_split[split].extend(plans_for_ring)
        else:
            ps_and_qs_by_split[split] = plans_for_ring
    return ps_and_qs_by_split, plans_with_no_sql_by_ring


# def create_filename(config: Dict) -> str:
#     return (
#         "_".join(config["entities"] + [config["ring_id"]])
#         + str(datetime.datetime.now()).replace(" ", "_")
#         + ".json"
#     )


def save_data_for_split(
    plans_and_questions: List[Dict],
    file_path: str,
    additional_metadata: Dict = None,
) -> None:
    # Add the ring_id to each of the generated training examples
    # for d in plans_and_questions:
    #     d["ring_id"] = ring_id

    # Get a string containing the entities and attributes for the ring
    # ring_ents_and_attrs = get_ring_ents_and_attrs_str(ring_id)

    final_output = {
        # "metadata": build_metadata(plans_and_questions, ring_ents_and_attrs),
        "metadata": build_metadata(plans_and_questions, None),
        "data": plans_and_questions,
    }

    if additional_metadata:
        final_output["metadata"].update(additional_metadata)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(final_output, indent=4))


def main(output_dir_name):

    # Determine the output directory paths for each of the splits
    ts = str(datetime.datetime.now()).replace(" ", "_")
    # output_dir_name = f"test_v1_benchmark_dataset_from_spider_{ts}"
    output_directory = os.path.join(
        GENERATION_ROOT_DIR, "generated_data", output_dir_name
    )
    os.makedirs(output_directory)

    logging.basicConfig(
        level=logging.INFO,
        filename=os.path.join(output_directory, "generation_log.txt"),
    )

    # Determine the name of a new directory that will be generated the benchmark dataset
    OUTPUT_FNS = {
        "train": os.path.join(output_directory, "train.json"),
        "dev": os.path.join(output_directory, "dev.json"),
        "test": os.path.join(output_directory, "test.json"),
    }

    ps_and_qs_by_split, plans_with_no_sql = generate_data_for_spider_dbs()

    for split, plans in ps_and_qs_by_split.items():
        save_data_for_split(plans, OUTPUT_FNS[split])

    json.dump(
        plans_with_no_sql,
        open(os.path.join(output_directory, "plans_with_no_sql.json"), "w"),
    )
    # print("Compiling the SQR plans...")
    # for split, plans in ps_and_qs_by_split.items():
    #     ps_and_qs_by_split[split] = compile_plans(ps_and_qs_by_split[split])
    # msg.good("Finished compiling the SQR plans.")

    # print("Generating corresponding SQL queries...")
    # for split, plans in ps_and_qs_by_split.items():
    #     ps_and_qs_by_split[split] = generate_sql(ps_and_qs_by_split["split"])
    # msg.good("Finished generating corresponding SQL queries.")
    # TODO: uncomment once CONFIG list generated
    # Make sure the output directories exist
    # for path in OUTPUT_DIRS.values():
    #     os.mkdir(path)

    # # Loop over each of the data generation configs to create the data
    # for c in CONFIGS:
    #     generate_data(
    #         ring_id=c["ring_id"],
    #         num_plans_per_base_plan_per_entity=c["num_plans_per_base_plan_per_entity"],
    #         num_retrieval_plans_per_entity=c["num_retrieval_plans_per_entity"],
    #         num_access_plans_per_attribute=c["num_access_plans_per_attribute"],
    #         filter_proportion=c["filter_proportion"],
    #         entities=c["entities"],
    #         base_plans=[],
    #         ignore_base_plans=[],
    #         output_directory=OUTPUT_DIRS[c["split"]],
    #         output_filename=create_filename(c),
    #         save_intermediate_output=False,
    #     )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output_dir_name",
        # default=f"satdb_from_spider_full_3x_simplified_v7_improved/splits_raw",
        default=f"ringsql_gen_from_spider_5x/splits_raw",
    )
    args = parser.parse_args()
    main(args.output_dir_name)
