#####################################################################################
# Usage Example:
#       python rephrase_with_gpt.py /full/path/to/benchmark/ --simplify
#
#   This example rephrases the questions using only the "simplify" rephrasing method.
#
# Assumptions:
#   - The input directory is the benchmark dataset containing a train, dev, and
#     test subdirectory. Each of these should have the output JSON files from
#     the generate_benchmark_dataset.py script.
#####################################################################################

import os
import json
import argparse
import datetime
from enum import Enum
from typing import List

from tqdm import tqdm
from wasabi import msg
from openai import OpenAI

class RephrasingMethod(Enum):
    SIMPLIFY = 1
    HIDE_DETAILS = 2
    SYNONYMS = 3
    SUBSTITUTIONS = 4
    EXPRESS_DIFF = 5
    FEW_SHOT = 6
    PARAPHRASE = 7

class PromptBuilder:
    def __init__(self):
        pass

    @staticmethod
    def make_prompt(question: str,
                    method: RephrasingMethod) -> str:
        """
        Creates the prompt for a given question using the specified rephrasing method.
        Prompts taken from Table 6 in Saparina and Lapata 2024 (https://arxiv.org/pdf/2402.08666)
        """
        if method == RephrasingMethod.SIMPLIFY:
            return f"""Simplify the following sentence: {question}"""
        elif method == RephrasingMethod.HIDE_DETAILS:
            return f"""Simplify the sentence by hiding unnecessary details that do not change the meaning: {question}"""
        elif method == RephrasingMethod.SYNONYMS:
            return f"""Simplify the following sentence using synonyms: {question}"""
        elif method == RephrasingMethod.SUBSTITUTIONS:
            return f"""Make the sentence simpler by substituting some words in {question}"""
        elif method == RephrasingMethod.EXPRESS_DIFF:
            return f"""What is a different way of expressing this question: {question}"""
        elif method == RephrasingMethod.FEW_SHOT:
            return f"""Examples of the question simplification:\n
                        Original: Find the names of stadiums whose capacity is smaller than the average capacity.\n
                        Simplified: Which stadiums are smaller than the average?\n
                        Original: Show the fleet series of aircraft flown by pilots younger than 34.\n
                        Simplified: Return the fleet series of the planes whose captains are younger than 34.\n
                        Original: Which cities have the largest population?\n
                        Simplified: Where do most people live?\n
                        Original: In which year was most of the ships built?\n
                        Simplified: When were most of the ships constructed?\n
                        Original: Tell me the number of orders with "Second time" as the order detail.\n
                        Simplified: How many orders have "Second time" as an order detail?\n
                        Original: {question}\n
                        Simplified: """
        elif method == RephrasingMethod.PARAPHRASE:
            return f"""Give me a paraphrase of the following question: {question}"""
        else:
            raise ValueError(f"No prompt implemented for method: '{method.name}'")

# Define globals
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_CLIENT = OpenAI(api_key=OPENAI_API_KEY)
GENERATION_ROOT_DIR = ""

def generate_with_llm(prompt: str,
                      temp: float = 0.0,
                      max_tokens: int = 1024,
                      response_format_type: str = 'text') -> str:
    response = OPENAI_CLIENT.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temp,
        response_format={"type": response_format_type})

    message_content = response.choices[0].message.content

    # Clean up the string
    message_content = message_content.strip()

    return message_content

def rephrase_single_question(q: str,
                             method: RephrasingMethod) -> str:
    prompt = PromptBuilder.make_prompt(q, method)
    output = generate_with_llm(prompt, temp=0.2)
    return output

def rephrase_questions(input_file_path: str,
                       output_file_path: str,
                       rephrasing_methods: List[RephrasingMethod]):
    # Read the json file containing the examples
    with open(input_file_path, encoding="utf-8") as f:
        data = json.load(f)

    # Rephrase the questions
    print(f"Beginning rephrasing for {input_file_path}")
    for d in tqdm(data['data']):
        rephrased_questions = []
        for q in d['questions']:
            for m in rephrasing_methods:
                try:
                    rephrased_questions.append(rephrase_single_question(q, m))
                except Exception as e:
                    print(f"Error when rephrasing the question '{q}'")
        d['rephrased_questions'] = [{"question": rq, "similarity": None} for rq in rephrased_questions]

    # Save the updated JSON dictionary with all the examples and the rephrased questions
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(data, indent=4))

    msg.good(f"Finished rephrasing for {input_file_path}")

def get_json_files(directory: str):
    # List all files in the directory
    files = os.listdir(directory)

    # Filter the list to include only .json files
    json_files = [f for f in files if f.endswith('.json')]

    return json_files

def main(benchmark_directory: str,
         simplify: bool,
         hide_details: bool,
         synonyms: bool,
         substitutions: bool,
         express_diff: bool,
         few_shot: bool,
         paraphrase: bool):

    # Determine the rephrasing methods to use
    rephrasing_methods_to_use = []
    if simplify:
        rephrasing_methods_to_use.append(RephrasingMethod.SIMPLIFY)
    if hide_details:
        rephrasing_methods_to_use.append(RephrasingMethod.HIDE_DETAILS)
    if synonyms:
        rephrasing_methods_to_use.append(RephrasingMethod.SYNONYMS)
    if substitutions:
        rephrasing_methods_to_use.append(RephrasingMethod.SUBSTITUTIONS)
    if express_diff:
        rephrasing_methods_to_use.append(RephrasingMethod.EXPRESS_DIFF)
    if few_shot:
        rephrasing_methods_to_use.append(RephrasingMethod.FEW_SHOT)
    if paraphrase:
        rephrasing_methods_to_use.append(RephrasingMethod.PARAPHRASE)

    # Ensure there is at least one rephrasing method specified to use
    if not rephrasing_methods_to_use:
        raise ValueError("No rephrasing methods specified. Please specify at least one.")

    INPUT_DIRS = {
        "train": os.path.join(benchmark_directory, "train"),
        "dev": os.path.join(benchmark_directory, "dev"),
        "test": os.path.join(benchmark_directory, "test")
    }

    # Make the base directory to store all of the outputs
    ts = str(datetime.datetime.now()).replace(" ", "_")
    output_dir_name = f"rephrased_dataset_{ts}"
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

    train_files = get_json_files(INPUT_DIRS["train"])
    dev_files = get_json_files(INPUT_DIRS["dev"])
    test_files = get_json_files(INPUT_DIRS["test"])

    # Rephrase the train set questions
    for file_name in train_files:
        rephrase_questions(os.path.join(INPUT_DIRS["train"], file_name), os.path.join(OUTPUT_DIRS["train"], file_name), rephrasing_methods_to_use)

    # Rephrase the dev set questions
    for file_name in dev_files:
        rephrase_questions(os.path.join(INPUT_DIRS["dev"], file_name), os.path.join(OUTPUT_DIRS["dev"], file_name), rephrasing_methods_to_use)

    # Rephrase the test set questions
    for file_name in test_files:
        rephrase_questions(os.path.join(INPUT_DIRS["test"], file_name), os.path.join(OUTPUT_DIRS["test"], file_name), rephrasing_methods_to_use)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("benchmark_directory", type=str)

    # Rephrasing method flags
    parser.add_argument("--simplify", action="store_true")
    parser.add_argument("--hide_details", action="store_true")
    parser.add_argument("--synonyms", action="store_true")
    parser.add_argument("--substitutions", action="store_true")
    parser.add_argument("--express_diff", action="store_true")
    parser.add_argument("--few_shot", action="store_true")
    parser.add_argument("--paraphrase", action="store_true")

    args = parser.parse_args()

    main(args.benchmark_directory,
         args.simplify,
         args.hide_details,
         args.synonyms,
         args.substitutions,
         args.express_diff,
         args.few_shot,
         args.paraphrase)
