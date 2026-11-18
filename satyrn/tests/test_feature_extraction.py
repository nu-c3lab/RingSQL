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
import unittest

import os

import requests

from helper_func import make_results_url
import json


class TestAnalysis(unittest.TestCase):

    def setUp(self):
        self.apikey = os.environ.get("API_KEY", "thisisatestkey")
        self.url = os.environ.get("TEST_URL", "http://127.0.0.1:5000/")
        self.ringids = {
            "MIMIC": "mimic9f2-1467-4a02-8785-ec251e78d5be",
            "zillow_rent": "Zillow8-1467-4a02-8785-ec251e78d5be",
            "air_quality": "Toxic-3418-r4hu-4289-38jd93k29s",
            "income_disparity": "money-1467-4a02-8785-ec251e78d5be",
            "school_shooting": "GunsRBad-1467-4a02-8785-ec251e78d5be",
            "scales": "SCALES-1467-4a02-8785-ec251e78d5be",
            "yelp": "dcac39f2-1467-4a02-8785-ec251e78d5be",
            "education": "education-1467-4a02-8785-ec251e78d5be"
        }
        self.ringid = ""
        self.versionid = "1"
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": self.apikey
        }
        self.urltype = "extractor"

    # helper function to ignore case - not used
    # def assertDictEqualIgnoreCase(self, expected, actual):
    #     for key, value in expected.items():
    #         self.assertEqual(
    #             value.lower() if isinstance(value, str) else value,
    #             actual[key].lower() if isinstance(actual[key], str) else actual[key]
    #         )

    def test_MIMIC_feature_extraction(self):
        self.ringid = self.ringids["MIMIC"]
        urllink = make_results_url(url=self.url, ringid=self.ringid, versionid=self.versionid, entity="" , urltype=self.urltype, filters=None)
        prompts = [{"question": "Give me a stay report for the EDstay with the stay id 37202404."}, {"question": "Give me a subject report for the Subject with the id 10026406."}]
        expected_results = [
            {
                "entity": "EDstay",
                "filter_attribute": "stay_id",
                "filter_value": "37202404",
                "report_type": "StayReport",
                "request_type": "report"
            },
            {
                "entity": "Subject",
                "filter_attribute": "id",
                "filter_value": "10026406",
                "report_type": "SubjectReport",
                "request_type": "report"
            }
        ]
        # print(urllink)
        for i in range(len(prompts)):
            resp = requests.get(urllink, headers=self.headers, json=prompts[i])
            # print(resp.content.decode('utf-8'))
            results = json.loads(resp.content.decode('utf-8'))
            self.assertEqual(expected_results[i], results)

    def test_zillow_rent_feature_extraction(self):
        self.ringid = self.ringids["zillow_rent"]
        urllink = make_results_url(url=self.url, ringid=self.ringid, versionid=self.versionid, entity="", urltype=self.urltype, filters=None)
        prompts = [{"question": "Give me a rental price trend report for the region with id 192949."}, {"question": "Give me a national rental price trend report."}]
        expected_results = [
            {
                "entity": "RegionInformation",
                "filter_attribute": "region_id",
                "filter_value": "192949",
                "report_type": "PerformanceReview",
                "request_type": "report"
            },
            {
                "entity": "RegionInformation",
                "filter_attribute": "region_name",
                "filter_value": "national",
                "report_type": "PerformanceReview",
                "request_type": "report"
            }
        ]
        # print(urllink)
        for i in range(len(prompts)):
            resp = requests.get(urllink, headers=self.headers, json=prompts[i])
            # print(resp.content.decode('utf-8'))
            results = json.loads(resp.content.decode('utf-8'))
            self.assertEqual(expected_results[i], results)

    def test_school_shooting_feature_extraction(self):
        self.ringid = self.ringids["school_shooting"]
        urllink = make_results_url(url=self.url, ringid=self.ringid, versionid=self.versionid, entity="", urltype=self.urltype, filters=None)
        prompts = [{"question": "Give me a report about all school incidents."}, {"question": "Give me an incident report for the Incident with id 20220609ALWAG."}, {"question": "Give me a report comparing the usage of handguns and rifles in school shooting incidents."}, {"question": "Give me a report on weapons, specifically handguns and rifles in school shootings"}]
        expected_results = [
            {
                "entity": "Incident",
                "filter_attribute": "summary",
                "filter_value": "all school incidents.",
                "report_type": "PerformanceReview",
                "request_type": "report"
            },
            {
                "entity": "Incident",
                "filter_attribute": "incident_id",
                "filter_value": "20220609ALWAG",
                "report_type": "PerformanceReview",
                "request_type": "report"
            },
            {
                "entity": "Incident",
                "filter_attribute": "",
                "filter_value": "handguns",
                "report_type": "PerformanceReview",
                "request_type": "report"
            },
            {
                "entity": "Weapon",
                "filter_attribute": "weapon_type",
                "filter_value": "handguns",
                "report_type": "PerformanceReview",
                "request_type": "report"
            }
        ]
        # print(urllink)
        for i in range(len(prompts)):
            resp = requests.get(urllink, headers=self.headers, json=prompts[i])
            # print(resp.content.decode('utf-8'))
            results = json.loads(resp.content.decode('utf-8'))
            self.assertEqual(expected_results[i], results)

    def test_air_quality_feature_extraction(self):
        self.ringid = self.ringids["air_quality"]
        urllink = make_results_url(url=self.url, ringid=self.ringid, versionid=self.versionid, entity="", urltype=self.urltype, filters=None)
        prompts = [{"question": "Give me a report about wildfire occurrences in the state named California."}, {"question": "Give me a report about the yearly trends of air quality index and wildfire occurrence for the county and state of Cook County, IL."}]
        expected_results = [
            {
                "entity": "Wildfire",
                "filter_attribute": "state_name",
                "filter_value": "California",
                "report_type": "PerformanceReview",
                "request_type": "report"
            },
            {
                "entity": "AQI",
                "filter_attribute": "county_name",
                "filter_value": "Cook County",
                "report_type": "PerformanceReview",
                "request_type": "report"
            }
        ]
        # print(urllink)
        for i in range(len(prompts)):
            resp = requests.get(urllink, headers=self.headers, json=prompts[i])
            # print(resp.content.decode('utf-8'))
            results = json.loads(resp.content.decode('utf-8'))
            self.assertEqual(expected_results[i], results)

    def test_education_feature_extraction(self):
        self.ringid = self.ringids["education"]
        urllink = make_results_url(url=self.url, ringid=self.ringid, versionid=self.versionid, entity="", urltype=self.urltype, filters=None)
        prompts = [{"question": "Give me a report of how students are performing based on school expenditures for the school with rcdts 010010040262007."}, {"question": "Give me a report of how students are performing based on school expenditures in the county with rcdts 010010040262008."}]
        expected_results = [
            {
                "entity": "School",
                "filter_attribute": "rcdts",
                "filter_value": "010010040262007",
                "report_type": "PerformanceReview",
                "request_type": "report"
            },
            {
                "entity": "District",
                "filter_attribute": "rcdts",
                "filter_value": "010010040262008",
                "report_type": "PerformanceReview",
                "request_type": "report"
            }
        ]
        # print(urllink)
        for i in range(len(prompts)):
            resp = requests.get(urllink, headers=self.headers, json=prompts[i])
            # print(resp.content.decode('utf-8'))
            results = json.loads(resp.content.decode('utf-8'))
            self.assertEqual(expected_results[i], results)

    def test_scales_feature_extraction(self):
        self.ringid = self.ringids["scales"]
        urllink = make_results_url(url=self.url, ringid=self.ringid, versionid=self.versionid, entity="", urltype=self.urltype, filters=None)
        prompts = [{"question": "Give me a summary of the case with id 1:16-cr-00002."}, {"question": "Give me a report summarizing the case history for the judge with the name Tanya Sue Chutkan."}]
        expected_results = [
            {
                "entity": "Case",
                "filter_attribute": "case_id",
                "filter_value": "1:16-cr-00002",
                "report_type": "PerformanceReview",
                "request_type": "report"
            },
            {
                "entity": "Judge",
                "filter_attribute": "name",
                "filter_value": "Tanya Sue Chutkan",
                "report_type": "PerformanceReview",
                "request_type": "report"
            }
        ]
        # print(urllink)
        for i in range(len(prompts)):
            resp = requests.get(urllink, headers=self.headers, json=prompts[i])
            # print(resp.content.decode('utf-8'))
            results = json.loads(resp.content.decode('utf-8'))
            self.assertEqual(expected_results[i], results)

    def test_income_disparity_feature_extraction(self):
        self.ringid = self.ringids["income_disparity"]
        urllink = make_results_url(url=self.url, ringid=self.ringid, versionid=self.versionid, entity="", urltype=self.urltype, filters=None)
        prompts = [{"question": "Give me a report on the Illinois county level income trends for Cook county."}, {"question": "Give me a report on the Illinois county level income trends for Adams county."}]
        expected_results = [
            {
                "entity": "Illinois",
                "filter_attribute": "county",
                "filter_value": "Cook county",
                "report_type": "PerformanceReview",
                "request_type": "report"
            },
            {
                "entity": "Illinois",
                "filter_attribute": "county",
                "filter_value": "Adams county",
                "report_type": "PerformanceReview",
                "request_type": "report"
            }
        ]
        # print(urllink)
        for i in range(len(prompts)):
            resp = requests.get(urllink, headers=self.headers, json=prompts[i])
            # print(resp.content.decode('utf-8'))
            results = json.loads(resp.content.decode('utf-8'))
            self.assertEqual(expected_results[i], results)

    def test_yelp_feature_extraction(self):
        self.ringid = self.ringids["yelp"]
        urllink = make_results_url(url=self.url, ringid=self.ringid, versionid=self.versionid, entity="", urltype=self.urltype, filters=None)
        prompts = [{"question": "Give me a performance report for the business named Hampton Social."}, {"question": "Give me a report of how businesses are performing for the state named Michigan."}, {"question": "Give me a business report of the top 3 businesses in Chicago."}]
        expected_results = [
            {
                "entity": "Business",
                "filter_attribute": "business_name",
                "filter_value": "Hampton Social",
                "report_type": "PerformanceReview",
                "request_type": "report"
            },
            {
                "entity": "Business",
                "filter_attribute": "state",
                "filter_value": "Michigan",
                "report_type": "PerformanceReview",
                "request_type": "report"
            },
            {
                "entity": "Business",
                "filter_attribute": "city",
                "filter_value": "Chicago",
                "report_type": "PerformanceReview",
                "request_type": "report"
            }
        ]
        # print(urllink)
        for i in range(len(prompts)):
            resp = requests.get(urllink, headers=self.headers, json=prompts[i])
            # print(resp.content.decode('utf-8'))
            results = json.loads(resp.content.decode('utf-8'))
            self.assertEqual(expected_results[i], results)
if __name__ == '__main__':
    unittest.main()
