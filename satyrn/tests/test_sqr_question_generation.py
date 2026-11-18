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
import requests
import unittest

from helper_func import make_results_url

class TestSQRQuestionGeneration(unittest.TestCase):

    def setUp(self):

        self.apikey = os.environ.get("API_KEY", "thisisatestkey")
        self.url = os.environ.get("TEST_URL", "http://127.0.0.1:5000/")
        self.ringid = "20e114c2-ef05-490c-bdd8-f6f271a6733f"
        self.versionid = "1"
        self.headers ={
            "x-api-key": self.apikey
        }
        self.maxDiff = None

    def test_sum_amount(self):
        sqr_plan = {
            "|1|": "(retrieve_entity Contribution)",
            "|2|": "(retrieve_attribute |1| amount)",
            "|3|": "(sum |2|)",
            "|4|": "(collect |3|)",
            "|5|": "(return |4|)"
        }

        expected_results = "What is the total contribution amount?"

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "question_gen", {})
        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = resp.content.decode('utf-8')
        self.assertEqual(expected_results, results)

    def test_median_amount_groupby_recipient(self):
        sqr_plan = {
            "|1|": "(retrieve_entity Contribution)",
            "|2|": "(retrieve_attribute |1| amount)",
            "|3|": "(retrieve_attribute |1| contributionRecipient)",
            "|4|": "(groupby |3|)",
            "|5|": "(median |2| |4|)",
            "|6|": "(collect |3| |5|)",
            "|7|": "(return |6|)"
        }

        expected_results = "What is the recipient and what is the median contribution amount grouped by recipient?"

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "question_gen", {})
        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = resp.content.decode('utf-8')
        self.assertEqual(expected_results, results)

    def test_count_contribution(self):
        sqr_plan = {
            "|1|": "(retrieve_entity Contribution)",
            "|2|": "(retrieve_attribute |1| id)",
            "|3|": "(count |2|)",
            "|4|": "(collect |3|)",
            "|5|": "(return |4|)"
        }

        expected_results = "What is the count of contribution?"

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "question_gen", {})
        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = resp.content.decode('utf-8')
        self.assertEqual(expected_results, results)

    def test_count_contributor_groupby_area(self):
        sqr_plan = {
            "|1|": "(retrieve_entity Contributor)",
            "|2|": "(retrieve_attribute |1| id)",
            "|3|": "(retrieve_attribute |1| area)",
            "|4|": "(groupby |3|)",
            "|5|": "(count |2| |4|)",
            "|6|": "(collect |3| |5|)",
            "|7|": "(return |6|)"
        }

        expected_results = "What is the contributor sector and what is the count of contributor grouped by contributor sector?"

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "question_gen", {})
        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = resp.content.decode('utf-8')
        self.assertEqual(expected_results, results)

    def test_averagecount_contribution_contributor_groupby_area(self):
        sqr_plan = {
            "|1|": "(retrieve_entity Contribution)",
            "|2|": "(retrieve_attribute |1| id)",
            "|3|": "(retrieve_entity Contributor)",
            "|4|": "(retrieve_attribute |3| id)",
            "|5|": "(retrieve_attribute |3| area)",
            "|6|": "(groupby |5| |4|)",
            "|7|": "(count |2| |6|)",
            "|8|": "(collect |7| |5| |4|)",
            "|9|": "(return |8|)",
            "|10|": "(retrieve_attribute |9| |5|)",
            "|11|": "(retrieve_attribute |9| |7|)",
            "|12|": "(groupby |10|)",
            "|13|": "(average |11| |12|)",
            "|14|": "(collect |10| |13|)",
            "|15|": "(return |14|)"
        }

        expected_results = "What is the contributor sector and what is the average count of contribution grouped by contributor sector grouped by contributor?"

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "question_gen", {})
        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = resp.content.decode('utf-8')
        self.assertEqual(expected_results, results)

    def test_count_contributor_groupby_parentorg(self):
        sqr_plan = {
            "|1|": "(retrieve_entity Contributor)",
            "|2|": "(retrieve_attribute |1| id)",
            "|3|": "(retrieve_attribute |1| parentOrg)",
            "|4|": "(groupby |3|)",
            "|5|": "(count |2| |4|)",
            "|6|": "(collect |3| |5|)",
            "|7|": "(return |6|)"
        }

        expected_results = "What is the contributor parent organization and what is the count of contributor grouped by contributor parent organization?"

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "question_gen", {})
        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = resp.content.decode('utf-8')
        self.assertEqual(expected_results, results)

    def test_average_count_contribution_groupby_contributor_id_instate(self):
        sqr_plan = {
            "|1|": "(retrieve_entity Contribution)",
            "|2|": "(retrieve_attribute |1| id)",
            "|3|": "(retrieve_attribute |1| inState)",
            "|4|": "(retrieve_entity Contributor)",
            "|5|": "(retrieve_attribute |4| id)",
            "|6|": "(groupby |5| |3|)",
            "|7|": "(count |2| |6|)",
            "|8|": "(collect |7| |5| |3|)",
            "|9|": "(return |8|)",
            "|10|": "(retrieve_attribute |9| |3|)",
            "|11|": "(retrieve_attribute |9| |7|)",
            "|12|": "(groupby |10|)",
            "|13|": "(average |11| |12|)",
            "|14|": "(collect |10| |13|)",
            "|15|": "(return |14|)"
        }

        expected_results = "What is the in state contribution status and what is the average count of contribution grouped by contributor grouped by in state contribution status?"

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "question_gen", {})
        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = resp.content.decode('utf-8')
        self.assertEqual(expected_results, results)

    def test_sum_average_count_contribution_groupby_contributor_id_instate_electionyear(self):
        sqr_plan = {
            "|1|": "(retrieve_entity Contribution)",
            "|2|": "(retrieve_attribute |1| id)",
            "|3|": "(retrieve_attribute |1| inState)",
            "|4|": "(retrieve_attribute |1| electionYear)",
            "|5|": "(retrieve_entity Contributor)",
            "|6|": "(retrieve_attribute |5| id)",
            "|7|": "(groupby |6| |3| |4|)",
            "|8|": "(count |2| |7|)",
            "|9|": "(collect |8| |6| |3| |4|)",
            "|10|": "(return |9|)",
            "|11|": "(retrieve_attribute |10| |8|)",
            "|12|": "(retrieve_attribute |10| |3|)",
            "|13|": "(retrieve_attribute |10| |4|)",
            "|14|": "(groupby |12| |13|)",
            "|15|": "(average |11| |14|)",
            "|16|": "(collect |15| |12| |13|)",
            "|17|": "(return |16|)",
            "|18|": "(retrieve_attribute |17| |15|)",
            "|19|": "(retrieve_attribute |17| |13|)",
            "|20|": "(groupby |19|)",
            "|21|": "(sum |18| |20|)",
            "|22|": "(collect |19| |21|)",
            "|23|": "(return |22|)"
        }

        expected_results = "What is the election year and what is the total average count of contribution grouped by contributor grouped by in state contribution status grouped by election year?"

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "question_gen", {})
        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = resp.content.decode('utf-8')
        self.assertEqual(expected_results, results)

    def test_filter_query(self):
        sqr_plan = {
            "|1|": "(retrieve_entity Contribution)",
            "|2|": "(retrieve_attribute |1| amount)",
            "|3|": "(retrieve_attribute |1| inState)",
            "|4|": "(greaterthan |2| 1002.0)",
            "|5|": "(exact |3| 1)",
            "|6|": "(and |4| |5|)",
            "|7|": "(collect |2| |3|)",
            "|8|": "(return |7| |6|)"
        }

        expected_results = "What is the contribution amount for contribution amount greater than 1002.0 and in state contribution status of 1 and " \
                           "what is the in state contribution status for contribution amount greater than 1002.0 and in state contribution status of 1?"

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "question_gen", {})
        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = resp.content.decode('utf-8')
        self.assertEqual(expected_results, results)

    def test_filter_query_2(self):
        sqr_plan = {
            "|1|": "(retrieve_entity Contribution)",
            "|2|": "(retrieve_attribute |1| amount)",
            "|3|": "(retrieve_entity Contributor)",
            "|4|": "(retrieve_attribute |3| parentOrg)",
            "|5|": "(greaterthan |2| 1002.0)",
            "|6|": "(contains |4| union)",
            "|7|": "(and |5| |6|)",
            "|8|": "(collect |2| |4|)",
            "|9|": "(return |8| |7|)"
        }

        expected_results = "What is the contribution amount for contribution amount greater than 1002.0 and contributor parent organization containing \"union\" and " \
                           "what is the contributor parent organization for contribution amount greater than 1002.0 and contributor parent organization containing \"union\"?"

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "question_gen", {})
        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = resp.content.decode('utf-8')
        self.assertEqual(expected_results, results)

    def test_depth_2_filter_query(self):
        sqr_plan = {
            "|1|": "(retrieve_entity Contribution)",
            "|2|": "(retrieve_attribute |1| amount)",
            "|3|": "(retrieve_entity Contributor)",
            "|4|": "(retrieve_attribute |3| parentOrg)",
            "|5|": "(greaterthan |2| 1002.0)",
            "|6|": "(contains |4| union)",
            "|7|": "(and |5| |6|)",
            "|8|": "(collect |2| |4|)",
            "|9|": "(return |8| |7|)",
            "|10|": "(retrieve_attribute |9| |2|)",
            "|11|": "(retrieve_attribute |9| |4|)",
            "|12|": "(contains |11| value)",
            "|13|": "(not |12|)",
            "|14|": "(groupby |11|)",
            "|15|": "(sum |10| |14|)",
            "|16|": "(collect |11| |15|)",
            "|17|": "(return |16| |13|)"
        }

        expected_results = "What is the contributor parent organization for contribution amount greater than 1002.0 and contributor parent " \
                           "organization containing \"union\" and not contributor parent organization containing \"value\" and what is the " \
                           "total contribution amount grouped by contributor parent organization for contribution amount greater than 1002.0 " \
                           "and contributor parent organization containing \"union\" and not contributor parent organization containing \"value\"?"

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "question_gen", {})
        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = resp.content.decode('utf-8')
        self.assertEqual(expected_results, results)

    def test_depth_2_filter_query_2(self):
        sqr_plan = {
            "|1|": "(retrieve_entity Contribution)",
            "|2|": "(retrieve_attribute |1| amount)",
            "|3|": "(retrieve_entity Contributor)",
            "|4|": "(retrieve_attribute |3| parentOrg)",
            "|5|": "(greaterthan |2| 1002.0)",
            "|6|": "(groupby |4|)",
            "|7|": "(sum |2| |6|)",
            "|8|": "(collect |7| |4|)",
            "|9|": "(return |8| |5|)",
            "|10|": "(retrieve_attribute |9| |7|)",
            "|11|": "(retrieve_attribute |9| |4|)",
            "|12|": "(lessthan_eq |10| 200000)",
            "|13|": "(collect |11| |10|)",
            "|14|": "(return |13| |12|)"
        }

        expected_results = "What is the contributor parent organization for contribution amount greater than 1002.0 and total contribution amount grouped by contributor parent organization less than or equal to 200000 and " \
                           "what is the total contribution amount grouped by contributor parent organization for contribution amount greater than 1002.0 and total contribution amount grouped by contributor parent organization less than or equal to 200000?"

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "question_gen", {})
        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = resp.content.decode('utf-8')
        self.assertEqual(expected_results, results)

    def test_simple_comparison_query(self):
        sqr_plan = {
            "|1|": "(retrieve_entity Contribution)",
            "|2|": "(retrieve_attribute |1| amount)",
            "|3|": "(greaterthan |2| 1002.0)",
            "|4|": "(retrieve_attribute |1| inState)",
            "|5|": "(collect |2| |4| |3|)",
            "|6|": "(return |5|)"
        }

        expected_results = "What is the contribution amount, what is the in state contribution status, and is the contribution amount greater than 1002.0?"

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "question_gen", {})
        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = resp.content.decode('utf-8')
        self.assertEqual(expected_results, results)

    def test_depth_2_comparison_query(self):
        sqr_plan = {
            "|1|": "(retrieve_entity Contribution)",
            "|2|": "(retrieve_attribute |1| amount)",
            "|3|": "(greaterthan |2| 1002.0)",
            "|4|": "(retrieve_attribute |1| inState)",
            "|5|": "(collect |2| |4| |3|)",
            "|6|": "(return |5|)",
            "|7|": "(retrieve_attribute |6| |2|)",
            "|8|": "(retrieve_attribute |6| |4|)",
            "|9|": "(retrieve_attribute |6| |3|)",
            "|10|": "(collect |7| |8| |9|)",
            "|11|": "(return |10|)"
        }

        expected_results = "What is the contribution amount, what is the in state contribution status, and is the contribution amount greater than 1002.0?"

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "question_gen", {})
        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = resp.content.decode('utf-8')
        self.assertEqual(expected_results, results)

    def test_depth_2_comparison_query2(self):
        sqr_plan = {
            "|1|": "(retrieve_entity Contribution)",
            "|2|": "(retrieve_attribute |1| amount)",
            "|3|": "(greaterthan |2| 1002.0)",
            "|4|": "(retrieve_attribute |1| inState)",
            "|5|": "(collect |2| |4| |3|)",
            "|6|": "(return |5|)",
            "|7|": "(retrieve_attribute |6| |2|)",
            "|8|": "(retrieve_attribute |6| |4|)",
            "|9|": "(retrieve_attribute |6| |3|)",
            "|10|": "(exact |9| 1)",
            "|11|": "(collect |7| |8| |9|)",
            "|12|": "(return |11| |10|)"
        }

        expected_results = "What is the contribution amount for contribution amount greater than 1002.0 of 1, " \
                           "what is the in state contribution status for contribution amount greater than 1002.0 of 1, " \
                           "and is the contribution amount greater than 1002.0 for contribution amount greater than 1002.0 of 1?"

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "question_gen", {})
        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = resp.content.decode('utf-8')
        self.assertEqual(expected_results, results)

    def test_depth_2_comparison_query3(self):
        sqr_plan = {
            "|1|": "(retrieve_entity Contribution)",
            "|2|": "(retrieve_attribute |1| amount)",
            "|3|": "(retrieve_entity Contributor)",
            "|4|": "(retrieve_attribute |3| parentOrg)",
            "|5|": "(greaterthan |2| 1002.0)",
            "|6|": "(groupby |4|)",
            "|7|": "(sum |2| |6|)",
            "|8|": "(collect |7| |4|)",
            "|9|": "(return |8| |5|)",
            "|10|": "(retrieve_attribute |9| |7|)",
            "|11|": "(retrieve_attribute |9| |4|)",
            "|12|": "(lessthan_eq |10| 200000)",
            "|13|": "(collect |11| |10| |12|)",
            "|14|": "(return |13|)"
        }

        expected_results = "What is the contributor parent organization for contribution amount greater than 1002.0, " \
                           "what is the total contribution amount grouped by contributor parent organization for contribution amount greater than 1002.0, " \
                           "and is the total contribution amount grouped by contributor parent organization for contribution amount greater than 1002.0 less than or equal to 200000?"

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "question_gen", {})
        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = resp.content.decode('utf-8')
        self.assertEqual(expected_results, results)

    def test_contributor_contribution_count_comparison(self):
        sqr_plan = {
            "|1|": "(retrieve_entity Contribution)",
            "|2|": "(retrieve_entity Contributor)",
            "|3|": "(retrieve_attribute |1| id)",
            "|4|": "(retrieve_attribute |2| area)",
            "|5|": "(count |3|)",
            "|6|": "(collect |4| |5|)",
            "|7|": "(contains |4| Electrical)",
            "|8|": "(contains |4| Teamsters)",
            "|9|": "(return |6| |7|)",
            "|10|": "(return |6| |8|)",
            "|11|": "(retrieve_attribute |9| |4|)",
            "|12|": "(retrieve_attribute |9| |5|)",
            "|13|": "(retrieve_attribute |10| |4|)",
            "|14|": "(retrieve_attribute |10| |5|)",
            "|15|": "(greaterthan |12| |14|)",
            "|16|": "(collect |11| |12| |13| |14| |15|)",
            "|17|": "(return |16|)"
        }

        expected_results = "What is the contributor sector for contributor sector containing \"Electrical\", what is the count of contribution for contributor sector containing \"Electrical\", what is the contributor sector for contributor sector containing \"Teamsters\", what is the count of contribution for contributor sector containing \"Teamsters\", and is the count of contribution for contributor sector containing \"Electrical\" greater than count of contribution for contributor sector containing \"Teamsters\"?"

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "question_gen", {})
        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = resp.content.decode('utf-8')
        self.assertEqual(expected_results, results)

    def test_multi_level_filters_with_junction_graph_structure(self):
        sqr_plan = {
            "|1|": "(retrieve_entity Contributor)",
            "|2|": "(retrieve_attribute |1| area)",
            "|3|": "(contains |2| Electrical)",
            "|4|": "(contains |2| Teamsters)",
            "|5|": "(collect |2|)",
            "|6|": "(return |5| |3|)",
            "|7|": "(return |5| |4|)",
            "|8|": "(retrieve_attribute |6| |2|)",
            "|9|": "(retrieve_attribute |7| |2|)",
            "|10|": "(retrieve_entity Contribution)",
            "|11|": "(retrieve_attribute |10| id)",
            "|12|": "(count |11|)",
            "|13|": "(contains |8| Workers)",
            "|14|": "(contains |9| Union)",
            "|15|": "(collect |8| |12|)",
            "|16|": "(collect |9| |12|)",
            "|17|": "(return |15| |13|)",
            "|18|": "(return |16| |14|)",
            "|19|": "(retrieve_attribute |17| |12|)",
            "|20|": "(retrieve_attribute |18| |12|)",
            "|21|": "(greaterthan |19| |20|)",
            "|22|": "(collect |21|)",
            "|23|": "(return |22|)"
        }

        expected_results = "Is the count of contribution for contributor sector containing \"Electrical\" and contributor sector containing \"Workers\" " \
                           "greater than count of contribution for contributor sector containing \"Teamsters\" and contributor sector containing \"Union\"?"

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "question_gen", {})
        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = resp.content.decode('utf-8')
        self.assertEqual(expected_results, results)

    def test_contributor_contribution_avg_sort(self):
        sqr_plan = {
            "|1|": "(retrieve_entity Contributor)",
            "|2|": "(retrieve_attribute |1| area)",
            "|3|": "(retrieve_entity Contribution)",
            "|4|": "(retrieve_attribute |3| amount)",
            "|5|": "(groupby |2|)",
            "|6|": "(average |4| |5|)",
            "|7|": "(collect |2| |6|)",
            "|8|": "(sort |2| asc |6| desc)",
            "|9|": "(return |7| |8|)"
        }

        expected_results = "For contributor sector sorted in ascending order and average contribution amount grouped by contributor sector sorted in descending order, " \
                           "what is the contributor sector and " \
                           "what is the average contribution amount grouped by contributor sector?"

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "question_gen", {})
        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = resp.content.decode('utf-8')
        self.assertEqual(expected_results, results)

    def test_basic_arithmetic(self):
        sqr_plan = {
            "|1|": "(retrieve_entity Contribution)",
            "|2|": "(retrieve_attribute |1| amount)",
            "|3|": "(retrieve_attribute |1| electionYear)",
            "|4|": "(add |2| |3|)",
            "|5|": "(subtract |2| |3|)",
            "|6|": "(multiply |2| |3|)",
            "|7|": "(divide |2| |3|)",
            "|8|": "(collect |2| |3| |4| |5| |6| |7|)",
            "|9|": "(return |8|)"
        }

        expected_results = "What is the contribution amount, " \
                           "what is the election year, " \
                           "what is contribution amount plus election year, " \
                           "what is contribution amount minus election year, " \
                           "what is contribution amount multiplied by election year, " \
                           "and what is contribution amount divided by election year?"

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "question_gen", {})
        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = resp.content.decode('utf-8')
        self.assertEqual(expected_results, results)

    def test_manual_standard_deviation_calculation(self):
        sqr_plan = {
            "|1|": "(retrieve_entity Contribution)",
            "|2|": "(retrieve_attribute |1| amount)",
            "|3|": "(average |2|)",
            "|4|": "(count |2|)",
            "|5|": "(collect |3|)",
            "|6|": "(return |5|)",
            "|7|": "(collect |4|)",
            "|8|": "(return |7|)",
            "|9|": "(retrieve_attribute |6| |3|)",
            "|10|": "(subtract |2| |9|)",
            "|11|": "(multiply |10| |10|)",
            "|12|": "(sum |11|)",
            "|13|": "(collect |12|)",
            "|14|": "(return |13|)",
            "|15|": "(retrieve_attribute |14| |12|)",
            "|16|": "(retrieve_attribute |8| |4|)",
            "|17|": "(divide |15| |16|)",
            "|18|": "(sqrt |17|)",
            "|19|": "(collect |18|)",
            "|20|": "(return |19|)"
        }

        expected_results = "What is square root of total contribution amount minus average contribution amount multiplied by contribution amount minus average contribution amount divided by count of contribution amount?"

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "question_gen", {})
        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = resp.content.decode('utf-8')
        self.assertEqual(expected_results, results)
#
    def test_having_filter(self):
        sqr_plan = {
            "|1|": "(retrieve_entity Contribution)",
            "|2|": "(retrieve_attribute |1| id)",
            "|3|": "(retrieve_entity Contributor)",
            "|4|": "(retrieve_attribute |3| name)",
            "|5|": "(groupby |4|)",
            "|6|": "(count |2| |5|)",
            "|7|": "(collect |4| |6|)",
            "|8|": "(exact |6| 2)",
            "|9|": "(return |7| |8|)"
        }

        expected_results = "What is the contributor for count of contribution grouped by contributor of 2 " \
                           "and what is the count of contribution grouped by contributor for count of contribution grouped by contributor of 2?"

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "question_gen", {})
        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = resp.content.decode('utf-8')
        self.assertEqual(expected_results, results)

    def test_filter_having_sort(self):
        sqr_plan = {
            "|1|": "(retrieve_entity Contribution)",
            "|2|": "(retrieve_attribute |1| id)",
            "|3|": "(retrieve_entity Contributor)",
            "|4|": "(retrieve_attribute |3| name)",
            "|5|": "(groupby |4|)",
            "|6|": "(count |2| |5|)",
            "|7|": "(collect |4| |6|)",
            "|8|": "(exact |6| 2)",
            "|9|": "(contains |4| ILLINOIS)",
            "|10|": "(sort |4| desc)",
            "|11|": "(return |7| |8| |9| |10|)"
        }

        expected_results = "For contributor sorted in descending order, " \
                           "what is the contributor for count of contribution grouped by contributor of 2 and contributor containing \"ILLINOIS\" " \
                           "and what is the count of contribution grouped by contributor for count of contribution grouped by contributor of 2 and contributor containing \"ILLINOIS\"?"

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "question_gen", {})
        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = resp.content.decode('utf-8')
        self.assertEqual(expected_results, results)

    def test_contributor_contribution_avg_sort_limit(self):
        sqr_plan = {
            "|1|": "(retrieve_entity Contributor)",
            "|2|": "(retrieve_attribute |1| area)",
            "|3|": "(retrieve_entity Contribution)",
            "|4|": "(retrieve_attribute |3| amount)",
            "|5|": "(groupby |2|)",
            "|6|": "(average |4| |5|)",
            "|7|": "(collect |2| |6|)",
            "|8|": "(sort |2| asc |6| desc)",
            "|9|": "(limit 5)",
            "|10|": "(return |7| |8| |9|)"
        }

        expected_results = "For contributor sector sorted in ascending order " \
                           "and average contribution amount grouped by contributor sector sorted in descending order " \
                           "and limited to the top 5 results, " \
                           "what is the contributor sector " \
                           "and what is the average contribution amount grouped by contributor sector?"

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "question_gen", {})
        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = resp.content.decode('utf-8')
        self.assertEqual(expected_results, results)

    def test_partial_date_attribute_selection(self):
        sqr_plan = {
            "|1|": "(retrieve_entity Contribution)",
            "|2|": "(retrieve_attribute |1| contributionDate)",
            "|3|": "(retrieve_attribute |1| contributionDate:year)",
            "|4|": "(retrieve_attribute |1| contributionDate:month)",
            "|5|": "(retrieve_attribute |1| contributionDate:day)",
            "|6|": "(retrieve_attribute |1| contributionDate:onlymonth)",
            "|7|": "(retrieve_attribute |1| contributionDate:onlyday)",
            "|8|": "(retrieve_attribute |1| contributionDate:dayofweek)",
            "|9|": "(exact |2| \"2020-04-02 14:30:21\")",
            "|10|": "(collect |2| |3| |4| |5| |6| |7| |8|)",
            "|11|": "(return |10| |9|)"
        }

        expected_results = "What is the contribution date for contribution date of 2020-04-02 14:30:21, " \
                           "what is the year of contribution date for contribution date of 2020-04-02 14:30:21, " \
                           "what is the year/month of contribution date for contribution date of 2020-04-02 14:30:21, " \
                           "what is the year/month/day of contribution date for contribution date of 2020-04-02 14:30:21, " \
                           "what is the month of contribution date for contribution date of 2020-04-02 14:30:21, " \
                           "what is the day of contribution date for contribution date of 2020-04-02 14:30:21, " \
                           "and what is the day of the week of contribution date for contribution date of 2020-04-02 14:30:21?"

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "question_gen", {})
        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = resp.content.decode('utf-8')
        self.assertEqual(expected_results, results)

    def test_row_num_one_per_plan(self):
        sqr_plan = {
            "|1|": "(retrieve_entity Contribution)",
            "|2|": "(retrieve_attribute |1| contributionDate)",
            "|3|": "(retrieve_attribute |1| amount)",
            "|4|": "(sort |3| desc)",
            "|5|": "(rownum |4|)",
            "|6|": "(exact |2| \"2020-04-02 14:30:21\")",
            "|7|": "(collect |5| |3|)",
            "|8|": "(return |7| |6|)"
        }

        expected_results = "What is the rank when contribution amount sorted in descending order for contribution date of 2020-04-02 14:30:21 and what is the contribution amount for contribution date of 2020-04-02 14:30:21?"

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "question_gen", {})
        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = resp.content.decode('utf-8')
        self.assertEqual(expected_results, results)

if __name__ == '__main__':
    unittest.main()