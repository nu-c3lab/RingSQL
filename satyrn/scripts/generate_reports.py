



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
    
    python generate_reports.py [<report_type> | all]
    
    - Run it from this directory (files are saved using paths relative to the scripts directory)
    - Ensure you have the Satyrn-API server running 
'''

import csv
import uuid
import json
import requests
import argparse
from typing import List

headers = {"x-api-key": "test_api_key"}

def make_results_url(url, ringid, versionid, entity, urltype):
    return f"{url}api/{urltype}/{ringid}/{versionid}/"

def generate_documents(document_types: List[str]):

    # Init the dictionary of entity instances
    report_info = {
        "AQIAndWildfireTrendsForCountyReport": {
            "ring_id": "Toxic-3418-r4hu-4289-38jd93k29s",
            "ring_name": "Air_Quality",
            "entity_name": "AQI",
            "filter_attribute_name": "county_state",
            "filter_values": [
                "Wicomico, Maryland",           # 4295 tokens
                "Cook, Illinois",               # 5827 tokens
                "Power, Idaho",                 # 6083 tokens
                "Ford, Kansas",                 # 6508 tokens
                "Carter, Missouri"              # 4810 tokens
            ]
        },
        "StateWildfireReport": {
            "ring_id": "Toxic-3418-r4hu-4289-38jd93k29s",
            "ring_name": "Air_Quality",
            "entity_name": "Wildfire",
            "filter_attribute_name": "state_name",
            "filter_values": [
                "California",       # 6994 tokens
                "Illinois",         # 6965 tokens
                "Oregon",           # 6994 tokens
                "Idaho",            # 6993 tokens
                "Washington"        # 6992 tokens
            ]
        },
        "CountyHighSchoolReportCard": {
            "ring_id": "education-1467-4a02-8785-ec251e78d5be",
            "ring_name": "education_ring",
            "entity_name": "School",
            "filter_attribute_name": "county",
            "filter_values": [
                "Dupage",       # 961 tokens
                "Cook",         # 860 tokens
                "Montgomery",   # 1007 tokens
                "Boone",        # 1069 tokens
                "Adams"         # 961 tokens
            ]
        },
        "HighSchoolExpenditureAndPerformanceReport": {
            "ring_id": "education-1467-4a02-8785-ec251e78d5be",
            "ring_name": "education_ring",
            "entity_name": "School",
            "filter_attribute_name": "school_name",
            "filter_values": [
                "Schaumburg High School",           # 1032 tokens
                "Reavis High School",               # 974 tokens
                "Pleasant Hill High School",        # 917 tokens
                "Naperville Central High School",   # 925 tokens
                "Naperville North High School"      # 1046 tokens
            ]
        },
        "StayReport": {
            "ring_id": "mimic9f2-1467-4a02-8785-ec251e78d5be",
            "ring_name": "MimicData",
            "entity_name": "EDstay",
            "filter_attribute_name": "stay_id",
            "filter_values": [
                34391979,       # ??? tokens
                37401157,       # 1096 tokens
                39054681,       # 1691 tokens
                31945330,       # 1687 tokens
                32095131        # 2215 tokens
            ]
        },
        "SubjectReport": {
            "ring_id": "mimic9f2-1467-4a02-8785-ec251e78d5be",
            "ring_name": "MimicData",
            "entity_name": "Subject",
            "filter_attribute_name": "id",
            "filter_values": [
                10026406,       # 980 tokens
                10002930,       # 1942 tokens
                10002428,       # 1726 tokens
                10023239,       # 1759 tokens
                10000032        # 1439  tokens
            ]
        },
        "CaseSummary": {
            "ring_id": "SCALES-1467-4a02-8785-ec251e78d5be",
            "ring_name": "scales",
            "entity_name": "Case",
            "filter_attribute_name": "ucid",
            "filter_values": [
                "dcd;;1:16-cv-00027",
                "ncmd;;1:16-cv-00027",
                "ncwd;;1:16-cv-00027",
                "vawd;;1:16-cv-00027",
                "wvnd;;1:16-cv-00027"
            ]
        },
        "JudgeSummary": {
            "ring_id": "SCALES-1467-4a02-8785-ec251e78d5be",
            "ring_name": "scales",
            "entity_name": "Judge",
            "filter_attribute_name": "name",
            "filter_values": [
                "alan cooke kay",
                "reggie b walton",
                "deborah a robinson",
                "colleen kollar-kotelly",
                "rosemary m collyer"
            ]
        },
        "AllIncidentsReport": {
            "ring_id": "GunsRBad-1467-4a02-8785-ec251e78d5be",
            "ring_name": "SchoolShooting",
            "entity_name": "Incident",
            "filter_attribute_name": None,
            "filter_values": [None]             # 1618 tokens
        },
        "HandgunVsRifleReport": {
            "ring_id": "GunsRBad-1467-4a02-8785-ec251e78d5be",
            "ring_name": "SchoolShooting",
            "entity_name": "Weapon",
            "filter_attribute_name": None,
            "filter_values": [None]             # 639 tokens
        },
        "SingleIncidentReport": {
            "ring_id": "GunsRBad-1467-4a02-8785-ec251e78d5be",
            "ring_name": "SchoolShooting",
            "entity_name": "Incident",
            "filter_attribute_name": "incident_id",
            "filter_values": [
                "20220307IAEAD",        # 1187 tokens
                "20200924CAWAC",        # 943 tokens
                "20200923PAWIW",        # 828 tokens
                "20200923FLHIJ",        # 921 tokens
                "20200921CAPLP"         # 749 tokens
            ]
        },
        "CountyIncomeTrendsReport": {
            "ring_id": "money-1467-4a02-8785-ec251e78d5be",
            "ring_name": "income disparity",
            "entity_name": "Illinois",
            "filter_attribute_name": "county",
            "filter_values": [
                "Cook County",          # 5040 tokens
                "DuPage County",        # 4181 tokens
                "Champaign County",     # 4181 tokens
                "Wayne County",         # 5040 tokens
                "McHenry County"        # 4181 tokens
            ]
        },
        "CountyPovertyTrendsReport": {
            "ring_id": "money-1467-4a02-8785-ec251e78d5be",
            "ring_name": "income disparity",
            "entity_name": "Illinois",
            "filter_attribute_name": "county",
            "filter_values": [
                "Cook County",              # 6090 tokens
                "DuPage County",            # 6473 tokens
                "Champaign County",         # 6473 tokens
                "Wayne County",             # 5977 tokens
                "McHenry County"            # 6473 tokens
            ]
        },
        "BusinessPerformanceReport": {
            "ring_id": "dcac39f2-1467-4a02-8785-ec251e78d5be",
            "ring_name": "YELP",
            "entity_name": "Business",
            "filter_attribute_name": "business_id",
            "filter_values": [
                "VrGxoSNZfSiT-G4OqRRGIw",
                "H0NEOp4e3Zu598u6kO3y0g",
                "sB45WFgysT617bKWP_WJwA",
                "Fk1xpM7fjqEJ4paqk5ZFSg",
                "4dVrWc4Nhuw9apfk9BWEcA"
            ]
        },
        "CommunityPerformanceReport": {
            "ring_id": "dcac39f2-1467-4a02-8785-ec251e78d5be",
            "ring_name": "YELP",
            "entity_name": "Business",
            "filter_attribute_name": "city",
            "filter_values": [
                "Philadelphia",
                "Reno",
                "Indianapolis",
                "Boise",
                "New Orleans"
            ]
        },
        "NationalRentTrendsReport": {
            "ring_id": "Zillow8-1467-4a02-8785-ec251e78d5be",
            "ring_name": "ZillowRent",
            "entity_name": None,
            "filter_attribute_name": None,
            "filter_values": [None]         # 1437 tokens
        },
        "RegionRentReport": {
            "ring_id": "Zillow8-1467-4a02-8785-ec251e78d5be",
            "ring_name": "ZillowRent",
            "entity_name": "RegionInformation",
            "filter_attribute_name": "region_id",
            "filter_values": [
                394913,         # 4319 tokens
                753899,         # 4314 tokens
                394463,         # 4328 tokens
                394514,         # 4328 tokens
                395057          # 4318 tokens
            ]
        }
    }

    # Parse through the document types to determine which ones to generate
    if 'all' in document_types:
        document_types = list(report_info.keys())
    else:
        document_types = [doc_type for doc_type in document_types if doc_type in report_info]

    report_generation_modes = ['per_plan', 'per_row'] # Options: {'per_plan', 'per_row'}
    report_model_types = ['StableBelugaInterface'] #  Options: {'GPT4Interface', 'GPT35Interface', 'StableBelugaInterface'}
    for doc_type in document_types:
        # Get the stored info needed to generate the reports for this doc_type
        doc_info = report_info[doc_type]

        # Generate report using the various model types:
        for model_type in report_model_types:

            # Generate reports using the various generation modes
            for generation_mode in report_generation_modes:

                # Iterate over the entity instances to generate the reports
                for filter_value in doc_info['filter_values']:
                    # Build the entity dict required by the Document object
                    instance = {
                        "report_type": doc_type,
                        "entity_name": doc_info["entity_name"],
                        "filter_attribute_name": doc_info["filter_attribute_name"],
                        "filter_value": filter_value,
                        "generation_mode": generation_mode,
                        "model": model_type
                    }

                    # Make the API call to get the plans and facts
                    plans_and_facts_url = make_results_url("http://127.0.0.1:5000/", doc_info["ring_id"], 1, None, "plans_and_facts")
                    resp = requests.get(plans_and_facts_url, headers=headers, json=instance)
                    plans_and_facts_json = json.loads(resp.content.decode('utf-8'))

                    # Make the API call to generate the report
                    report_generation_url = make_results_url("http://127.0.0.1:5000/", doc_info["ring_id"], 1, None, "report_from_prompt")
                    prompt_dict = {"prompt": plans_and_facts_json["prompt"], "model": model_type}
                    resp = requests.get(report_generation_url, headers=headers, json=prompt_dict)
                    report = resp.content.decode('utf-8')
                    print(report)

                    # Write out a CSV file for each of the reports
                    csv_header = ['report_id', 'report_type', 'entity_name', 'filter_attribute_name', 'filter_value', 'ring_id', 'ring_name', 'generation_mode', 'prompt', 'model_type', 'report', 'claims', 'class']
                    csv_data = [
                        [str(uuid.uuid4()), doc_type, instance['entity_name'], instance['filter_attribute_name'], instance['filter_value'], doc_info['ring_id'], doc_info['ring_name'],
                         generation_mode, plans_and_facts_json['prompt'], model_type, report, '', '']
                    ]

                    csv_file_path = f'generated_documents/{doc_type}_{filter_value}_{model_type}_{generation_mode}.csv'
                    with open(csv_file_path, 'w', encoding='UTF8', newline='') as f:
                        writer = csv.writer(f)

                        # Write the header
                        writer.writerow(csv_header)

                        # Write the data
                        writer.writerows(csv_data)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Generate documents.')
    parser.add_argument('doc_types', type=str, nargs='+', help='the document type(s) to generate. Use "all" to generate all documents types at once.')
    args = parser.parse_args()

    generate_documents(args.doc_types)

