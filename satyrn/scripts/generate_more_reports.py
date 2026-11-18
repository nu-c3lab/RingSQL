



'''
This file is part of Satyrn.
Satyrn is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software Foundation,
either version 3 of the License, or (at your option) any later version.
Satyrn is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with Satyrn.
If not, see <https://www.gnu.org/licenses/>.
'''

'''
Running this script
    
    python generate_more_reports.py [<rind_id> | all]
    
    - Run it from this directory (files are saved using paths relative to the scripts directory)
    - Ensure you have the Satyrn-API server running 
'''

import csv
import uuid
import json
import requests
import argparse
from itertools import product
from typing import List
import spacy

def make_results_url(url, ringid, versionid, urltype):
    return f"{url}api/{urltype}/{ringid}/{versionid}/"

def generate_documents(report_model_types : List[str]):

    # Init the dictionary of entity instances
    with open('generation_parameter_configurations_mini.json', 'r') as f:
        configurations = json.load(f)

    nlp = spacy.load('en_core_web_sm')

    domains = {
        # 'environmental_sustainability': 'Toxic-3418-r4hu-4289-38jd93k29s',
        # 'education': 'education-1467-4a02-8785-ec251e78d5be',
        # 'socioeconomics': 'money-1467-4a02-8785-ec251e78d5be',
        # 'healthcare': 'mimic9f2-1467-4a02-8785-ec251e78d5be',
        # 'legal_and_judicial': 'SCALES-1467-4a02-8785-ec251e78d5be',
        # 'criminal_justice': 'shooting-1467-4a02-8785-ec251e78d5be',
        # 'business': 'dcac39f2-1467-4a02-8785-ec251e78d5be',
        'urban_housing': 'Zillow8-1467-4a02-8785-ec251e78d5be'
    }

    report_types = [
        'RankingBlueprint',
        'ComparativeBenchmarkBlueprint',
        'TimeOverTimeBlueprint'
    ]
    statement_generation_methods = [
        # 'recursive',
        'template',
        'table'
    ]
    prompt_types = [
        # 'baseline',
        # 'baseline_with_reqs',
        'baseline_with_facts'
    ]

    # Parse through the document types to determine which ones to generate
    if 'all' in report_model_types:
        report_model_types = [
            "gpt3.5",
            "gpt4",
            "mistral",
            "mixtral",
            "code_interpreter",
            "none"
        ]

    for domain, report_type, generation_method, prompt_type, report_model in product(domains, report_types, statement_generation_methods, prompt_types, report_model_types):
        if report_model == 'code_interpreter' and prompt_type != 'baseline_with_reqs':
            continue

        for instance in configurations[domain]:
            request = {**instance, 'report_type': report_type, 'statement_generation_method': generation_method, 'prompt_type': prompt_type, 'llm': report_model}
            if report_type == 'TimeOverTimeBlueprint' and not request['time_attribute_name']:
                continue

            print(f'Generating reports for configuration: {domain} | {report_type} | {generation_method} | {prompt_type} | {report_model}')

            # Make the API call to generate the report
            report_generation_url = make_results_url("http://127.0.0.1:5000/", domains[domain], 1, "imp_plan")
            resp = requests.get(report_generation_url, json=request)
            report = json.loads(resp.content.decode('utf-8'))
            print(report)
            report_sents = list(nlp(report['report']).sents)

            # Write out a CSV file for each of the reports
            csv_header = ['report_id', 'report_type', 'entity_name', 'filter_attribute_name', 'filter_value', 'domain', 'generation_method', 'prompt_type', 'prompt', 'model_type', 'report', 'claims', 'class']
            uid = str(uuid.uuid4())
            csv_data = [
                [
                    uid,
                    report_type,
                    instance['entity_name'],
                    instance['entity_instance_identifier_attribute_name'],
                    instance['entity_instance_identifier_value'],
                    domains[domain],
                    generation_method,
                    prompt_type,
                    report['prompt'],
                    report_model,
                    report_sents[0],
                    '',
                    ''
                ],
                *[['','','','','','','','','','', report_sent, '', ''] for report_sent in report_sents[1:]]
            ]

            csv_file_path = f"generated_documents/{domain}_{report_type}_{instance['entity_name']}_{instance['entity_instance_identifier_value']}_{report_model}_{generation_method}_{uid}.csv"
            with open(csv_file_path, 'w', encoding='UTF8', newline='') as f:
                writer = csv.writer(f)

                # Write the header
                writer.writerow(csv_header)

                # Write the data
                writer.writerows(csv_data)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Generate documents.')
    parser.add_argument('model_types', type=str, nargs='+', help='The rind ids for which to generate documents. Use "all" to generate documents for all rings.')
    args = parser.parse_args()

    generate_documents(args.model_types)

