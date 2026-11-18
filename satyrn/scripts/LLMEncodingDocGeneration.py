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

import json
import uuid
from typing import List, Dict

from tqdm import tqdm
from satyrn.core.LanguageGeneration.GPT4Interface import GPT4Interface

implicit_prompts_with_errors = []
explicit_prompts_with_errors = []
other_prompts_with_errors = []

def generate_records(prompts: List[str],
                     prompt_type: str) -> List[Dict]:
    # Init a list to store the records
    records = []

    generation_temperature = 0.0
    model_interface = GPT4Interface()
    model_name = 'gpt-4'
    for p in tqdm(prompts):
        try:
            # Gather and generate all necessary info
            record = {}
            record["report_id"] = str(uuid.uuid4())
            record["prompt"] = p
            record["temperature"] = generation_temperature
            record["model"] = model_name
            record["prompt_type"] = prompt_type
            # record["report"] = "REPORT"
            record["report"] = model_interface.generate(p, generation_temperature) # TODO: Uncomment this when not testing
            record["statements"] = {}  # This will ultimately contain things like "is_claim", "info_in_claim"

            # Save the record
            records.append(record)
        except Exception as e:
            if prompt_type == "implicit":
                implicit_prompts_with_errors.append(p)
            elif prompts == "explicit":
                explicit_prompts_with_errors.append(p)
            else:
                other_prompts_with_errors.append(p)
            print(f"error with prompt: {p}")

    return records

def main():
    # Init the report types and prompt templates
    report_types = [
        "biography of a fictional actor",
        "biography of a fictional politician",
        "biography of a fictional academic",
        "biography of a fictional company or organization",
        "biography of a fictional athlete",

        "summary of a patient stay at a hospital",
        "summary of political contributions for a political party",
        "summary of fundraising performance for a politician",
        "analysis of the correlation between academic expenditures and student performance",
        "summary of air quality and pollutants for a city",

        "performance report for a salesperson",
        "performance report for a doctor",
        "performance report for a business",
        "performance report for a community of businesses",
        "progress report for an individual student",

        "national housing price trends report",
        "housing price trends for a metropolitan region",
        "academic performance trends for an individual student",
        "wildfire occurrence trends in the United States",
        "air quality trends for a county in the United States",

        "housing price comparison report for two metropolitan regions",
        "report comparing the air quality comparison for two counties",
        "report comparing the statistics associated with the usage of handguns vs rifles used in school shootings",
        "report comparing two judges",
        "report comparing the poverty levels of two counties"
    ]

    implicit_prompt_templates = [
        "Generate a 500 word <report>.",
        "Within 500 words, please write a <report>.",
        "Please write a 500 word <report>.",
        "Give me a <report> using a maximum of 500 words.",
        "Please compose a <report>. Limit the report to 500 words.",
    ]

    explicit_prompt_templates = [
        "Tell me what information you need to generate a <report>.",
        "What facts or other information would you need to produce a <report>?",
        "How do I write a <report>?",
        "Can you provide the structure and types of information needed to write a <report>?",
        "If I were going to write a <report>, how would I do that?",
    ]

    # Generate the prompts
    implicit_prompts = [t.replace("<report>", report) for report in report_types for t in implicit_prompt_templates]
    # explicit_prompts = [t.replace("<report>", report) for report in report_types for t in explicit_prompt_templates]

    # Generate the reports
    implicit_records = generate_records(implicit_prompts, "implicit")
    # explicit_records = generate_records(explicit_prompts, "explicit")
    print(f"Generated {len(implicit_records)} implicit records.")
    # print(f"Generated {len(explicit_records)} explicit records.")

    # Print any prompts for which there were errors
    print("IMPLICIT PROMPTS WITH ERRORS")
    print(implicit_prompts_with_errors)
    print("EXPLICIT PROMPTS WITH ERRORS")
    print(explicit_prompts_with_errors)
    print("OTHER PROMPTS WITH ERRORS")
    print(other_prompts_with_errors)

    # Write out the implicit records
    with open("implicit_llm_encoding_reports.json", "w") as outfile:
        outfile.write(json.dumps(implicit_records, ensure_ascii=False, indent=4))

    # Write out the explicit records
    # with open("explicit_llm_encoding_reports.json", "w") as outfile:
    #     outfile.write(json.dumps(explicit_records, ensure_ascii=False, indent=4))

if __name__ == '__main__':
    main()
