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

import os
import json
import requests
import unittest

from helper_func import make_results_url

class TestSQRComposition(unittest.TestCase):

    def setUp(self):

        self.apikey = os.environ.get("API_KEY", "thisisatestkey")
        self.url = os.environ.get("TEST_URL", "http://127.0.0.1:5000/")
        self.ringid = "Toxic-3418-r4hu-4289-38jd93k29s"
        self.versionid = "1"
        self.headers ={
            "x-api-key": self.apikey
        }
        self.maxDiff = None

    def test_metric_ranking_for_entity_instance(self):
        endpoint_info = {
            "access_plan": {
                "|1|": "(retrieve_entity Wildfire)",
                "|2|": "(retrieve_attribute |1| fire_size)",
                "|3|": "(retrieve_attribute |1| id)",
                "|4|": "(collect |2| |3|)",
                "|5|": "(return |4|)"
            },
            "base_plan": {
                "|1|": "(retrieve_attribute |A| {Identifier:0})",
                "|2|": "(retrieve_attribute |A| {Metric:0})",

                "|3|": "(sort |2| desc)",
                "|4|": "(rownum |3|)",
                "|5|": "(collect |4| |1|)",
                "|6|": "(return |5|)",

                "|7|": "(retrieve_attribute |6| |4|)",
                "|8|": "(retrieve_attribute |6| |1|)",
                "|9|": "(exact |8| {String:0})",
                "|10|": "(collect |7| |8|)",
                "|11|": "(return |10| |9|)"
            },
            "slot_fillers": {
                "String:0": "2284522"
            },
            "target_plan": {
                "|1A|": "(retrieve_entity Wildfire)",
                "|2A|": "(retrieve_attribute |1A| fire_size)",
                "|3A|": "(retrieve_attribute |1A| id)",
                "|4A|": "(collect |2A| |3A|)",
                "|5A|": "(return |4A|)",

                "|1|": "(retrieve_attribute |5A| |3A|)",
                "|2|": "(retrieve_attribute |5A| |2A|)",

                "|3|": "(sort |2| desc)",
                "|4|": "(rownum |3|)",
                "|5|": "(collect |4| |1|)",
                "|6|": "(return |5|)",

                "|7|": "(retrieve_attribute |6| |4|)",
                "|8|": "(retrieve_attribute |6| |1|)",
                "|9|": "(exact |8| {String:0})",
                "|10|": "(collect |7| |8|)",
                "|11|": "(return |10| |9|)"
            }
        }

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "unittest_sqr_compose", {})

        resp = requests.get(urllink, headers=self.headers, json=endpoint_info)
        results = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(results["target_plan_results"], results["composed_plan_results"])

    def test_metric_ranking_for_entity_instance_related_entity(self):
        endpoint_info = {
            "access_plan": {
                "|1|": "(retrieve_entity State)",
                "|2|": "(retrieve_entity Wildfire)",
                "|3|": "(retrieve_attribute |1| name)",
                "|4|": "(retrieve_attribute |2| fire_size)",
                "|5|": "(groupby |3|)",
                "|6|": "({Analysis:0} |4| |5|)",
                "|7|": "(collect |3| |6|)",
                "|8|": "(return |7|)",
            },
            "base_plan": {
                "|1|": "(retrieve_attribute |A| {Identifier:0})",
                "|2|": "(retrieve_attribute |A| {Metric:0})",

                "|3|": "(sort |2| desc)",
                "|4|": "(rownum |3|)",
                "|5|": "(collect |4| |1|)",
                "|6|": "(return |5|)",

                "|7|": "(retrieve_attribute |6| |4|)",
                "|8|": "(retrieve_attribute |6| |1|)",
                "|9|": "(exact |8| {String:0})",
                "|10|": "(collect |7| |8|)",
                "|11|": "(return |10| |9|)"
            },
            "slot_fillers": {
                "Analysis:0": "average",
                "String:0": "Idaho"
            },
            "target_plan": {
                "|1A|": "(retrieve_entity State)",
                "|2A|": "(retrieve_entity Wildfire)",
                "|3A|": "(retrieve_attribute |1A| name)",
                "|4A|": "(retrieve_attribute |2A| fire_size)",
                "|5A|": "(groupby |3A|)",
                "|6A|": "({Analysis:0} |4A| |5A|)",
                "|7A|": "(collect |3A| |6A|)",
                "|8A|": "(return |7A|)",

                "|1|": "(retrieve_attribute |8A| |3A|)",
                "|2|": "(retrieve_attribute |8A| |6A|)",

                "|3|": "(sort |2| desc)",
                "|4|": "(rownum |3|)",
                "|5|": "(collect |4| |1|)",
                "|6|": "(return |5|)",

                "|7|": "(retrieve_attribute |6| |4|)",
                "|8|": "(retrieve_attribute |6| |1|)",
                "|9|": "(exact |8| {String:0})",
                "|10|": "(collect |7| |8|)",
                "|11|": "(return |10| |9|)"
            }
        }

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "unittest_sqr_compose", {})

        resp = requests.get(urllink, headers=self.headers, json=endpoint_info)
        results = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(results["target_plan_results"], results["composed_plan_results"])

    def test_top_three_instances_for_metric(self):
        endpoint_info = {
            "access_plan": {
                "|1|": "(retrieve_entity Wildfire)",
                "|2|": "(retrieve_attribute |1| fire_size)",
                "|3|": "(retrieve_attribute |1| id)",
                "|4|": "(collect |2| |3|)",
                "|5|": "(return |4|)"
            },
            "base_plan": {
                "|1|": "(retrieve_attribute |A| {Identifier:0})",
                "|2|": "(retrieve_attribute |A| {Metric:0})",

                "|3|": "(collect |1| |2|)",
                "|4|": "(sort |2| desc)",
                "|5|": "(limit 3)",
                "|6|": "(return |3| |4| |5|)"
            },
            "slot_fillers": {},
            "target_plan": {
                "|1A|": "(retrieve_entity Wildfire)",
                "|2A|": "(retrieve_attribute |1A| fire_size)",
                "|3A|": "(retrieve_attribute |1A| id)",
                "|4A|": "(collect |2A| |3A|)",
                "|5A|": "(return |4A|)",

                "|1|": "(retrieve_attribute |5A| |3A|)",
                "|2|": "(retrieve_attribute |5A| |2A|)",

                "|3|": "(collect |1| |2|)",
                "|4|": "(sort |2| desc)",
                "|5|": "(limit 3)",
                "|6|": "(return |3| |4| |5|)"
            }
        }

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "unittest_sqr_compose", {})

        resp = requests.get(urllink, headers=self.headers, json=endpoint_info)
        results = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(results["target_plan_results"], results["composed_plan_results"])

    def test_top_three_instances_for_metric_related_entity(self):
        endpoint_info = {
            "access_plan": {
                "|1|": "(retrieve_entity State)",
                "|2|": "(retrieve_entity Wildfire)",
                "|3|": "(retrieve_attribute |1| name)",
                "|4|": "(retrieve_attribute |2| fire_size)",
                "|5|": "(groupby |3|)",
                "|6|": "({Analysis:0} |4| |5|)",
                "|7|": "(collect |3| |6|)",
                "|8|": "(return |7|)",
            },
            "base_plan": {
                "|1|": "(retrieve_attribute |A| {Identifier:0})",
                "|2|": "(retrieve_attribute |A| {Metric:0})",

                "|3|": "(collect |1| |2|)",
                "|4|": "(sort |2| desc)",
                "|5|": "(limit 3)",
                "|6|": "(return |3| |4| |5|)"
            },
            "slot_fillers": {
                "Analysis:0": "average",
            },
            "target_plan": {
                "|1A|": "(retrieve_entity State)",
                "|2A|": "(retrieve_entity Wildfire)",
                "|3A|": "(retrieve_attribute |1A| name)",
                "|4A|": "(retrieve_attribute |2A| fire_size)",
                "|5A|": "(groupby |3A|)",
                "|6A|": "({Analysis:0} |4A| |5A|)",
                "|7A|": "(collect |3A| |6A|)",
                "|8A|": "(return |7A|)",

                "|1|": "(retrieve_attribute |8A| |3A|)",
                "|2|": "(retrieve_attribute |8A| |6A|)",

                "|3|": "(collect |1| |2|)",
                "|4|": "(sort |2| desc)",
                "|5|": "(limit 3)",
                "|6|": "(return |3| |4| |5|)"
            }
        }

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "unittest_sqr_compose", {})

        resp = requests.get(urllink, headers=self.headers, json=endpoint_info)
        results = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(results["target_plan_results"], results["composed_plan_results"])

    def test_average_metric_for_entity_class(self):
        endpoint_info = {
            "access_plan": {
                "|1|": "(retrieve_entity Wildfire)",
                "|2|": "(retrieve_attribute |1| fire_size)",
                "|3|": "(collect |2|)",
                "|4|": "(return |3|)"
            },
            "base_plan": {
                "|1|": "(retrieve_attribute |A| {Metric:0})",
                "|2|": "({Analysis:0} |1|)",
                "|3|": "(collect |2|)",
                "|4|": "(return |3|)"
            },
            "slot_fillers": {
                "Analysis:0": "average"
            },
            "target_plan": {
                "|1|": "(retrieve_entity Wildfire)",
                "|2|": "(retrieve_attribute |1| fire_size)",
                "|3|": "(collect |2|)",
                "|4|": "(return |3|)",

                "|5|": "(retrieve_attribute |4| |2|)",
                "|6|": "({Analysis:0} |5|)",
                "|7|": "(collect |6|)",
                "|8|": "(return |7|)"
            }
        }

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "unittest_sqr_compose", {})

        resp = requests.get(urllink, headers=self.headers, json=endpoint_info)
        results = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(results["target_plan_results"], results["composed_plan_results"])

    def test_average_metric_for_entity_class_related_entity(self):
        endpoint_info = {
            "access_plan": {
                "|1|": "(retrieve_entity State)",
                "|2|": "(retrieve_entity Wildfire)",
                "|3|": "(retrieve_attribute |1| name)",
                "|4|": "(retrieve_attribute |2| fire_size)",
                "|5|": "(groupby |3|)",
                "|6|": "({Analysis:0} |4| |5|)",
                "|7|": "(collect |6|)",
                "|8|": "(return |7|)",
            },
            "base_plan": {
                "|1|": "(retrieve_attribute |A| {Metric:0})",
                "|2|": "({Analysis:0} |1|)",
                "|3|": "(collect |2|)",
                "|4|": "(return |3|)"
            },
            "slot_fillers": {
                "Analysis:0": "average",
                "Analysis:1": "average"
            },
            "target_plan": {
                "|1|": "(retrieve_entity State)",
                "|2|": "(retrieve_entity Wildfire)",
                "|3|": "(retrieve_attribute |1| name)",
                "|4|": "(retrieve_attribute |2| fire_size)",
                "|5|": "(groupby |3|)",
                "|6|": "({Analysis:0} |4| |5|)",
                "|7|": "(collect |6|)",
                "|8|": "(return |7|)",

                "|9|": "(retrieve_attribute |8| |6|)",
                "|10|": "({Analysis:1} |9|)",
                "|11|": "(collect |10|)",
                "|12|": "(return |11|)"
            }
        }

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "unittest_sqr_compose", {})

        resp = requests.get(urllink, headers=self.headers, json=endpoint_info)
        results = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(results["target_plan_results"], results["composed_plan_results"])

    def test_distance_from_max_metric(self):
        endpoint_info = {
            "access_plan": {
                "|1|": "(retrieve_entity Wildfire)",
                "|2|": "(retrieve_attribute |1| fire_size)",
                "|3|": "(retrieve_attribute |1| id)",
                "|4|": "(collect |2| |3|)",
                "|5|": "(return |4|)"
            },
            "base_plan": {
                "|1|": "(retrieve_attribute |A| {Metric:0})",
                "|2|": "(max |1|)",
                "|3|": "(collect |2|)",
                "|4|": "(return |3|)",

                "|5|": "(retrieve_attribute |A| {Identifier:0})",
                "|6|": "(retrieve_attribute |A| {Metric:0)})",
                "|7|": "(exact |5| \"{String:0}\")",
                "|8|": "(collect |5| |6|)",
                "|9|": "(return |8| |7|)",

                "|10|": "(retrieve_attribute |4| |2|)",
                "|11|": "(retrieve_attribute |9| |6|)",
                "|12|": "(subtract |10| |11|)",
                "|13|": "(collect |12|)",
                "|14|": "(return |13|)"
            },
            "slot_fillers": {
                "Analysis:0": "average",
                "String:0": "2284522"
            },
            "target_plan": {
                "|1A|": "(retrieve_entity Wildfire)",
                "|2A|": "(retrieve_attribute |1A| fire_size)",
                "|3A|": "(retrieve_attribute |1A| id)",
                "|4A|": "(collect |2A| |3A|)",
                "|5A|": "(return |4A|)",

                "|1|": "(retrieve_attribute |5A| |2A|)",
                "|2|": "(max |1|)",
                "|3|": "(collect |2|)",
                "|4|": "(return |3|)",

                "|5|": "(retrieve_attribute |5A| |3A|)",
                "|6|": "(retrieve_attribute |5A| |2A|)",
                "|7|": "(exact |5| \"{String:0}\")",
                "|8|": "(collect |5| |6|)",
                "|9|": "(return |8| |7|)",

                "|10|": "(retrieve_attribute |4| |2|)",
                "|11|": "(retrieve_attribute |9| |6|)",
                "|12|": "(subtract |10| |11|)",
                "|13|": "(collect |12|)",
                "|14|": "(return |13|)"
            }
        }

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "unittest_sqr_compose", {})

        resp = requests.get(urllink, headers=self.headers, json=endpoint_info)
        results = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(results["target_plan_results"], results["composed_plan_results"])

    def test_distance_from_max_metric_related_entity(self):
        endpoint_info = {
            "access_plan": {
                "|1|": "(retrieve_entity State)",
                "|2|": "(retrieve_entity Wildfire)",
                "|3|": "(retrieve_attribute |1| name)",
                "|4|": "(retrieve_attribute |2| fire_size)",
                "|5|": "(groupby |3|)",
                "|6|": "({Analysis:0} |4| |5|)",
                "|7|": "(collect |3| |6|)",
                "|8|": "(return |7|)",
            },
            "base_plan": {
                "|1|": "(retrieve_attribute |A| {Metric:0})",
                "|2|": "(max |1|)",
                "|3|": "(collect |2|)",
                "|4|": "(return |3|)",

                "|5|": "(retrieve_attribute |A| {Identifier:0})",
                "|6|": "(retrieve_attribute |A| {Metric:0)})",
                "|7|": "(exact |5| \"{String:0}\")",
                "|8|": "(collect |5| |6|)",
                "|9|": "(return |8| |7|)",

                "|10|": "(retrieve_attribute |4| |2|)",
                "|11|": "(retrieve_attribute |9| |6|)",
                "|12|": "(subtract |10| |11|)",
                "|13|": "(collect |12|)",
                "|14|": "(return |13|)"
            },
            "slot_fillers": {
                "Analysis:0": "average",
                "String:0": "California"
            },
            "target_plan": {
                "|1A|": "(retrieve_entity State)",
                "|2A|": "(retrieve_entity Wildfire)",
                "|3A|": "(retrieve_attribute |1A| name)",
                "|4A|": "(retrieve_attribute |2A| fire_size)",
                "|5A|": "(groupby |3A|)",
                "|6A|": "({Analysis:0} |4A| |5A|)",
                "|7A|": "(collect |3A| |6A|)",
                "|8A|": "(return |7A|)",

                "|1|": "(retrieve_attribute |8A| |6A|)",
                "|2|": "(max |1|)",
                "|3|": "(collect |2|)",
                "|4|": "(return |3|)",

                "|5|": "(retrieve_attribute |8A| |3A|)",
                "|6|": "(retrieve_attribute |8A| |6A|)",
                "|7|": "(exact |5| \"{String:0}\")",
                "|8|": "(collect |5| |6|)",
                "|9|": "(return |8| |7|)",

                "|10|": "(retrieve_attribute |4| |2|)",
                "|11|": "(retrieve_attribute |9| |6|)",
                "|12|": "(subtract |10| |11|)",
                "|13|": "(collect |12|)",
                "|14|": "(return |13|)"
            }
        }

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "unittest_sqr_compose", {})

        resp = requests.get(urllink, headers=self.headers, json=endpoint_info)
        results = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(results["target_plan_results"], results["composed_plan_results"])

    def test_is_instance_greater_than_average(self):
        endpoint_info = {
            "access_plan": {
                "|1|": "(retrieve_entity Wildfire)",
                "|2|": "(retrieve_attribute |1| fire_size)",
                "|3|": "(retrieve_attribute |1| id)",
                "|4|": "(collect |2| |3|)",
                "|5|": "(return |4|)"
            },
            "base_plan": {
                "|1|": "(retrieve_attribute |A| {Metric:0})",
                "|2|": "({Analysis:0} |1|)",
                "|3|": "(collect |2|)",
                "|4|": "(return |3|)",

                "|5|": "(retrieve_attribute |A| {Identifier:0})",
                "|6|": "(retrieve_attribute |A| {Metric:0})",
                "|7|": "(exact |5| \"{String:0}\")",
                "|8|": "(collect |5| |6|)",
                "|9|": "(return |8| |7|)",

                "|10|": "(retrieve_attribute |4| |2|)",
                "|11|": "(retrieve_attribute |9| |6|)",
                "|12|": "(greaterthan |11| |10|)",
                "|13|": "(collect |12|)",
                "|14|": "(return |13|)"
            },
            "slot_fillers": {
                "Analysis:0": "average",
                "String:0": "2284522"
            },
            "target_plan": {
                "|1A|": "(retrieve_entity Wildfire)",
                "|2A|": "(retrieve_attribute |1A| fire_size)",
                "|3A|": "(retrieve_attribute |1A| id)",
                "|4A|": "(collect |2A| |3A|)",
                "|5A|": "(return |4A|)",

                "|1|": "(retrieve_attribute |5A| |2A|)",
                "|2|": "({Analysis:0} |1|)",
                "|3|": "(collect |2|)",
                "|4|": "(return |3|)",

                "|5|": "(retrieve_attribute |5A| |3A|)",
                "|6|": "(retrieve_attribute |5A| |2A|)",
                "|7|": "(exact |5| \"{String:0}\")",
                "|8|": "(collect |5| |6|)",
                "|9|": "(return |8| |7|)",

                "|10|": "(retrieve_attribute |4| |2|)",
                "|11|": "(retrieve_attribute |9| |6|)",
                "|12|": "(greaterthan |11| |10|)",
                "|13|": "(collect |12|)",
                "|14|": "(return |13|)"
            }
        }

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "unittest_sqr_compose", {})

        resp = requests.get(urllink, headers=self.headers, json=endpoint_info)
        results = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(results["target_plan_results"], results["composed_plan_results"])

    def test_is_instance_greater_than_average_related_entity(self):
        endpoint_info = {
            "access_plan": {
                "|1|": "(retrieve_entity State)",
                "|2|": "(retrieve_entity Wildfire)",
                "|3|": "(retrieve_attribute |1| name)",
                "|4|": "(retrieve_attribute |2| fire_size)",
                "|5|": "(groupby |3|)",
                "|6|": "({Analysis:0} |4| |5|)",
                "|7|": "(collect |3| |6|)",
                "|8|": "(return |7|)",
            },
            "base_plan": {
                "|1|": "(retrieve_attribute |A| {Metric:0})",
                "|2|": "({Analysis:1} |1|)",
                "|3|": "(collect |2|)",
                "|4|": "(return |3|)",

                "|5|": "(retrieve_attribute |A| {Identifier:0})",
                "|6|": "(retrieve_attribute |A| {Metric:0})",
                "|7|": "(exact |5| \"{String:0}\")",
                "|8|": "(collect |5| |6|)",
                "|9|": "(return |8| |7|)",

                "|10|": "(retrieve_attribute |4| |2|)",
                "|11|": "(retrieve_attribute |9| |6|)",
                "|12|": "(greaterthan |11| |10|)",
                "|13|": "(collect |12|)",
                "|14|": "(return |13|)"
            },
            "slot_fillers": {
                "Analysis:0": "average",
                "Analysis:1": "average",
                "String:0": "Idaho"
            },
            "target_plan": {
                "|1A|": "(retrieve_entity State)",
                "|2A|": "(retrieve_entity Wildfire)",
                "|3A|": "(retrieve_attribute |1A| name)",
                "|4A|": "(retrieve_attribute |2A| fire_size)",
                "|5A|": "(groupby |3A|)",
                "|6A|": "({Analysis:0} |4A| |5A|)",
                "|7A|": "(collect |3A| |6A|)",
                "|8A|": "(return |7A|)",

                "|1|": "(retrieve_attribute |8A| |6A|)",
                "|2|": "({Analysis:1} |1|)",
                "|3|": "(collect |2|)",
                "|4|": "(return |3|)",

                "|5|": "(retrieve_attribute |8A| |3A|)",
                "|6|": "(retrieve_attribute |8A| |6A|)",
                "|7|": "(exact |5| \"{String:0}\")",
                "|8|": "(collect |5| |6|)",
                "|9|": "(return |8| |7|)",

                "|10|": "(retrieve_attribute |4| |2|)",
                "|11|": "(retrieve_attribute |9| |6|)",
                "|12|": "(greaterthan |11| |10|)",
                "|13|": "(collect |12|)",
                "|14|": "(return |13|)"
            }
        }

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "unittest_sqr_compose", {})

        resp = requests.get(urllink, headers=self.headers, json=endpoint_info)
        results = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(results["target_plan_results"], results["composed_plan_results"])

if __name__ == '__main__':
    unittest.main()