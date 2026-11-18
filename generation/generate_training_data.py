################################################################################################################################
#
#       This script can be used to generate training data for the text-to-SQL and text-to-SQR tasks.
#
#
#       Example Usage:
#
#       Make sure the Satyrn-API is running and has the desired rings loaded.
#
#       Then, from the directory containing this script, run the following command:
#
#           python generate_training_data.py Toxic-3418-r4hu-4289-38jd93k29s 100 50 100 0.7 --entities State --base_plans EntityCount
#
################################################################################################################################

import os
import json
import argparse
import requests
import datetime
from typing import List, Dict
from collections import defaultdict

from tqdm import tqdm
from wasabi import msg

GENERATION_ROOT_DIR = ""
SATYRN_URL = "http://127.0.0.1:5000/"
APIKEY = "thisisatestkey"
HEADERS = {"x-api-key": APIKEY}


def get_and_make_default_output_directory() -> str:
    # Determine the output directory path
    ts = str(datetime.datetime.now()).replace(" ", "_")
    output_dir_name = f"training_data_{ts}"
    output_directory = os.path.join(
        GENERATION_ROOT_DIR, "generated_data", output_dir_name
    )

    # Make the output directory
    os.mkdir(output_directory)

    return output_directory


def make_results_url(url, ring_id, url_type):
    return f"{url}api/{url_type}/{ring_id}/1/"


def generate_data_with_access_plans(
    ring_id: str,
    entities: List[str],
    num_access_plans_per_attribute: int,
    filter_proportion: float,
    augment_with_order_by_proportion: float,
) -> List:
    urllink = make_results_url(SATYRN_URL, ring_id, "generate_plans")
    resp = requests.get(
        urllink,
        headers=HEADERS,
        json={
            "desired_entities": entities,
            "filter_proportion": filter_proportion,
            "num_access_plans_per_attribute": num_access_plans_per_attribute,
            "num_plans_per_base_plan_per_entity": 0,
            "num_retrieval_plans_per_entity": 0,
            "num_grouping_plans_per_entity": 0,
            "num_set_operation_plans_per_entity": 0,
            "num_in_operation_plans_per_entity": 0,
            "in_op_negate_proportion": 0,
            "num_multi_join_plans_per_entity": 0,
            "num_simple_aggregation_plans_per_entity": 0,
            "num_simple_join_plans_per_entity": 0,
            "augment_with_order_by_proportion": augment_with_order_by_proportion,
        },
    )
    results = json.loads(resp.content.decode("utf-8"))
    return results["plans_and_questions"]


def generate_data_with_retrieval_plans(
    ring_id: str,
    num_retrieval_plans_per_entity: int,
    filter_proportion: float,
    distinct_proportion: float,
    entities: List[str],
    augment_with_order_by_proportion: float,
) -> List:
    urllink = make_results_url(SATYRN_URL, ring_id, "generate_plans")
    resp = requests.get(
        urllink,
        headers=HEADERS,
        json={
            "desired_entities": entities,
            "filter_proportion": filter_proportion,
            "num_access_plans_per_attribute": 0,
            "num_plans_per_base_plan_per_entity": 0,
            "num_retrieval_plans_per_entity": num_retrieval_plans_per_entity,
            "num_grouping_plans_per_entity": 0,
            "num_set_operation_plans_per_entity": 0,
            "num_in_operation_plans_per_entity": 0,
            "in_op_negate_proportion": 0,
            "retrieval_distinct_proportion": distinct_proportion,
            "num_multi_join_plans_per_entity": 0,
            "num_simple_aggregation_plans_per_entity": 0,
            "num_simple_join_plans_per_entity": 0,
            "augment_with_order_by_proportion": augment_with_order_by_proportion,
        },
    )
    results = json.loads(resp.content.decode("utf-8"))
    return results["plans_and_questions"]


def generate_data_with_grouping_plans(
    ring_id: str,
    num_grouping_plans_per_entity: int,
    filter_proportion: float,
    having_porportion: float,
    entities: List[str],
    augment_with_order_by_proportion: float,
) -> List:
    urllink = make_results_url(SATYRN_URL, ring_id, "generate_plans")
    resp = requests.get(
        urllink,
        headers=HEADERS,
        json={
            "desired_entities": entities,
            "filter_proportion": filter_proportion,
            "num_access_plans_per_attribute": 0,
            "num_plans_per_base_plan_per_entity": 0,
            "num_retrieval_plans_per_entity": 0,
            "num_grouping_plans_per_entity": num_grouping_plans_per_entity,
            "num_set_operation_plans_per_entity": 0,
            "num_in_operation_plans_per_entity": 0,
            "in_op_negate_proportion": 0,
            "grouping_having_proportion": having_porportion,
            "num_multi_join_plans_per_entity": 0,
            "num_simple_aggregation_plans_per_entity": 0,
            "num_simple_join_plans_per_entity": 0,
            "augment_with_order_by_proportion": augment_with_order_by_proportion,
        },
    )
    results = json.loads(resp.content.decode("utf-8"))
    return results["plans_and_questions"]


def generate_data_with_set_operation_plans(
    ring_id: str,
    num_set_operation_plans_per_entity: int,
    filter_proportion: float,
    entities: List[str],
    augment_with_order_by_proportion: float,
) -> List:
    urllink = make_results_url(SATYRN_URL, ring_id, "generate_plans")
    resp = requests.get(
        urllink,
        headers=HEADERS,
        json={
            "desired_entities": entities,
            "filter_proportion": filter_proportion,
            "num_access_plans_per_attribute": 0,
            "num_plans_per_base_plan_per_entity": 0,
            "num_retrieval_plans_per_entity": 0,
            "num_grouping_plans_per_entity": 0,
            "num_set_operation_plans_per_entity": num_set_operation_plans_per_entity,
            "num_in_operation_plans_per_entity": 0,
            "in_op_negate_proportion": 0,
            "num_multi_join_plans_per_entity": 0,
            "num_simple_aggregation_plans_per_entity": 0,
            "num_simple_join_plans_per_entity": 0,
            "augment_with_order_by_proportion": augment_with_order_by_proportion,
        },
    )
    results = json.loads(resp.content.decode("utf-8"))
    return results["plans_and_questions"]


def generate_data_with_in_operation_plans(
    ring_id: str,
    num_in_operation_plans_per_entity: int,
    filter_proportion: float,
    in_op_negate_proportion: float,
    entities: List[str],
    augment_with_order_by_proportion: float,
) -> List:
    urllink = make_results_url(SATYRN_URL, ring_id, "generate_plans")
    resp = requests.get(
        urllink,
        headers=HEADERS,
        json={
            "desired_entities": entities,
            "filter_proportion": filter_proportion,
            "num_access_plans_per_attribute": 0,
            "num_plans_per_base_plan_per_entity": 0,
            "num_retrieval_plans_per_entity": 0,
            "num_grouping_plans_per_entity": 0,
            "num_set_operation_plans_per_entity": 0,
            "num_in_operation_plans_per_entity": num_in_operation_plans_per_entity,
            "in_op_negate_proportion": in_op_negate_proportion,
            "num_multi_join_plans_per_entity": 0,
            "num_simple_aggregation_plans_per_entity": 0,
            "num_simple_join_plans_per_entity": 0,
            "augment_with_order_by_proportion": augment_with_order_by_proportion,
        },
    )
    results = json.loads(resp.content.decode("utf-8"))
    return results["plans_and_questions"]


def generate_data_with_multi_join_plans(
    ring_id: str,
    num_multi_join_plans_per_entity: int,
    filter_proportion: float,
    entities: List[str],
    augment_with_order_by_proportion: float,
) -> List:
    urllink = make_results_url(SATYRN_URL, ring_id, "generate_plans")
    resp = requests.get(
        urllink,
        headers=HEADERS,
        json={
            "desired_entities": entities,
            "filter_proportion": filter_proportion,
            "num_access_plans_per_attribute": 0,
            "num_plans_per_base_plan_per_entity": 0,
            "num_retrieval_plans_per_entity": 0,
            "num_grouping_plans_per_entity": 0,
            "num_set_operation_plans_per_entity": 0,
            "num_in_operation_plans_per_entity": 0,
            "in_op_negate_proportion": 0,
            "num_multi_join_plans_per_entity": num_multi_join_plans_per_entity,
            "num_simple_aggregation_plans_per_entity": 0,
            "num_simple_join_plans_per_entity": 0,
            "augment_with_order_by_proportion": augment_with_order_by_proportion,
        },
    )
    results = json.loads(resp.content.decode("utf-8"))
    return results["plans_and_questions"]


def generate_data_with_simple_aggregation_plans(
    ring_id: str,
    num_simple_aggregation_plans_per_entity: int,
    filter_proportion: float,
    entities: List[str],
    augment_with_order_by_proportion: float,
) -> List:
    urllink = make_results_url(SATYRN_URL, ring_id, "generate_plans")
    resp = requests.get(
        urllink,
        headers=HEADERS,
        json={
            "desired_entities": entities,
            "filter_proportion": filter_proportion,
            "num_access_plans_per_attribute": 0,
            "num_plans_per_base_plan_per_entity": 0,
            "num_retrieval_plans_per_entity": 0,
            "num_grouping_plans_per_entity": 0,
            "num_set_operation_plans_per_entity": 0,
            "num_in_operation_plans_per_entity": 0,
            "in_op_negate_proportion": 0,
            "num_multi_join_plans_per_entity": 0,
            "num_simple_aggregation_plans_per_entity": num_simple_aggregation_plans_per_entity,
            "num_simple_join_plans_per_entity": 0,
            "augment_with_order_by_proportion": augment_with_order_by_proportion,
        },
    )
    results = json.loads(resp.content.decode("utf-8"))
    return results["plans_and_questions"]


def generate_data_with_simple_join_plans(
    ring_id: str,
    num_simple_join_plans_per_entity: int,
    filter_proportion: float,
    entities: List[str],
    augment_with_order_by_proportion: float,
) -> List:
    urllink = make_results_url(SATYRN_URL, ring_id, "generate_plans")
    resp = requests.get(
        urllink,
        headers=HEADERS,
        json={
            "desired_entities": entities,
            "filter_proportion": filter_proportion,
            "num_access_plans_per_attribute": 0,
            "num_plans_per_base_plan_per_entity": 0,
            "num_retrieval_plans_per_entity": 0,
            "num_grouping_plans_per_entity": 0,
            "num_set_operation_plans_per_entity": 0,
            "num_in_operation_plans_per_entity": 0,
            "in_op_negate_proportion": 0,
            "num_multi_join_plans_per_entity": 0,
            "num_simple_aggregation_plans_per_entity": 0,
            "num_simple_join_plans_per_entity": num_simple_join_plans_per_entity,
            "augment_with_order_by_proportion": augment_with_order_by_proportion,
        },
    )
    results = json.loads(resp.content.decode("utf-8"))
    return results["plans_and_questions"]


def generate_data_with_simple_sql_plans(
    ring_id: str,
    num_simple_sql_plans_per_entity: int,
    filter_proportion: float,
    entities: List[str],
) -> List:
    urllink = make_results_url(SATYRN_URL, ring_id, "generate_plans")
    resp = requests.get(
        urllink,
        headers=HEADERS,
        json={
            "desired_entities": entities,
            "filter_proportion": filter_proportion,
            "num_access_plans_per_attribute": 0,
            "num_plans_per_base_plan_per_entity": 0,
            "num_retrieval_plans_per_entity": 0,
            "num_grouping_plans_per_entity": 0,
            "num_set_operation_plans_per_entity": 0,
            "num_in_operation_plans_per_entity": 0,
            "in_op_negate_proportion": 0,
            "num_multi_join_plans_per_entity": 0,
            "num_simple_aggregation_plans_per_entity": 0,
            "num_simple_join_plans_per_entity": 0,
            "num_simple_sql_plans_per_entity": num_simple_sql_plans_per_entity,
            "augment_with_order_by_proportion": 0,
        },
    )
    results = json.loads(resp.content.decode("utf-8"))
    return results["plans_and_questions"]


def get_base_plan_templates() -> Dict:
    urllink = f"{SATYRN_URL}api/get_base_plans/"
    resp = requests.get(urllink, headers=HEADERS)
    results = json.loads(resp.content.decode("utf-8"))
    return results


def get_base_plan_templates_to_use(
    desired_base_plans: List[str], ignored_base_plans: List[str]
) -> Dict:
    base_plan_templates = get_base_plan_templates()
    # print(base_plan_templates)

    if len(desired_base_plans) > 0:
        base_plan_templates = {
            base_plan_name: base_plan_templates[base_plan_name]
            for base_plan_name in desired_base_plans
        }

    if len(ignored_base_plans) > 0:
        for base_plan_name in ignored_base_plans:
            if base_plan_name in base_plan_templates:
                del base_plan_templates[base_plan_name]

    return base_plan_templates


def get_ring_ents_and_attrs_str(ring_id: str):
    try:
        urllink = make_results_url(SATYRN_URL, ring_id, "get_ring_ents_attrs")
        resp = requests.get(urllink, headers=HEADERS)
        results = json.loads(resp.content.decode("utf-8"))
        ents_and_attrs = results["ents_and_attrs"]
    except:
        msg.fail(
            f"Unable to retrieve the entities and attributes string for ring: {ring_id}"
        )
        ents_and_attrs = ""
    return ents_and_attrs


def generate_data_with_base_plans(
    ring_id: str,
    num_plans_per_base_plan_per_entity: int,
    filter_proportion: float,
    entities: List[str],
    desired_base_plans: List[str] = None,
    ignored_base_plans: List[str] = None,
    order_by_proportion=0,
) -> List:
    plans_and_questions = []
    base_plan_templates_to_use = get_base_plan_templates_to_use(
        desired_base_plans, ignored_base_plans
    )

    urllink = make_results_url(SATYRN_URL, ring_id, "generate_plans")
    for base_plan_name in tqdm(base_plan_templates_to_use.keys()):
        temp_num_plans_per_base_plan_per_entity = (
            num_plans_per_base_plan_per_entity
        )
        temp_filter_proportion = filter_proportion
        while temp_num_plans_per_base_plan_per_entity:
            try:
                print(
                    f"Generating data with base plan '{base_plan_name}' where num_plans_per_base_plan_per_entity={temp_num_plans_per_base_plan_per_entity} and filter_proportion={temp_filter_proportion}..."
                )
                resp = requests.get(
                    urllink,
                    headers=HEADERS,
                    json={
                        "target_base_plan": base_plan_name,
                        "desired_entities": entities,
                        "num_plans_per_base_plan_per_entity": temp_num_plans_per_base_plan_per_entity,
                        "filter_proportion": temp_filter_proportion,
                        "num_access_plans_per_attribute": 0,
                        "num_retrieval_plans_per_entity": 0,
                        "num_grouping_plans_per_entity": 0,
                        "num_set_operation_plans_per_entity": 0,
                        "num_in_operation_plans_per_entity": 0,
                        "in_op_negate_proportion": 0,
                        "num_multi_join_plans_per_entity": 0,
                        "num_simple_aggregation_plans_per_entity": 0,
                        "num_simple_join_plans_per_entity": 0,
                        "num_simple_sql_plans_per_entity": 0,
                        "augment_with_order_by_proportion": order_by_proportion,
                    },
                )
                results = json.loads(resp.content.decode("utf-8"))

                plans_and_questions.extend(results["plans_and_questions"])
                temp_num_plans_per_base_plan_per_entity = False

                print()
                msg.good(
                    f"Successfully generated data with base plan '{base_plan_name}'."
                )
                print(
                    f"{len(plans_and_questions)} plans generated via base plans so far."
                )
            except Exception as e:
                # Ensure that we try to generate without filters before giving up
                if (
                    temp_num_plans_per_base_plan_per_entity // 2 < 1
                    and temp_filter_proportion > 0
                ):
                    temp_num_plans_per_base_plan_per_entity = (
                        temp_num_plans_per_base_plan_per_entity // 2
                    )
                    temp_filter_proportion = 0
                else:
                    # Halve the values with an int divide
                    temp_num_plans_per_base_plan_per_entity = (
                        temp_num_plans_per_base_plan_per_entity // 2
                    )
                    temp_filter_proportion = temp_filter_proportion // 2

                msg.fail(f"Error when generating plans for '{base_plan_name}'.")

    return plans_and_questions


def compile_plans(plans_and_questions: List[Dict]) -> List[Dict]:
    """
    Adds a "compiled_plan" key and value to each of the objects.
    :param plans_and_questions:
    :type plans_and_questions:
    :return:
    :rtype:
    """
    urllink = f"{SATYRN_URL}api/compile_sqr/1/"
    updated_plans_and_questions = []
    for d in tqdm(plans_and_questions):
        try:
            resp = requests.get(urllink, headers=HEADERS, json=d["plan"])
            results = json.loads(resp.content.decode("utf-8"))
            d["compiled_plan"] = results
            updated_plans_and_questions.append(d)
        except Exception as e:
            d["compiled_plan"] = None
            updated_plans_and_questions.append(d)
    print()
    return updated_plans_and_questions


def generate_sql(plans_and_questions: List[Dict], ring_id: str) -> List[Dict]:
    """
    Adds a "sql" key and value to each of the objects.
    :param plans_and_questions:
    :type plans_and_questions:
    :return:
    :rtype:
    """
    urllink = make_results_url(SATYRN_URL, ring_id, "sqr_to_sql")
    updated_plans_and_questions = []
    for d in tqdm(plans_and_questions):
        try:
            resp = requests.get(
                urllink, headers=HEADERS, json=d["compiled_plan"]
            )
            results = json.loads(resp.content.decode("utf-8"))
            d["sql"] = results["sql"]
            d["sql_original_aliases"] = results["sql_original_aliases"]
            updated_plans_and_questions.append(d)
        except Exception as e:
            d["sql"] = None
            d["sql_original_aliases"] = None
            updated_plans_and_questions.append(d)
    print()
    return updated_plans_and_questions


def build_metadata(
    plans_and_questions: List[Dict], ring_ents_and_attrs: str = ""
) -> Dict:
    base_plan_distribution = defaultdict(int)
    source_distribution = defaultdict(int)
    for d in plans_and_questions:
        if "base_plan" in d and d["base_plan"]:
            base_plan_distribution[d["base_plan"]] += 1
        # elif "bp" in d and d["bp"]:
        #     base_plan_distribution[d["bp"]] += 1
        if "source" in d and d["source"]:
            source_distribution[d["source"]] += 1

    return {
        "created_on": str(datetime.datetime.now()),
        "total_questions": sum(
            len(d["questions"]) if "questions" in d else 1
            for d in plans_and_questions
        ),
        "total_generated_sqr": len(plans_and_questions),
        "total_compiled_sqr": sum(
            1
            for d in plans_and_questions
            if "compiled_plan" in d and d["compiled_plan"]
        ),
        "total_sql": sum(
            1 for d in plans_and_questions if "sql" in d and d["sql"]
        ),
        "base_plan_distribution": base_plan_distribution,
        "ring_ents_and_attrs": ring_ents_and_attrs,
        "source_distribution": source_distribution,
    }


def save_data(
    plans_and_questions: List[Dict],
    file_path: str,
    ring_id: str,
    additional_metadata: Dict = None,
) -> None:
    # Add the ring_id to each of the generated training examples
    for d in plans_and_questions:
        d["ring_id"] = ring_id

    # Get a string containing the entities and attributes for the ring
    ring_ents_and_attrs = get_ring_ents_and_attrs_str(ring_id)

    final_output = {
        "metadata": build_metadata(plans_and_questions, ring_ents_and_attrs),
        "data": plans_and_questions,
    }

    if additional_metadata:
        final_output["metadata"].update(additional_metadata)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(final_output, indent=4))


def generate_data(
    ring_id: str,
    num_plans_per_base_plan_per_entity: int,
    num_retrieval_plans_per_entity: int,
    num_grouping_plans_per_entity: int,
    num_set_operation_plans_per_entity: int,
    num_in_operation_plans_per_entity: int,
    num_access_plans_per_attribute: int,
    filter_proportion: float,
    in_op_negate_proportion: float,
    retrieval_distinct_proportion: float,
    grouping_having_proportion: float,
    entities: List[str],
    base_plans: List[str],
    ignore_base_plans: List[str],
    output_directory: str,
    output_filename: str,
    save_intermediate_output: bool,
) -> None:
    # Store the input parameters for later output
    additional_metadata = {
        "input_params": {
            "ring_id": ring_id,
            "num_plans_per_base_plan_per_entity": num_plans_per_base_plan_per_entity,
            "num_retrieval_plans_per_entity": num_retrieval_plans_per_entity,
            "num_grouping_plans_per_entity": num_grouping_plans_per_entity,
            "num_access_plans_per_attribute": num_access_plans_per_attribute,
            "num_set_operation_plans_per_entity": num_set_operation_plans_per_entity,
            "num_in_operation_plans_per_entity": num_in_operation_plans_per_entity,
            "filter_proportion": filter_proportion,
            "in_op_negate_proportion": in_op_negate_proportion,
            "retireval_distinct_proportion": retrieval_distinct_proportion,
            "grouping_having_proportion": grouping_having_proportion,
            "entities": entities,
            "base_plans": base_plans,
            "ignore_base_plans": ignore_base_plans,
        }
    }

    # Make a new directory where all of the intermediate and final data will be saved
    if not output_directory:
        output_directory = get_and_make_default_output_directory()

    # Init the list where all the generated questions and plans will be stored
    plans_and_questions = []

    # Make the API call to generate plans from the access plans
    print("Generating data using the access plans...")
    plans_and_questions.extend(
        generate_data_with_access_plans(
            ring_id, entities, num_access_plans_per_attribute, filter_proportion
        )
    )
    msg.good("Finished generating data using the access plans.")
    if save_intermediate_output:
        save_path = os.path.join(output_directory, "access_plans.json")
        save_data(
            plans_and_questions,
            save_path,
            ring_id,
            additional_metadata=additional_metadata,
        )

    # Generate the initial set of plans (multiple API calls)
    print("Generating data using the base plans...")
    plans_and_questions.extend(
        generate_data_with_base_plans(
            ring_id,
            num_plans_per_base_plan_per_entity,
            filter_proportion,
            entities,
            base_plans,
            ignore_base_plans,
        )
    )
    msg.good("Finished generating data using the base plans.")
    if save_intermediate_output:
        save_path = os.path.join(
            output_directory, "access_plans_base_plans.json"
        )
        save_data(
            plans_and_questions,
            save_path,
            ring_id,
            additional_metadata=additional_metadata,
        )

    # Generate data that are retrieval plans
    print("Generating data using the retrieval plans...")
    plans_and_questions.extend(
        generate_data_with_retrieval_plans(
            ring_id,
            num_retrieval_plans_per_entity,
            filter_proportion,
            retrieval_distinct_proportion,
            entities,
        )
    )
    msg.good("Finished generating data using the retrieval plans.")
    if save_intermediate_output:
        save_path = os.path.join(
            output_directory, "access_plans_base_plans_retrieval_plans.json"
        )
        save_data(
            plans_and_questions,
            save_path,
            ring_id,
            additional_metadata=additional_metadata,
        )

    # Generate data that are grouping plans
    print("Generating data using the grouping plans...")
    plans_and_questions.extend(
        generate_data_with_grouping_plans(
            ring_id,
            num_grouping_plans_per_entity,
            filter_proportion,
            grouping_having_proportion,
            entities,
        )
    )
    msg.good("Finished generating data using the grouping plans.")

    # Generate data that are set operation plans
    print("Generating data using the set operation plans...")
    plans_and_questions.extend(
        generate_data_with_set_operation_plans(
            ring_id,
            num_set_operation_plans_per_entity,
            filter_proportion,
            entities,
        )
    )
    msg.good("Finished generating data using the set operation plans.")

    # Generate data that are in operation plans
    print("Generating data using the in operation plans...")
    plans_and_questions.extend(
        generate_data_with_in_operation_plans(
            ring_id,
            num_set_operation_plans_per_entity,
            filter_proportion,
            in_op_negate_proportion,
            entities,
        )
    )
    msg.good("Finished generating data using the in operation plans.")

    if save_intermediate_output:
        save_path = os.path.join(
            output_directory,
            "access_plans_base_plans_retrieval_plans_grouping_plans.json",
        )
        save_data(
            plans_and_questions,
            save_path,
            ring_id,
            additional_metadata=additional_metadata,
        )

    # Augment the generated data with compiled SQR
    print("Compiling the SQR plans...")
    plans_and_questions = compile_plans(plans_and_questions)
    msg.good("Finished compiling the SQR plans.")
    if save_intermediate_output:
        save_path = os.path.join(
            output_directory,
            "access_plans_base_plans_retrieval_plans_grouping_plans_compiled.json",
        )
        save_data(
            plans_and_questions,
            save_path,
            ring_id,
            additional_metadata=additional_metadata,
        )

    # Augment the generated data with SQL based on the compiled SQR
    print("Generating corresponding SQL queries...")
    plans_and_questions = generate_sql(plans_and_questions, ring_id)
    msg.good("Finished generating corresponding SQL queries.")
    # TODO: Save this intermediate output (once the final steps are added)

    # TODO: Rephrase the questions (API call) (load in the file from the last step?)

    # TODO: Save this intermediate output

    # TODO: Filter out low similarity questions (API call)

    # TODO: Save this intermediate output

    # Save the final output data
    output_filename = (
        output_filename
        if output_filename
        else "access_plans_base_plans_retrieval_plans_grouping_plans_compiled_sql.json"
    )
    save_path = os.path.join(output_directory, output_filename)
    save_data(
        plans_and_questions,
        save_path,
        ring_id,
        additional_metadata=additional_metadata,
    )

    # Print out the full path to where the final data was stored
    print(f"Data generation finished. Final dataset saved to '{save_path}'.")

    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("ring_id", type=str)
    parser.add_argument("num_plans_per_base_plan_per_entity", type=int)
    parser.add_argument("num_retrieval_plans_per_ent", type=int)
    parser.add_argument("num_grouping_plans_per_ent", type=int)
    parser.add_argument("num_set_operation_plans_per_ent", type=int),
    parser.add_argument("num_in_operation_plans_per_ent", type=int),
    parser.add_argument("num_access_plans_per_attribute", type=int)
    parser.add_argument("filter_proportion", type=float)
    parser.add_argument("in_op_negate_proportion", type=float)
    parser.add_argument("--entities", nargs="*", default=[])
    parser.add_argument("--base_plans", nargs="*", default=[])
    parser.add_argument("--ignore_base_plans", nargs="*", default=[])
    parser.add_argument("--output_directory", default="")
    parser.add_argument("--output_filename", default="")
    parser.add_argument("--save_intermediate_output", action="store_false")

    # TODO: Add flags for whether to generate SQL, whether to rephrase, whether to filter out rephrased questions, whether to generate the answers for them (???)

    args = parser.parse_args()

    generate_data(
        args.ring_id,
        args.num_plans_per_base_plan_per_entity,
        args.num_retrieval_plans_per_ent,
        args.num_grouping_plans_per_ent,
        args.num_set_operation_plans_per_ent,
        args.num_in_operation_plans_per_ent,
        args.num_access_plans_per_attribute,
        args.filter_proportion,
        args.in_op_negate_proportion,
        args.entities,
        args.base_plans,
        args.ignore_base_plans,
        args.output_directory,
        args.output_filename,
        args.save_intermediate_output,
    )
