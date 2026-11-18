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

class TestSQRAnalysis(unittest.TestCase):

    def setUp(self):

        self.apikey = os.environ.get("API_KEY", "thisisatestkey")
        self.url = os.environ.get("TEST_URL", "http://127.0.0.1:5000/")
        self.ringid = "20e114c2-ef05-490c-bdd8-f6f271a6733f"
        self.versionid = "1"
        self.headers ={
            "x-api-key": self.apikey
        }
        # self.maxDiff = None

    def test_sum_amount(self):
        # ground truth verified
        search_opts = {}

        sqr_plan = {
            "|1|": "(retrieve_entity Contribution)",
            "|2|": "(retrieve_attribute |1| amount)",
            "|3|": "(sum |2|)",
            "|4|": "(collect |3|)",
            "|5|": "(return |4|)"
        }

        expected_results = {
            "fieldNames": [
                "sum(Contribution//amount)"
            ],
            "length": 1,
            "results": [
                [
                    3745502.3
                ]
            ],
            "units": {
                "results": [
                    [
                        "dollar",
                        "dollars"
                    ]
                ]
            }
        }

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "sqr_analysis", search_opts)

        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(expected_results, results)

    def test_median_amount_groupby_recipient(self):
        # ground truth verified
        search_opts = {}

        sqr_plan = {
            "|1|": "(retrieve_entity Contribution)",
            "|2|": "(retrieve_attribute |1| amount)",
            "|3|": "(retrieve_attribute |1| contributionRecipient)",
            "|4|": "(groupby |3|)",
            "|5|": "(median |2| |4|)",
            "|6|": "(collect |3| |5|)",
            "|7|": "(return |6|)"
        }

        expected_results = {
            "fieldNames": [
                "Contribution//contributionRecipient",
                "median(Contribution//amount)"
            ],
            "length": 11,
            "results": [
                [
                    "BISS, DANIEL K & WALLACE, LITESA E",
                    1500.0
                ],
                [
                    "BOLAND, MIKE J",
                    625.0
                ],
                [
                    "CASTILLO, THOMAS MICHAEL",
                    200.0
                ],
                [
                    "DAIBER, ROBERT A (BOB) & TODD, JONATHAN",
                    350.0
                ],
                [
                    "HENDON, RICKEY R",
                    750.0
                ],
                [
                    "HYNES, DANIEL W",
                    1000.0
                ],
                [
                    "LINK, TERRY",
                    750.0
                ],
                [
                    "PRITZKER, JAY ROBERT (J B) & STRATTON, JULIANA W",
                    1000.0
                ],
                [
                    "QUINN III, PATRICK JOSEPH (PAT) & SIMON, SHEILA J",
                    2500.0
                ],
                [
                    "QUINN III, PATRICK JOSEPH (PAT) & VALLAS, PAUL GUST",
                    2500.0
                ],
                [
                    "TURNER SR, ARTHUR",
                    900.0
                ]
            ],
            "units": {
                "results": [
                    [
                        "",
                        ""
                    ],
                    [
                        "dollar",
                        "dollars"
                    ]
                ]
            }
        }

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "sqr_analysis", search_opts)

        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = json.loads(resp.content.decode('utf-8'))
        results['results'] = {tuple(row) for row in results['results']}
        self.assertEqual(expected_results, results)

    def test_count_contribution(self):
        # ground truth verified
        search_opts = {}

        sqr_plan = {
            "|1|": "(retrieve_entity Contribution)",
            "|2|": "(retrieve_attribute |1| id)",
            "|3|": "(count |2|)",
            "|4|": "(collect |3|)",
            "|5|": "(return |4|)"
        }
        expected_results = {
            "fieldNames": [
                "count(Contribution//id)"
            ],
            "length": 1,
            "results": [
                [
                    200
                ]
            ],
            "units": {
                "results": [
                    [
                        "Contribution",
                        "Contributions"
                    ]
                ]
            }
        }
        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "sqr_analysis", search_opts)

        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(expected_results, results)

    def test_count_contributor_groupby_area(self):
        # ground truth verified
        search_opts = {}

        sqr_plan = {
            "|1|": "(retrieve_entity Contributor)",
            "|2|": "(retrieve_attribute |1| id)",
            "|3|": "(retrieve_attribute |1| area)",
            "|4|": "(groupby |3|)",
            "|5|": "(count |2| |4|)",
            "|6|": "(collect |3| |5|)",
            "|7|": "(return |6|)"
        }

        expected_results = {
            "fieldNames": [
                "Contributor//area",
                "count(Contributor//id)"
            ],
            "length": 17,
            "results": [
                [
                    "Air transport unions",
                    1
                ],
                [
                    "Automotive unions",
                    2
                ],
                [
                    "Communications & hi-tech unions",
                    1
                ],
                [
                    "Construction unions",
                    53
                ],
                [
                    "Electrical workers/IBEW",
                    10
                ],
                [
                    "Entertainment unions",
                    4
                ],
                [
                    "Fire fighters unions and associations",
                    2
                ],
                [
                    "Health worker unions",
                    2
                ],
                [
                    "Labor unions",
                    5
                ],
                [
                    "Manufacturing unions",
                    1
                ],
                [
                    "Other unions",
                    4
                ],
                [
                    "Police unions & associations",
                    3
                ],
                [
                    "Railroad unions",
                    4
                ],
                [
                    "Retail trade unions",
                    3
                ],
                [
                    "State & local government employee unions",
                    3
                ],
                [
                    "Teachers unions",
                    6
                ],
                [
                    "Teamsters unions",
                    14
                ]
            ],
            "units": {
                "results": [
                    [
                        "",
                        ""
                    ],
                    [
                        "Contributor",
                        "Contributors"
                    ]
                ]
            }
        }
        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "sqr_analysis", search_opts)

        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = json.loads(resp.content.decode('utf-8'))
        results['results'] = {tuple(row) for row in results['results']}
        self.assertEqual(expected_results, results)

    def test_averagecount_contribution_contributor_groupby_area(self):
        # ground truth verified
        search_opts = {}

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

        expected_results = {
            "fieldNames": [
                "alias_0//Contributor//area",
                "average(alias_0//count(Contribution//id))"
            ],
            "length": 17,
            "results": [
                [
                    "Air transport unions",
                    1.0
                ],
                [
                    "Automotive unions",
                    4.0
                ],
                [
                    "Communications & hi-tech unions",
                    1.0
                ],
                [
                    "Construction unions",
                    1.55
                ],
                [
                    "Electrical workers/IBEW",
                    2.2
                ],
                [
                    "Entertainment unions",
                    1.75
                ],
                [
                    "Fire fighters unions and associations",
                    2.0
                ],
                [
                    "Health worker unions",
                    3.5
                ],
                [
                    "Labor unions",
                    2.2
                ],
                [
                    "Manufacturing unions",
                    1.0
                ],
                [
                    "Other unions",
                    1.5
                ],
                [
                    "Police unions & associations",
                    2.0
                ],
                [
                    "Railroad unions",
                    1.5
                ],
                [
                    "Retail trade unions",
                    2.33
                ],
                [
                    "State & local government employee unions",
                    1.33
                ],
                [
                    "Teachers unions",
                    1.83
                ],
                [
                    "Teamsters unions",
                    1.14
                ]
            ],
            "units": {
                "results": [
                    [
                        "",
                        ""
                    ],
                    [
                        "Contribution per Contributor",
                        "Contributions per Contributor"
                    ]
                ]
            }
        }

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "sqr_analysis", search_opts)

        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = json.loads(resp.content.decode('utf-8'))
        results['results'] = {tuple(row) for row in results['results']}
        self.assertEqual(expected_results, results)

    def test_count_contributor_groupby_parentorg(self):
        # ground truth verified
        search_opts = {}

        sqr_plan = {
            "|1|": "(retrieve_entity Contributor)",
            "|2|": "(retrieve_attribute |1| id)",
            "|3|": "(retrieve_attribute |1| parentOrg)",
            "|4|": "(groupby |3|)",
            "|5|": "(count |2| |4|)",
            "|6|": "(collect |3| |5|)",
            "|7|": "(return |6|)"
        }

        expected_results = {
            "fieldNames": [
                "Contributor//parentOrg",
                "count(Contributor//id)"
            ],
            "length": 28,
            "results": [
                [
                    "AMERICAN FEDERATION OF TEACHERS / AFT",
                    3
                ],
                [
                    "BROTHERHOOD OF LOCOMOTIVE ENGINEERS & TRAINMEN / BLET",
                    1
                ],
                [
                    "COMMUNICATIONS WORKERS OF AMERICA / CWA",
                    1
                ],
                [
                    "FRATERNAL ORDER OF POLICE ASSOCIATES / FOP",
                    1
                ],
                [
                    "ILLINOIS AFL-CIO",
                    1
                ],
                [
                    "INTERNATIONAL ALLIANCE OF THEATRICAL STAGE EMPLOYEES / IATSE",
                    3
                ],
                [
                    "INTERNATIONAL ASSOCIATION OF BRIDGE STRUCTURAL ORNAMENTAL & REINFORCING IRON WORKERS",
                    5
                ],
                [
                    "INTERNATIONAL ASSOCIATION OF FIRE FIGHTERS / IAFF",
                    2
                ],
                [
                    "INTERNATIONAL ASSOCIATION OF HEAT & FROST INSULATORS & ALLIED WORKERS / HFIAW",
                    1
                ],
                [
                    "INTERNATIONAL ASSOCIATION OF SHEET METAL AIR RAIL & TRANSPORTATION WORKERS / SMART",
                    2
                ],
                [
                    "INTERNATIONAL BROTHERHOOD OF BOILERMAKERS IRON SHIP BUILDERS BLACKSMITHS FORGERS & HELPERS / IBB",
                    2
                ],
                [
                    "INTERNATIONAL BROTHERHOOD OF ELECTRICAL WORKERS / IBEW",
                    9
                ],
                [
                    "INTERNATIONAL BROTHERHOOD OF TEAMSTERS / IBT",
                    13
                ],
                [
                    "INTERNATIONAL UNION OF OPERATING ENGINEERS / IUOE",
                    6
                ],
                [
                    "INTERNATIONAL UNION OF PAINTERS & ALLIED TRADES / IUPAT",
                    2
                ],
                [
                    "LABORERS INTERNATIONAL UNION OF NORTH AMERICA / LIUNA",
                    7
                ],
                [
                    "NATIONAL AFL-CIO",
                    5
                ],
                [
                    "NATIONAL EDUCATION ASSOCIATION / NEA",
                    1
                ],
                [
                    "No value",
                    25
                ],
                [
                    "SERVICE EMPLOYEES INTERNATIONAL UNION / SEIU",
                    3
                ],
                [
                    "SHEET METAL WORKERS INTERNATIONAL ASSOCIATION / SMWIA",
                    1
                ],
                [
                    "UNITE HERE! INTERNATIONAL UNION",
                    1
                ],
                [
                    "UNITED ASSOCIATION OF JOURNEYMEN & APPRENTICES OF THE PLUMBING & PIPE FITTING INDUSTRY OF THE UNITED STATES & CANADA / UA",
                    10
                ],
                [
                    "UNITED AUTOMOBILE AEROSPACE & AGRICULTURAL IMPLEMENT WORKERS OF AMERICA / UAW",
                    2
                ],
                [
                    "UNITED BROTHERHOOD OF CARPENTERS & JOINERS / UBC",
                    7
                ],
                [
                    "UNITED FOOD & COMMERCIAL WORKERS INTERNATIONAL UNION / UFCW",
                    2
                ],
                [
                    "UNITED STEEL PAPER & FORESTRY RUBBER MANUFACTURING ENERGY ALLIED INDUSTRIAL & SERVICE WORKERS INTERNATIONAL / USW",
                    1
                ],
                [
                    "UNITED UNION OF ROOFERS WATERPROOFERS & ALLIED WORKERS",
                    1
                ]
            ],
            "units": {
                "results": [
                    [
                        "",
                        ""
                    ],
                    [
                        "Contributor",
                        "Contributors"
                    ]
                ]
            }
        }
        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "sqr_analysis", search_opts)

        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = json.loads(resp.content.decode('utf-8'))
        results['results'] = {tuple(row) for row in results['results']}
        self.assertEqual(expected_results, results)

    def test_average_count_contribution_groupby_contributor_id_instate(self):
        # ground truth verified
        search_opts = {}

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

        expected_results = {
            "fieldNames": [
                "alias_0//Contribution//inState",
                "average(alias_0//count(Contribution//id))"
            ],
            "length": 2,
            "results": {
                (
                    False,
                    1.88
                ),
                (
                    True,
                    1.67
                )
            },
            "units": {
                "results": [
                    [
                        "",
                        ""
                    ],
                    [
                        "Contribution per Contributor",
                        "Contributions per Contributor"
                    ]
                ]
            }
        }
        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "sqr_analysis", search_opts)

        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = json.loads(resp.content.decode('utf-8'))
        results['results'] = {tuple(row) for row in results['results']}
        self.assertEqual(expected_results, results)

    def test_sum_average_count_contribution_groupby_contributor_id_instate_electionyear(self):
        # ground truth verified
        search_opts = {}

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

        expected_results = {
            "fieldNames": [
                "alias_1//alias_0//Contribution//electionYear",
                "sum(alias_1//average(alias_0//count(Contribution//id)))"
            ],
            "length": 3,
            "results": [
                [
                    2010,
                    3.37
                ],
                [
                    2014,
                    3.02
                ],
                [
                    2018,
                    1.0
                ]
            ],
            "units": {
                "results": [
                    [
                        "",
                        ""
                    ],
                    [
                        "Contribution per Contributor per In State Contribution Status",
                        "Contributions per Contributor per In State Contribution Status"
                    ]
                ]
            }
        }
        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "sqr_analysis", search_opts)

        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = json.loads(resp.content.decode('utf-8'))
        results['results'] = {tuple(row) for row in results['results']}
        self.assertEqual(expected_results, results)

    def test_filter_query(self):
        search_opts = {}

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

        expected_results = {
            "fieldNames": [
                "Contribution//amount",
                "Contribution//inState"
            ],
            "length": 79,
            "results": [
                [
                    2500.0,
                    True
                ],
                [
                    5000.0,
                    True
                ],
                [
                    25000.0,
                    True
                ],
                [
                    5000.0,
                    True
                ],
                [
                    1600.0,
                    True
                ],
                [
                    10000.0,
                    True
                ],
                [
                    2500.0,
                    True
                ],
                [
                    25000.0,
                    True
                ],
                [
                    25000.0,
                    True
                ],
                [
                    50000.0,
                    True
                ],
                [
                    100000.0,
                    True
                ],
                [
                    1500.0,
                    True
                ],
                [
                    5000.0,
                    True
                ],
                [
                    2500.0,
                    True
                ],
                [
                    50000.0,
                    True
                ],
                [
                    15000.0,
                    True
                ],
                [
                    25000.0,
                    True
                ],
                [
                    100000.0,
                    True
                ],
                [
                    10000.0,
                    True
                ],
                [
                    20000.0,
                    True
                ],
                [
                    42600.0,
                    True
                ],
                [
                    5000.0,
                    True
                ],
                [
                    20000.0,
                    True
                ],
                [
                    10000.0,
                    True
                ],
                [
                    5000.0,
                    True
                ],
                [
                    1200.0,
                    True
                ],
                [
                    2500.0,
                    True
                ],
                [
                    5000.0,
                    True
                ],
                [
                    2500.0,
                    True
                ],
                [
                    25000.0,
                    True
                ],
                [
                    2500.0,
                    True
                ],
                [
                    5000.0,
                    True
                ],
                [
                    2500.0,
                    True
                ],
                [
                    2500.0,
                    True
                ],
                [
                    2500.0,
                    True
                ],
                [
                    2500.0,
                    True
                ],
                [
                    5000.0,
                    True
                ],
                [
                    30000.0,
                    True
                ],
                [
                    10000.0,
                    True
                ],
                [
                    2500.0,
                    True
                ],
                [
                    50000.0,
                    True
                ],
                [
                    5000.0,
                    True
                ],
                [
                    750000.0,
                    True
                ],
                [
                    5300.0,
                    True
                ],
                [
                    50000.0,
                    True
                ],
                [
                    1300.0,
                    True
                ],
                [
                    20000.0,
                    True
                ],
                [
                    50000.0,
                    True
                ],
                [
                    5000.0,
                    True
                ],
                [
                    100000.0,
                    True
                ],
                [
                    10000.0,
                    True
                ],
                [
                    10000.0,
                    True
                ],
                [
                    2500.0,
                    True
                ],
                [
                    32250.0,
                    True
                ],
                [
                    1300.0,
                    True
                ],
                [
                    50000.0,
                    True
                ],
                [
                    5000.0,
                    True
                ],
                [
                    4000.0,
                    True
                ],
                [
                    2000.0,
                    True
                ],
                [
                    5000.0,
                    True
                ],
                [
                    10000.0,
                    True
                ],
                [
                    10000.0,
                    True
                ],
                [
                    5000.0,
                    True
                ],
                [
                    40600.0,
                    True
                ],
                [
                    200000.0,
                    True
                ],
                [
                    50000.0,
                    True
                ],
                [
                    5000.0,
                    True
                ],
                [
                    5000.0,
                    True
                ],
                [
                    5000.0,
                    True
                ],
                [
                    2500.0,
                    True
                ],
                [
                    5000.0,
                    True
                ],
                [
                    7500.0,
                    True
                ],
                [
                    2500.0,
                    True
                ],
                [
                    10000.0,
                    True
                ],
                [
                    10000.0,
                    True
                ],
                [
                    2000.0,
                    True
                ],
                [
                    25000.0,
                    True
                ],
                [
                    25000.0,
                    True
                ],
                [
                    2000.0,
                    True
                ]
            ],
            "units": {
                "results": [
                    [
                        "dollar",
                        "dollars"
                    ],
                    [
                        "",
                        ""
                    ]
                ]
            }
        }
        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "sqr_analysis", search_opts)

        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(expected_results, results)

    def test_filter_query_2(self):
        search_opts = {}

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

        expected_results = {
            "fieldNames": [
                "Contribution//amount",
                "Contributor//parentOrg"
            ],
            "length": 25,
            "results": [
                [
                    25000.0,
                    "LABORERS INTERNATIONAL UNION OF NORTH AMERICA / LIUNA"
                ],
                [
                    50000.0,
                    "INTERNATIONAL UNION OF OPERATING ENGINEERS / IUOE"
                ],
                [
                    1500.0,
                    "LABORERS INTERNATIONAL UNION OF NORTH AMERICA / LIUNA"
                ],
                [
                    50000.0,
                    "INTERNATIONAL UNION OF OPERATING ENGINEERS / IUOE"
                ],
                [
                    100000.0,
                    "SERVICE EMPLOYEES INTERNATIONAL UNION / SEIU"
                ],
                [
                    42600.0,
                    "UNITED FOOD & COMMERCIAL WORKERS INTERNATIONAL UNION / UFCW"
                ],
                [
                    20000.0,
                    "SERVICE EMPLOYEES INTERNATIONAL UNION / SEIU"
                ],
                [
                    1200.0,
                    "UNITED FOOD & COMMERCIAL WORKERS INTERNATIONAL UNION / UFCW"
                ],
                [
                    100000.0,
                    "LABORERS INTERNATIONAL UNION OF NORTH AMERICA / LIUNA"
                ],
                [
                    2500.0,
                    "UNITED FOOD & COMMERCIAL WORKERS INTERNATIONAL UNION / UFCW"
                ],
                [
                    5000.0,
                    "SERVICE EMPLOYEES INTERNATIONAL UNION / SEIU"
                ],
                [
                    10000.0,
                    "LABORERS INTERNATIONAL UNION OF NORTH AMERICA / LIUNA"
                ],
                [
                    750000.0,
                    "SERVICE EMPLOYEES INTERNATIONAL UNION / SEIU"
                ],
                [
                    10000.0,
                    "INTERNATIONAL UNION OF OPERATING ENGINEERS / IUOE"
                ],
                [
                    50000.0,
                    "LABORERS INTERNATIONAL UNION OF NORTH AMERICA / LIUNA"
                ],
                [
                    100000.0,
                    "SERVICE EMPLOYEES INTERNATIONAL UNION / SEIU"
                ],
                [
                    10000.0,
                    "LABORERS INTERNATIONAL UNION OF NORTH AMERICA / LIUNA"
                ],
                [
                    1300.0,
                    "INTERNATIONAL UNION OF PAINTERS & ALLIED TRADES / IUPAT"
                ],
                [
                    50000.0,
                    "SERVICE EMPLOYEES INTERNATIONAL UNION / SEIU"
                ],
                [
                    10000.0,
                    "INTERNATIONAL UNION OF PAINTERS & ALLIED TRADES / IUPAT"
                ],
                [
                    40600.0,
                    "UNITED FOOD & COMMERCIAL WORKERS INTERNATIONAL UNION / UFCW"
                ],
                [
                    5000.0,
                    "INTERNATIONAL UNION OF OPERATING ENGINEERS / IUOE"
                ],
                [
                    100000.0,
                    "LABORERS INTERNATIONAL UNION OF NORTH AMERICA / LIUNA"
                ],
                [
                    5000.0,
                    "LABORERS INTERNATIONAL UNION OF NORTH AMERICA / LIUNA"
                ],
                [
                    25000.0,
                    "INTERNATIONAL UNION OF OPERATING ENGINEERS / IUOE"
                ]
            ],
            "units": {
                "results": [
                    [
                        "dollar",
                        "dollars"
                    ],
                    [
                        "",
                        ""
                    ]
                ]
            }
        }
        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "sqr_analysis", search_opts)

        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = json.loads(resp.content.decode('utf-8'))
        results['results'] = {tuple(row) for row in results['results']}
        self.assertEqual(expected_results, results)

    def test_depth_2_filter_query(self):
        search_opts = {}

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

        expected_results = {
            "fieldNames": [
                "alias_0//Contributor//parentOrg",
                "sum(alias_0//Contribution//amount)"
            ],
            "length": 5,
            "results": [
                [
                    "INTERNATIONAL UNION OF OPERATING ENGINEERS / IUOE",
                    140000.0
                ],
                [
                    "INTERNATIONAL UNION OF PAINTERS & ALLIED TRADES / IUPAT",
                    11300.0
                ],
                [
                    "LABORERS INTERNATIONAL UNION OF NORTH AMERICA / LIUNA",
                    301500.0
                ],
                [
                    "SERVICE EMPLOYEES INTERNATIONAL UNION / SEIU",
                    1025000.0
                ],
                [
                    "UNITED FOOD & COMMERCIAL WORKERS INTERNATIONAL UNION / UFCW",
                    86900.0
                ]
            ],
            "units": {
                "results": [
                    [
                        "",
                        ""
                    ],
                    [
                        "dollar",
                        "dollars"
                    ]
                ]
            }
        }
        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "sqr_analysis", search_opts)

        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = json.loads(resp.content.decode('utf-8'))
        results['results'] = {tuple(row) for row in results['results']}
        self.assertEqual(expected_results, results)

    def test_depth_2_filter_query_2(self):
        search_opts = {}

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

        expected_results = {
            "fieldNames": [
                "alias_0//Contributor//parentOrg",
                "alias_0//sum(Contribution//amount)"
            ],
            "length": 17,
            "results": [
                [
                    "AMERICAN FEDERATION OF TEACHERS / AFT",
                    127500.0
                ],
                [
                    "COMMUNICATIONS WORKERS OF AMERICA / CWA",
                    2500.0
                ],
                [
                    "FRATERNAL ORDER OF POLICE ASSOCIATES / FOP",
                    2500.0
                ],
                [
                    "ILLINOIS AFL-CIO",
                    5300.0
                ],
                [
                    "INTERNATIONAL ALLIANCE OF THEATRICAL STAGE EMPLOYEES / IATSE",
                    7500.0
                ],
                [
                    "INTERNATIONAL ASSOCIATION OF BRIDGE STRUCTURAL ORNAMENTAL & REINFORCING IRON WORKERS",
                    25000.0
                ],
                [
                    "INTERNATIONAL ASSOCIATION OF FIRE FIGHTERS / IAFF",
                    14100.0
                ],
                [
                    "INTERNATIONAL ASSOCIATION OF HEAT & FROST INSULATORS & ALLIED WORKERS / HFIAW",
                    5000.0
                ],
                [
                    "INTERNATIONAL BROTHERHOOD OF ELECTRICAL WORKERS / IBEW",
                    32500.0
                ],
                [
                    "INTERNATIONAL BROTHERHOOD OF TEAMSTERS / IBT",
                    125000.0
                ],
                [
                    "INTERNATIONAL UNION OF OPERATING ENGINEERS / IUOE",
                    140000.0
                ],
                [
                    "INTERNATIONAL UNION OF PAINTERS & ALLIED TRADES / IUPAT",
                    11300.0
                ],
                [
                    "NATIONAL AFL-CIO",
                    65902.3
                ],
                [
                    "NATIONAL EDUCATION ASSOCIATION / NEA",
                    200000.0
                ],
                [
                    "UNITED ASSOCIATION OF JOURNEYMEN & APPRENTICES OF THE PLUMBING & PIPE FITTING INDUSTRY OF THE UNITED STATES & CANADA / UA",
                    105000.0
                ],
                [
                    "UNITED BROTHERHOOD OF CARPENTERS & JOINERS / UBC",
                    93750.0
                ],
                [
                    "UNITED FOOD & COMMERCIAL WORKERS INTERNATIONAL UNION / UFCW",
                    86900.0
                ]
            ],
            "units": {
                "results": [
                    [
                        "",
                        ""
                    ],
                    [
                        "dollar",
                        "dollars"
                    ]
                ]
            }
        }
        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "sqr_analysis", search_opts)

        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = json.loads(resp.content.decode('utf-8'))
        results['results'] = {tuple(row) for row in results['results']}
        self.assertEqual(expected_results, results)

    def test_simple_comparison_query(self):
        # ground truth verified
        search_opts = {}

        sqr_plan = {
            "|1|": "(retrieve_entity Contribution)",
            "|2|": "(retrieve_attribute |1| amount)",
            "|3|": "(greaterthan |2| 1002.0)",
            "|4|": "(retrieve_attribute |1| inState)",
            "|5|": "(collect |2| |4| |3|)",
            "|6|": "(return |5|)"
        }

        expected_results = {
            "fieldNames": [
                "Contribution//amount",
                "Contribution//inState",
                'greaterthan(Contribution//amount,1002.0)'
            ],
            "length": 200,
            "results": [
                [
                    10000.0,
                    False,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    100.0,
                    True,
                    False
                ],
                [
                    25000.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    False,
                    False
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    100.0,
                    True,
                    False
                ],
                [
                    1600.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    25000.0,
                    True,
                    True
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    200.0,
                    True,
                    False
                ],
                [
                    25000.0,
                    True,
                    True
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    300.0,
                    False,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    50000.0,
                    True,
                    True
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    100000.0,
                    True,
                    True
                ],
                [
                    50000.0,
                    False,
                    True
                ],
                [
                    1500.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    False,
                    False
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    200.0,
                    True,
                    False
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    50000.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    15000.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    200.0,
                    False,
                    False
                ],
                [
                    25000.0,
                    True,
                    True
                ],
                [
                    100000.0,
                    True,
                    True
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    20000.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    False,
                    False
                ],
                [
                    100000.0,
                    False,
                    True
                ],
                [
                    42600.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    20000.0,
                    True,
                    True
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    300.0,
                    True,
                    False
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    1200.0,
                    True,
                    True
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    100000.0,
                    False,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    25000.0,
                    True,
                    True
                ],
                [
                    600.0,
                    True,
                    False
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    10000.0,
                    False,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    250000.0,
                    False,
                    True
                ],
                [
                    200.0,
                    True,
                    False
                ],
                [
                    2500.0,
                    False,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    200.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    3000.0,
                    False,
                    True
                ],
                [
                    750.0,
                    True,
                    False
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    30000.0,
                    True,
                    True
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    50000.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    750000.0,
                    True,
                    True
                ],
                [
                    5300.0,
                    True,
                    True
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    250.0,
                    False,
                    False
                ],
                [
                    10000.0,
                    False,
                    True
                ],
                [
                    50000.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    5000.0,
                    False,
                    True
                ],
                [
                    1300.0,
                    True,
                    True
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    20000.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    50000.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    False,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    500000.0,
                    False,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    100000.0,
                    True,
                    True
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    5000.0,
                    False,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    10000.0,
                    False,
                    True
                ],
                [
                    32250.0,
                    True,
                    True
                ],
                [
                    1300.0,
                    True,
                    True
                ],
                [
                    50000.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    4000.0,
                    True,
                    True
                ],
                [
                    2500.0,
                    False,
                    True
                ],
                [
                    250000.0,
                    False,
                    True
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    2000.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    1500.0,
                    False,
                    True
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    40600.0,
                    True,
                    True
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    100.0,
                    False,
                    False
                ],
                [
                    200.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    200000.0,
                    True,
                    True
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    50000.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    False,
                    True
                ],
                [
                    100000.0,
                    False,
                    True
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    10600.0,
                    False,
                    True
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    False,
                    True
                ],
                [
                    7602.3,
                    False,
                    True
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    False,
                    False
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    200.0,
                    True,
                    False
                ],
                [
                    7500.0,
                    True,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    2000.0,
                    True,
                    True
                ],
                [
                    25000.0,
                    True,
                    True
                ],
                [
                    25000.0,
                    True,
                    True
                ],
                [
                    2000.0,
                    True,
                    True
                ]
            ],
            "units": {
                "results": [
                    [
                        "dollar",
                        "dollars"
                    ],
                    [
                        "",
                        ""
                    ],
                    [
                        "",
                        ""
                    ]
                ]
            }
        }

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "sqr_analysis", search_opts)

        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(expected_results, results)

    def test_depth_2_comparison_query(self):
        search_opts = {}

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

        expected_results = {
            "fieldNames": [
                "alias_0//Contribution//amount",
                "alias_0//Contribution//inState",
                'alias_0//greaterthan(Contribution//amount,1002.0)'
            ],
            "length": 200,
            "results": [
                [
                    10000.0,
                    False,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    100.0,
                    True,
                    False
                ],
                [
                    25000.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    False,
                    False
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    100.0,
                    True,
                    False
                ],
                [
                    1600.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    25000.0,
                    True,
                    True
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    200.0,
                    True,
                    False
                ],
                [
                    25000.0,
                    True,
                    True
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    300.0,
                    False,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    50000.0,
                    True,
                    True
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    100000.0,
                    True,
                    True
                ],
                [
                    50000.0,
                    False,
                    True
                ],
                [
                    1500.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    False,
                    False
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    200.0,
                    True,
                    False
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    50000.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    15000.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    200.0,
                    False,
                    False
                ],
                [
                    25000.0,
                    True,
                    True
                ],
                [
                    100000.0,
                    True,
                    True
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    20000.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    False,
                    False
                ],
                [
                    100000.0,
                    False,
                    True
                ],
                [
                    42600.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    20000.0,
                    True,
                    True
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    300.0,
                    True,
                    False
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    1200.0,
                    True,
                    True
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    100000.0,
                    False,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    25000.0,
                    True,
                    True
                ],
                [
                    600.0,
                    True,
                    False
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    10000.0,
                    False,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    250000.0,
                    False,
                    True
                ],
                [
                    200.0,
                    True,
                    False
                ],
                [
                    2500.0,
                    False,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    200.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    3000.0,
                    False,
                    True
                ],
                [
                    750.0,
                    True,
                    False
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    30000.0,
                    True,
                    True
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    50000.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    750000.0,
                    True,
                    True
                ],
                [
                    5300.0,
                    True,
                    True
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    250.0,
                    False,
                    False
                ],
                [
                    10000.0,
                    False,
                    True
                ],
                [
                    50000.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    5000.0,
                    False,
                    True
                ],
                [
                    1300.0,
                    True,
                    True
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    20000.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    50000.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    False,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    500000.0,
                    False,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    100000.0,
                    True,
                    True
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    5000.0,
                    False,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    10000.0,
                    False,
                    True
                ],
                [
                    32250.0,
                    True,
                    True
                ],
                [
                    1300.0,
                    True,
                    True
                ],
                [
                    50000.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    4000.0,
                    True,
                    True
                ],
                [
                    2500.0,
                    False,
                    True
                ],
                [
                    250000.0,
                    False,
                    True
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    2000.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    1500.0,
                    False,
                    True
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    40600.0,
                    True,
                    True
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    100.0,
                    False,
                    False
                ],
                [
                    200.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    200000.0,
                    True,
                    True
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    50000.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    False,
                    True
                ],
                [
                    100000.0,
                    False,
                    True
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    10600.0,
                    False,
                    True
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    250.0,
                    True,
                    False
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    False,
                    True
                ],
                [
                    7602.3,
                    False,
                    True
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    500.0,
                    True,
                    False
                ],
                [
                    1000.0,
                    False,
                    False
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    1000.0,
                    True,
                    False
                ],
                [
                    200.0,
                    True,
                    False
                ],
                [
                    7500.0,
                    True,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    2000.0,
                    True,
                    True
                ],
                [
                    25000.0,
                    True,
                    True
                ],
                [
                    25000.0,
                    True,
                    True
                ],
                [
                    2000.0,
                    True,
                    True
                ]
            ],
            "units": {
                "results": [
                    [
                        "dollar",
                        "dollars"
                    ],
                    [
                        "",
                        ""
                    ],
                    [
                        "",
                        ""
                    ]
                ]
            }
        }

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "sqr_analysis", search_opts)

        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(expected_results, results)

    def test_depth_2_comparison_query2(self):
        search_opts = {}

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

        expected_results = {
            "fieldNames": [
                "alias_0//Contribution//amount",
                "alias_0//Contribution//inState",
                'alias_0//greaterthan(Contribution//amount,1002.0)'
            ],
            "length": 100,
            "results": [
                [
                    10000.0,
                    False,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    25000.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    1600.0,
                    True,
                    True
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    25000.0,
                    True,
                    True
                ],
                [
                    25000.0,
                    True,
                    True
                ],
                [
                    50000.0,
                    True,
                    True
                ],
                [
                    100000.0,
                    True,
                    True
                ],
                [
                    50000.0,
                    False,
                    True
                ],
                [
                    1500.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    50000.0,
                    True,
                    True
                ],
                [
                    15000.0,
                    True,
                    True
                ],
                [
                    25000.0,
                    True,
                    True
                ],
                [
                    100000.0,
                    True,
                    True
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    20000.0,
                    True,
                    True
                ],
                [
                    100000.0,
                    False,
                    True
                ],
                [
                    42600.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    20000.0,
                    True,
                    True
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    1200.0,
                    True,
                    True
                ],
                [
                    100000.0,
                    False,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    25000.0,
                    True,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    10000.0,
                    False,
                    True
                ],
                [
                    250000.0,
                    False,
                    True
                ],
                [
                    2500.0,
                    False,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    3000.0,
                    False,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    30000.0,
                    True,
                    True
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    50000.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    750000.0,
                    True,
                    True
                ],
                [
                    5300.0,
                    True,
                    True
                ],
                [
                    10000.0,
                    False,
                    True
                ],
                [
                    50000.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    False,
                    True
                ],
                [
                    1300.0,
                    True,
                    True
                ],
                [
                    20000.0,
                    True,
                    True
                ],
                [
                    50000.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    500000.0,
                    False,
                    True
                ],
                [
                    100000.0,
                    True,
                    True
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    False,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    10000.0,
                    False,
                    True
                ],
                [
                    32250.0,
                    True,
                    True
                ],
                [
                    1300.0,
                    True,
                    True
                ],
                [
                    50000.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    4000.0,
                    True,
                    True
                ],
                [
                    2500.0,
                    False,
                    True
                ],
                [
                    250000.0,
                    False,
                    True
                ],
                [
                    2000.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    1500.0,
                    False,
                    True
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    40600.0,
                    True,
                    True
                ],
                [
                    200000.0,
                    True,
                    True
                ],
                [
                    50000.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    False,
                    True
                ],
                [
                    100000.0,
                    False,
                    True
                ],
                [
                    10600.0,
                    False,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    False,
                    True
                ],
                [
                    7602.3,
                    False,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    5000.0,
                    True,
                    True
                ],
                [
                    7500.0,
                    True,
                    True
                ],
                [
                    2500.0,
                    True,
                    True
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    10000.0,
                    True,
                    True
                ],
                [
                    2000.0,
                    True,
                    True
                ],
                [
                    25000.0,
                    True,
                    True
                ],
                [
                    25000.0,
                    True,
                    True
                ],
                [
                    2000.0,
                    True,
                    True
                ]
            ],
            "units": {
                "results": [
                    [
                        "dollar",
                        "dollars"
                    ],
                    [
                        "",
                        ""
                    ],
                    [
                        "",
                        ""
                    ]
                ]
            }
        }

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "sqr_analysis", search_opts)

        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(expected_results, results)

    def test_depth_2_comparison_query3(self):
        search_opts = {}

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

        expected_results = {
            "fieldNames": [
                "alias_0//Contributor//parentOrg",
                "alias_0//sum(Contribution//amount)",
                'lessthan_eq(alias_0//sum(Contribution//amount),200000)'
            ],
            "length": 21,
            "results": [
                [
                    "AMERICAN FEDERATION OF TEACHERS / AFT",
                    127500.0,
                    True
                ],
                [
                    "COMMUNICATIONS WORKERS OF AMERICA / CWA",
                    2500.0,
                    True
                ],
                [
                    "FRATERNAL ORDER OF POLICE ASSOCIATES / FOP",
                    2500.0,
                    True
                ],
                [
                    "ILLINOIS AFL-CIO",
                    5300.0,
                    True
                ],
                [
                    "INTERNATIONAL ALLIANCE OF THEATRICAL STAGE EMPLOYEES / IATSE",
                    7500.0,
                    True
                ],
                [
                    "INTERNATIONAL ASSOCIATION OF BRIDGE STRUCTURAL ORNAMENTAL & REINFORCING IRON WORKERS",
                    25000.0,
                    True
                ],
                [
                    "INTERNATIONAL ASSOCIATION OF FIRE FIGHTERS / IAFF",
                    14100.0,
                    True
                ],
                [
                    "INTERNATIONAL ASSOCIATION OF HEAT & FROST INSULATORS & ALLIED WORKERS / HFIAW",
                    5000.0,
                    True
                ],
                [
                    "INTERNATIONAL BROTHERHOOD OF ELECTRICAL WORKERS / IBEW",
                    32500.0,
                    True
                ],
                [
                    "INTERNATIONAL BROTHERHOOD OF TEAMSTERS / IBT",
                    125000.0,
                    True
                ],
                [
                    "INTERNATIONAL UNION OF OPERATING ENGINEERS / IUOE",
                    140000.0,
                    True
                ],
                [
                    "INTERNATIONAL UNION OF PAINTERS & ALLIED TRADES / IUPAT",
                    11300.0,
                    True
                ],
                [
                    "LABORERS INTERNATIONAL UNION OF NORTH AMERICA / LIUNA",
                    301500.0,
                    False
                ],
                [
                    "NATIONAL AFL-CIO",
                    65902.3,
                    True
                ],
                [
                    "NATIONAL EDUCATION ASSOCIATION / NEA",
                    200000.0,
                    True
                ],
                [
                    "No value",
                    992100.0,
                    False
                ],
                [
                    "SERVICE EMPLOYEES INTERNATIONAL UNION / SEIU",
                    1025000.0,
                    False
                ],
                [
                    "UNITED ASSOCIATION OF JOURNEYMEN & APPRENTICES OF THE PLUMBING & PIPE FITTING INDUSTRY OF THE UNITED STATES & CANADA / UA",
                    105000.0,
                    True
                ],
                [
                    "UNITED AUTOMOBILE AEROSPACE & AGRICULTURAL IMPLEMENT WORKERS OF AMERICA / UAW",
                    314500.0,
                    False
                ],
                [
                    "UNITED BROTHERHOOD OF CARPENTERS & JOINERS / UBC",
                    93750.0,
                    True
                ],
                [
                    "UNITED FOOD & COMMERCIAL WORKERS INTERNATIONAL UNION / UFCW",
                    86900.0,
                    True
                ]
            ],
            "units": {
                "results": [
                    [
                        "",
                        ""
                    ],
                    [
                        "dollar",
                        "dollars"
                    ],
                    [
                        "",
                        ""
                    ]
                ]
            }
        }

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "sqr_analysis", search_opts)

        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = json.loads(resp.content.decode('utf-8'))
        results['results'] = {tuple(row) for row in results['results']}
        self.assertEqual(expected_results, results)

    def test_contributor_contribution_count_comparison(self):
        search_opts = {}

        sqr_plan = {
            "|1|": "(retrieve_entity Contribution)",
            "|2|": "(retrieve_entity Contributor)",
            "|3|": "(retrieve_attribute |1| id)",
            "|4|": "(retrieve_attribute |2| area)",
            "|5|": "(count |3|)",
            "|6|": "(get_one |4|)",
            "|7|": "(collect |6| |5|)",
            "|8|": "(contains |4| Electrical)",
            "|9|": "(contains |4| Teamsters)",
            "|10|": "(return |7| |8|)",
            "|11|": "(return |7| |9|)",
            "|12|": "(retrieve_attribute |10| |6|)",
            "|13|": "(retrieve_attribute |10| |5|)",
            "|14|": "(retrieve_attribute |11| |6|)",
            "|15|": "(retrieve_attribute |11| |5|)",
            "|16|": "(greaterthan |13| |15|)",
            "|17|": "(collect |12| |13| |14| |15| |16|)",
            "|18|": "(return |17|)"
        }

        expected_results = {
            "fieldNames": [
                "alias_1//Contributor//area",
                "alias_1//count(Contribution//id)",
                "alias_0//Contributor//area",
                "alias_0//count(Contribution//id)",
                'greaterthan(alias_1//count(Contribution//id),alias_0//count(Contribution//id))'
            ],
            "length": 1,
            "results": [
                [
                    "Electrical workers/IBEW",
                    22,
                    "Teamsters unions",
                    16,
                    True
                ]
            ],
            "units": {
                "results": [
                    [
                        "",
                        ""
                    ],
                    [
                        "Contribution",
                        "Contributions"
                    ],
                    [
                        "",
                        ""
                    ],
                    [
                        "Contribution",
                        "Contributions"
                    ],
                    [
                        "",
                        ""
                    ]
                ]
            }
        }

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "sqr_analysis", search_opts)

        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(expected_results, results)

    def test_contributor_contribution_avg_sort(self):
        search_opts = {}

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

        expected_results = {
            "fieldNames": [
                "Contributor//area",
                "average(Contribution//amount)"
            ],
            "length": 17,
            "results": [
                [
                    "Air transport unions",
                    2500.0
                ],
                [
                    "Automotive unions",
                    39406.25
                ],
                [
                    "Communications & hi-tech unions",
                    2500.0
                ],
                [
                    "Construction unions",
                    10230.49
                ],
                [
                    "Electrical workers/IBEW",
                    3845.56
                ],
                [
                    "Entertainment unions",
                    1585.71
                ],
                [
                    "Fire fighters unions and associations",
                    3650.0
                ],
                [
                    "Health worker unions",
                    132357.14
                ],
                [
                    "Labor unions",
                    6368.18
                ],
                [
                    "Manufacturing unions",
                    500.0
                ],
                [
                    "Other unions",
                    1500.0
                ],
                [
                    "Police unions & associations",
                    925.0
                ],
                [
                    "Railroad unions",
                    475.0
                ],
                [
                    "Retail trade unions",
                    48307.14
                ],
                [
                    "State & local government employee unions",
                    164375.0
                ],
                [
                    "Teachers unions",
                    30359.09
                ],
                [
                    "Teamsters unions",
                    8250.0
                ]
            ],
            "units": {
                "results": [
                    [
                        "",
                        ""
                    ],
                    [
                        "dollar",
                        "dollars"
                    ]
                ]
            }
        }

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "sqr_analysis", search_opts)

        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(expected_results, results)

    def test_contributor_contribution_avg_sort_limit(self):
        search_opts = {}

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

        expected_results = {
            "fieldNames": [
                "Contributor//area",
                "average(Contribution//amount)"
            ],
            "length": 5,
            "results": [
                [
                    "Air transport unions",
                    2500.0
                ],
                [
                    "Automotive unions",
                    39406.25
                ],
                [
                    "Communications & hi-tech unions",
                    2500.0
                ],
                [
                    "Construction unions",
                    10230.49
                ],
                [
                    "Electrical workers/IBEW",
                    3845.56
                ]
            ],
            "units": {
                "results": [
                    [
                        "",
                        ""
                    ],
                    [
                        "dollar",
                        "dollars"
                    ]
                ]
            }
        }

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "sqr_analysis", search_opts)

        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(expected_results, results)

    def test_basic_arithmetic(self):
        search_opts = {}

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

        expected_results = {
            "fieldNames": [
                "Contribution//amount",
                "Contribution//electionYear",
                'add(Contribution//amount,Contribution//electionYear)',
                'subtract(Contribution//amount,Contribution//electionYear)',
                'multiply(Contribution//amount,Contribution//electionYear)',
                'divide(Contribution//amount,Contribution//electionYear)'
            ],
            "length": 200,
            "results": [
                [
                    10000.0,
                    2010,
                    12010.0,
                    7990.0,
                    20100000.0,
                    4.975124378109452
                ],
                [
                    2500.0,
                    2010,
                    4510.0,
                    490.0,
                    5025000.0,
                    1.243781094527363
                ],
                [
                    5000.0,
                    2010,
                    7010.0,
                    2990.0,
                    10050000.0,
                    2.487562189054726
                ],
                [
                    100.0,
                    2010,
                    2110.0,
                    -1910.0,
                    201000.0,
                    0.04975124378109453
                ],
                [
                    25000.0,
                    2010,
                    27010.0,
                    22990.0,
                    50250000.0,
                    12.437810945273633
                ],
                [
                    1000.0,
                    2014,
                    3014.0,
                    -1014.0,
                    2014000.0,
                    0.49652432969215493
                ],
                [
                    5000.0,
                    2010,
                    7010.0,
                    2990.0,
                    10050000.0,
                    2.487562189054726
                ],
                [
                    250.0,
                    2014,
                    2264.0,
                    -1764.0,
                    503500.0,
                    0.12413108242303873
                ],
                [
                    1000.0,
                    2010,
                    3010.0,
                    -1010.0,
                    2010000.0,
                    0.4975124378109453
                ],
                [
                    500.0,
                    2010,
                    2510.0,
                    -1510.0,
                    1005000.0,
                    0.24875621890547264
                ],
                [
                    1000.0,
                    2010,
                    3010.0,
                    -1010.0,
                    2010000.0,
                    0.4975124378109453
                ],
                [
                    250.0,
                    2010,
                    2260.0,
                    -1760.0,
                    502500.0,
                    0.12437810945273632
                ],
                [
                    1000.0,
                    2014,
                    3014.0,
                    -1014.0,
                    2014000.0,
                    0.49652432969215493
                ],
                [
                    100.0,
                    2010,
                    2110.0,
                    -1910.0,
                    201000.0,
                    0.04975124378109453
                ],
                [
                    1600.0,
                    2010,
                    3610.0,
                    -410.0,
                    3216000.0,
                    0.7960199004975125
                ],
                [
                    1000.0,
                    2010,
                    3010.0,
                    -1010.0,
                    2010000.0,
                    0.4975124378109453
                ],
                [
                    10000.0,
                    2010,
                    12010.0,
                    7990.0,
                    20100000.0,
                    4.975124378109452
                ],
                [
                    2500.0,
                    2014,
                    4514.0,
                    486.0,
                    5035000.0,
                    1.2413108242303872
                ],
                [
                    1000.0,
                    2010,
                    3010.0,
                    -1010.0,
                    2010000.0,
                    0.4975124378109453
                ],
                [
                    25000.0,
                    2014,
                    27014.0,
                    22986.0,
                    50350000.0,
                    12.413108242303872
                ],
                [
                    500.0,
                    2010,
                    2510.0,
                    -1510.0,
                    1005000.0,
                    0.24875621890547264
                ],
                [
                    1000.0,
                    2010,
                    3010.0,
                    -1010.0,
                    2010000.0,
                    0.4975124378109453
                ],
                [
                    200.0,
                    2014,
                    2214.0,
                    -1814.0,
                    402800.0,
                    0.09930486593843098
                ],
                [
                    25000.0,
                    2014,
                    27014.0,
                    22986.0,
                    50350000.0,
                    12.413108242303872
                ],
                [
                    500.0,
                    2010,
                    2510.0,
                    -1510.0,
                    1005000.0,
                    0.24875621890547264
                ],
                [
                    300.0,
                    2010,
                    2310.0,
                    -1710.0,
                    603000.0,
                    0.14925373134328357
                ],
                [
                    500.0,
                    2014,
                    2514.0,
                    -1514.0,
                    1007000.0,
                    0.24826216484607747
                ],
                [
                    50000.0,
                    2010,
                    52010.0,
                    47990.0,
                    100500000.0,
                    24.875621890547265
                ],
                [
                    250.0,
                    2010,
                    2260.0,
                    -1760.0,
                    502500.0,
                    0.12437810945273632
                ],
                [
                    100000.0,
                    2010,
                    102010.0,
                    97990.0,
                    201000000.0,
                    49.75124378109453
                ],
                [
                    50000.0,
                    2010,
                    52010.0,
                    47990.0,
                    100500000.0,
                    24.875621890547265
                ],
                [
                    1500.0,
                    2010,
                    3510.0,
                    -510.0,
                    3015000.0,
                    0.746268656716418
                ],
                [
                    5000.0,
                    2014,
                    7014.0,
                    2986.0,
                    10070000.0,
                    2.4826216484607744
                ],
                [
                    1000.0,
                    2014,
                    3014.0,
                    -1014.0,
                    2014000.0,
                    0.49652432969215493
                ],
                [
                    250.0,
                    2010,
                    2260.0,
                    -1760.0,
                    502500.0,
                    0.12437810945273632
                ],
                [
                    500.0,
                    2010,
                    2510.0,
                    -1510.0,
                    1005000.0,
                    0.24875621890547264
                ],
                [
                    1000.0,
                    2014,
                    3014.0,
                    -1014.0,
                    2014000.0,
                    0.49652432969215493
                ],
                [
                    200.0,
                    2010,
                    2210.0,
                    -1810.0,
                    402000.0,
                    0.09950248756218906
                ],
                [
                    2500.0,
                    2014,
                    4514.0,
                    486.0,
                    5035000.0,
                    1.2413108242303872
                ],
                [
                    250.0,
                    2010,
                    2260.0,
                    -1760.0,
                    502500.0,
                    0.12437810945273632
                ],
                [
                    1000.0,
                    2010,
                    3010.0,
                    -1010.0,
                    2010000.0,
                    0.4975124378109453
                ],
                [
                    50000.0,
                    2010,
                    52010.0,
                    47990.0,
                    100500000.0,
                    24.875621890547265
                ],
                [
                    1000.0,
                    2014,
                    3014.0,
                    -1014.0,
                    2014000.0,
                    0.49652432969215493
                ],
                [
                    15000.0,
                    2010,
                    17010.0,
                    12990.0,
                    30150000.0,
                    7.462686567164179
                ],
                [
                    1000.0,
                    2010,
                    3010.0,
                    -1010.0,
                    2010000.0,
                    0.4975124378109453
                ],
                [
                    1000.0,
                    2010,
                    3010.0,
                    -1010.0,
                    2010000.0,
                    0.4975124378109453
                ],
                [
                    200.0,
                    2010,
                    2210.0,
                    -1810.0,
                    402000.0,
                    0.09950248756218906
                ],
                [
                    25000.0,
                    2014,
                    27014.0,
                    22986.0,
                    50350000.0,
                    12.413108242303872
                ],
                [
                    100000.0,
                    2010,
                    102010.0,
                    97990.0,
                    201000000.0,
                    49.75124378109453
                ],
                [
                    10000.0,
                    2010,
                    12010.0,
                    7990.0,
                    20100000.0,
                    4.975124378109452
                ],
                [
                    500.0,
                    2010,
                    2510.0,
                    -1510.0,
                    1005000.0,
                    0.24875621890547264
                ],
                [
                    20000.0,
                    2014,
                    22014.0,
                    17986.0,
                    40280000.0,
                    9.930486593843098
                ],
                [
                    1000.0,
                    2014,
                    3014.0,
                    -1014.0,
                    2014000.0,
                    0.49652432969215493
                ],
                [
                    100000.0,
                    2014,
                    102014.0,
                    97986.0,
                    201400000.0,
                    49.65243296921549
                ],
                [
                    42600.0,
                    2014,
                    44614.0,
                    40586.0,
                    85796400.0,
                    21.1519364448858
                ],
                [
                    5000.0,
                    2010,
                    7010.0,
                    2990.0,
                    10050000.0,
                    2.487562189054726
                ],
                [
                    1000.0,
                    2014,
                    3014.0,
                    -1014.0,
                    2014000.0,
                    0.49652432969215493
                ],
                [
                    20000.0,
                    2010,
                    22010.0,
                    17990.0,
                    40200000.0,
                    9.950248756218905
                ],
                [
                    250.0,
                    2010,
                    2260.0,
                    -1760.0,
                    502500.0,
                    0.12437810945273632
                ],
                [
                    1000.0,
                    2010,
                    3010.0,
                    -1010.0,
                    2010000.0,
                    0.4975124378109453
                ],
                [
                    10000.0,
                    2010,
                    12010.0,
                    7990.0,
                    20100000.0,
                    4.975124378109452
                ],
                [
                    500.0,
                    2010,
                    2510.0,
                    -1510.0,
                    1005000.0,
                    0.24875621890547264
                ],
                [
                    300.0,
                    2010,
                    2310.0,
                    -1710.0,
                    603000.0,
                    0.14925373134328357
                ],
                [
                    250.0,
                    2010,
                    2260.0,
                    -1760.0,
                    502500.0,
                    0.12437810945273632
                ],
                [
                    5000.0,
                    2014,
                    7014.0,
                    2986.0,
                    10070000.0,
                    2.4826216484607744
                ],
                [
                    250.0,
                    2010,
                    2260.0,
                    -1760.0,
                    502500.0,
                    0.12437810945273632
                ],
                [
                    1200.0,
                    2010,
                    3210.0,
                    -810.0,
                    2412000.0,
                    0.5970149253731343
                ],
                [
                    500.0,
                    2010,
                    2510.0,
                    -1510.0,
                    1005000.0,
                    0.24875621890547264
                ],
                [
                    500.0,
                    2014,
                    2514.0,
                    -1514.0,
                    1007000.0,
                    0.24826216484607747
                ],
                [
                    100000.0,
                    2014,
                    102014.0,
                    97986.0,
                    201400000.0,
                    49.65243296921549
                ],
                [
                    2500.0,
                    2014,
                    4514.0,
                    486.0,
                    5035000.0,
                    1.2413108242303872
                ],
                [
                    500.0,
                    2010,
                    2510.0,
                    -1510.0,
                    1005000.0,
                    0.24875621890547264
                ],
                [
                    5000.0,
                    2010,
                    7010.0,
                    2990.0,
                    10050000.0,
                    2.487562189054726
                ],
                [
                    2500.0,
                    2018,
                    4518.0,
                    482.0,
                    5045000.0,
                    1.2388503468780971
                ],
                [
                    25000.0,
                    2014,
                    27014.0,
                    22986.0,
                    50350000.0,
                    12.413108242303872
                ],
                [
                    600.0,
                    2014,
                    2614.0,
                    -1414.0,
                    1208400.0,
                    0.29791459781529295
                ],
                [
                    2500.0,
                    2010,
                    4510.0,
                    490.0,
                    5025000.0,
                    1.243781094527363
                ],
                [
                    5000.0,
                    2010,
                    7010.0,
                    2990.0,
                    10050000.0,
                    2.487562189054726
                ],
                [
                    2500.0,
                    2014,
                    4514.0,
                    486.0,
                    5035000.0,
                    1.2413108242303872
                ],
                [
                    500.0,
                    2010,
                    2510.0,
                    -1510.0,
                    1005000.0,
                    0.24875621890547264
                ],
                [
                    1000.0,
                    2014,
                    3014.0,
                    -1014.0,
                    2014000.0,
                    0.49652432969215493
                ],
                [
                    10000.0,
                    2010,
                    12010.0,
                    7990.0,
                    20100000.0,
                    4.975124378109452
                ],
                [
                    1000.0,
                    2010,
                    3010.0,
                    -1010.0,
                    2010000.0,
                    0.4975124378109453
                ],
                [
                    250000.0,
                    2014,
                    252014.0,
                    247986.0,
                    503500000.0,
                    124.13108242303873
                ],
                [
                    200.0,
                    2018,
                    2218.0,
                    -1818.0,
                    403600.0,
                    0.09910802775024777
                ],
                [
                    2500.0,
                    2010,
                    4510.0,
                    490.0,
                    5025000.0,
                    1.243781094527363
                ],
                [
                    2500.0,
                    2014,
                    4514.0,
                    486.0,
                    5035000.0,
                    1.2413108242303872
                ],
                [
                    2500.0,
                    2010,
                    4510.0,
                    490.0,
                    5025000.0,
                    1.243781094527363
                ],
                [
                    1000.0,
                    2010,
                    3010.0,
                    -1010.0,
                    2010000.0,
                    0.4975124378109453
                ],
                [
                    500.0,
                    2010,
                    2510.0,
                    -1510.0,
                    1005000.0,
                    0.24875621890547264
                ],
                [
                    2500.0,
                    2010,
                    4510.0,
                    490.0,
                    5025000.0,
                    1.243781094527363
                ],
                [
                    1000.0,
                    2010,
                    3010.0,
                    -1010.0,
                    2010000.0,
                    0.4975124378109453
                ],
                [
                    500.0,
                    2010,
                    2510.0,
                    -1510.0,
                    1005000.0,
                    0.24875621890547264
                ],
                [
                    200.0,
                    2010,
                    2210.0,
                    -1810.0,
                    402000.0,
                    0.09950248756218906
                ],
                [
                    1000.0,
                    2014,
                    3014.0,
                    -1014.0,
                    2014000.0,
                    0.49652432969215493
                ],
                [
                    3000.0,
                    2014,
                    5014.0,
                    986.0,
                    6042000.0,
                    1.4895729890764648
                ],
                [
                    750.0,
                    2014,
                    2764.0,
                    -1264.0,
                    1510500.0,
                    0.3723932472691162
                ],
                [
                    5000.0,
                    2014,
                    7014.0,
                    2986.0,
                    10070000.0,
                    2.4826216484607744
                ],
                [
                    30000.0,
                    2010,
                    32010.0,
                    27990.0,
                    60300000.0,
                    14.925373134328359
                ],
                [
                    10000.0,
                    2010,
                    12010.0,
                    7990.0,
                    20100000.0,
                    4.975124378109452
                ],
                [
                    250.0,
                    2010,
                    2260.0,
                    -1760.0,
                    502500.0,
                    0.12437810945273632
                ],
                [
                    500.0,
                    2018,
                    2518.0,
                    -1518.0,
                    1009000.0,
                    0.24777006937561943
                ],
                [
                    500.0,
                    2014,
                    2514.0,
                    -1514.0,
                    1007000.0,
                    0.24826216484607747
                ],
                [
                    2500.0,
                    2010,
                    4510.0,
                    490.0,
                    5025000.0,
                    1.243781094527363
                ],
                [
                    1000.0,
                    2010,
                    3010.0,
                    -1010.0,
                    2010000.0,
                    0.4975124378109453
                ],
                [
                    50000.0,
                    2010,
                    52010.0,
                    47990.0,
                    100500000.0,
                    24.875621890547265
                ],
                [
                    1000.0,
                    2014,
                    3014.0,
                    -1014.0,
                    2014000.0,
                    0.49652432969215493
                ],
                [
                    5000.0,
                    2014,
                    7014.0,
                    2986.0,
                    10070000.0,
                    2.4826216484607744
                ],
                [
                    750000.0,
                    2014,
                    752014.0,
                    747986.0,
                    1510500000.0,
                    372.39324726911616
                ],
                [
                    5300.0,
                    2014,
                    7314.0,
                    3286.0,
                    10674200.0,
                    2.6315789473684212
                ],
                [
                    250.0,
                    2010,
                    2260.0,
                    -1760.0,
                    502500.0,
                    0.12437810945273632
                ],
                [
                    250.0,
                    2014,
                    2264.0,
                    -1764.0,
                    503500.0,
                    0.12413108242303873
                ],
                [
                    1000.0,
                    2010,
                    3010.0,
                    -1010.0,
                    2010000.0,
                    0.4975124378109453
                ],
                [
                    250.0,
                    2010,
                    2260.0,
                    -1760.0,
                    502500.0,
                    0.12437810945273632
                ],
                [
                    10000.0,
                    2010,
                    12010.0,
                    7990.0,
                    20100000.0,
                    4.975124378109452
                ],
                [
                    50000.0,
                    2010,
                    52010.0,
                    47990.0,
                    100500000.0,
                    24.875621890547265
                ],
                [
                    1000.0,
                    2010,
                    3010.0,
                    -1010.0,
                    2010000.0,
                    0.4975124378109453
                ],
                [
                    5000.0,
                    2014,
                    7014.0,
                    2986.0,
                    10070000.0,
                    2.4826216484607744
                ],
                [
                    1300.0,
                    2010,
                    3310.0,
                    -710.0,
                    2613000.0,
                    0.6467661691542289
                ],
                [
                    250.0,
                    2010,
                    2260.0,
                    -1760.0,
                    502500.0,
                    0.12437810945273632
                ],
                [
                    1000.0,
                    2010,
                    3010.0,
                    -1010.0,
                    2010000.0,
                    0.4975124378109453
                ],
                [
                    20000.0,
                    2014,
                    22014.0,
                    17986.0,
                    40280000.0,
                    9.930486593843098
                ],
                [
                    1000.0,
                    2010,
                    3010.0,
                    -1010.0,
                    2010000.0,
                    0.4975124378109453
                ],
                [
                    50000.0,
                    2010,
                    52010.0,
                    47990.0,
                    100500000.0,
                    24.875621890547265
                ],
                [
                    1000.0,
                    2010,
                    3010.0,
                    -1010.0,
                    2010000.0,
                    0.4975124378109453
                ],
                [
                    1000.0,
                    2010,
                    3010.0,
                    -1010.0,
                    2010000.0,
                    0.4975124378109453
                ],
                [
                    5000.0,
                    2010,
                    7010.0,
                    2990.0,
                    10050000.0,
                    2.487562189054726
                ],
                [
                    1000.0,
                    2010,
                    3010.0,
                    -1010.0,
                    2010000.0,
                    0.4975124378109453
                ],
                [
                    500.0,
                    2010,
                    2510.0,
                    -1510.0,
                    1005000.0,
                    0.24875621890547264
                ],
                [
                    1000.0,
                    2010,
                    3010.0,
                    -1010.0,
                    2010000.0,
                    0.4975124378109453
                ],
                [
                    500000.0,
                    2010,
                    502010.0,
                    497990.0,
                    1005000000.0,
                    248.75621890547265
                ],
                [
                    1000.0,
                    2010,
                    3010.0,
                    -1010.0,
                    2010000.0,
                    0.4975124378109453
                ],
                [
                    500.0,
                    2010,
                    2510.0,
                    -1510.0,
                    1005000.0,
                    0.24875621890547264
                ],
                [
                    500.0,
                    2014,
                    2514.0,
                    -1514.0,
                    1007000.0,
                    0.24826216484607747
                ],
                [
                    100000.0,
                    2010,
                    102010.0,
                    97990.0,
                    201000000.0,
                    49.75124378109453
                ],
                [
                    10000.0,
                    2010,
                    12010.0,
                    7990.0,
                    20100000.0,
                    4.975124378109452
                ],
                [
                    10000.0,
                    2014,
                    12014.0,
                    7986.0,
                    20140000.0,
                    4.965243296921549
                ],
                [
                    1000.0,
                    2010,
                    3010.0,
                    -1010.0,
                    2010000.0,
                    0.4975124378109453
                ],
                [
                    5000.0,
                    2014,
                    7014.0,
                    2986.0,
                    10070000.0,
                    2.4826216484607744
                ],
                [
                    1000.0,
                    2010,
                    3010.0,
                    -1010.0,
                    2010000.0,
                    0.4975124378109453
                ],
                [
                    2500.0,
                    2010,
                    4510.0,
                    490.0,
                    5025000.0,
                    1.243781094527363
                ],
                [
                    10000.0,
                    2014,
                    12014.0,
                    7986.0,
                    20140000.0,
                    4.965243296921549
                ],
                [
                    32250.0,
                    2010,
                    34260.0,
                    30240.0,
                    64822500.0,
                    16.044776119402986
                ],
                [
                    1300.0,
                    2010,
                    3310.0,
                    -710.0,
                    2613000.0,
                    0.6467661691542289
                ],
                [
                    50000.0,
                    2010,
                    52010.0,
                    47990.0,
                    100500000.0,
                    24.875621890547265
                ],
                [
                    5000.0,
                    2014,
                    7014.0,
                    2986.0,
                    10070000.0,
                    2.4826216484607744
                ],
                [
                    250.0,
                    2010,
                    2260.0,
                    -1760.0,
                    502500.0,
                    0.12437810945273632
                ],
                [
                    4000.0,
                    2010,
                    6010.0,
                    1990.0,
                    8040000.0,
                    1.9900497512437811
                ],
                [
                    2500.0,
                    2014,
                    4514.0,
                    486.0,
                    5035000.0,
                    1.2413108242303872
                ],
                [
                    250000.0,
                    2014,
                    252014.0,
                    247986.0,
                    503500000.0,
                    124.13108242303873
                ],
                [
                    500.0,
                    2010,
                    2510.0,
                    -1510.0,
                    1005000.0,
                    0.24875621890547264
                ],
                [
                    1000.0,
                    2010,
                    3010.0,
                    -1010.0,
                    2010000.0,
                    0.4975124378109453
                ],
                [
                    500.0,
                    2010,
                    2510.0,
                    -1510.0,
                    1005000.0,
                    0.24875621890547264
                ],
                [
                    2000.0,
                    2010,
                    4010.0,
                    -10.0,
                    4020000.0,
                    0.9950248756218906
                ],
                [
                    5000.0,
                    2014,
                    7014.0,
                    2986.0,
                    10070000.0,
                    2.4826216484607744
                ],
                [
                    10000.0,
                    2010,
                    12010.0,
                    7990.0,
                    20100000.0,
                    4.975124378109452
                ],
                [
                    1500.0,
                    2010,
                    3510.0,
                    -510.0,
                    3015000.0,
                    0.746268656716418
                ],
                [
                    10000.0,
                    2010,
                    12010.0,
                    7990.0,
                    20100000.0,
                    4.975124378109452
                ],
                [
                    1000.0,
                    2014,
                    3014.0,
                    -1014.0,
                    2014000.0,
                    0.49652432969215493
                ],
                [
                    5000.0,
                    2014,
                    7014.0,
                    2986.0,
                    10070000.0,
                    2.4826216484607744
                ],
                [
                    40600.0,
                    2014,
                    42614.0,
                    38586.0,
                    81768400.0,
                    20.158887785501488
                ],
                [
                    500.0,
                    2014,
                    2514.0,
                    -1514.0,
                    1007000.0,
                    0.24826216484607747
                ],
                [
                    100.0,
                    2010,
                    2110.0,
                    -1910.0,
                    201000.0,
                    0.04975124378109453
                ],
                [
                    200.0,
                    2010,
                    2210.0,
                    -1810.0,
                    402000.0,
                    0.09950248756218906
                ],
                [
                    500.0,
                    2014,
                    2514.0,
                    -1514.0,
                    1007000.0,
                    0.24826216484607747
                ],
                [
                    500.0,
                    2010,
                    2510.0,
                    -1510.0,
                    1005000.0,
                    0.24875621890547264
                ],
                [
                    500.0,
                    2014,
                    2514.0,
                    -1514.0,
                    1007000.0,
                    0.24826216484607747
                ],
                [
                    200000.0,
                    2010,
                    202010.0,
                    197990.0,
                    402000000.0,
                    99.50248756218906
                ],
                [
                    500.0,
                    2018,
                    2518.0,
                    -1518.0,
                    1009000.0,
                    0.24777006937561943
                ],
                [
                    50000.0,
                    2014,
                    52014.0,
                    47986.0,
                    100700000.0,
                    24.826216484607745
                ],
                [
                    5000.0,
                    2010,
                    7010.0,
                    2990.0,
                    10050000.0,
                    2.487562189054726
                ],
                [
                    100000.0,
                    2014,
                    102014.0,
                    97986.0,
                    201400000.0,
                    49.65243296921549
                ],
                [
                    500.0,
                    2014,
                    2514.0,
                    -1514.0,
                    1007000.0,
                    0.24826216484607747
                ],
                [
                    10600.0,
                    2014,
                    12614.0,
                    8586.0,
                    21348400.0,
                    5.2631578947368425
                ],
                [
                    500.0,
                    2010,
                    2510.0,
                    -1510.0,
                    1005000.0,
                    0.24875621890547264
                ],
                [
                    250.0,
                    2014,
                    2264.0,
                    -1764.0,
                    503500.0,
                    0.12413108242303873
                ],
                [
                    1000.0,
                    2018,
                    3018.0,
                    -1018.0,
                    2018000.0,
                    0.49554013875123887
                ],
                [
                    250.0,
                    2010,
                    2260.0,
                    -1760.0,
                    502500.0,
                    0.12437810945273632
                ],
                [
                    5000.0,
                    2010,
                    7010.0,
                    2990.0,
                    10050000.0,
                    2.487562189054726
                ],
                [
                    5000.0,
                    2014,
                    7014.0,
                    2986.0,
                    10070000.0,
                    2.4826216484607744
                ],
                [
                    7602.3,
                    2014,
                    9616.3,
                    5588.3,
                    15311032.200000001,
                    3.7747269116186692
                ],
                [
                    500.0,
                    2010,
                    2510.0,
                    -1510.0,
                    1005000.0,
                    0.24875621890547264
                ],
                [
                    5000.0,
                    2010,
                    7010.0,
                    2990.0,
                    10050000.0,
                    2.487562189054726
                ],
                [
                    5000.0,
                    2010,
                    7010.0,
                    2990.0,
                    10050000.0,
                    2.487562189054726
                ],
                [
                    500.0,
                    2010,
                    2510.0,
                    -1510.0,
                    1005000.0,
                    0.24875621890547264
                ],
                [
                    1000.0,
                    2010,
                    3010.0,
                    -1010.0,
                    2010000.0,
                    0.4975124378109453
                ],
                [
                    500.0,
                    2014,
                    2514.0,
                    -1514.0,
                    1007000.0,
                    0.24826216484607747
                ],
                [
                    1000.0,
                    2014,
                    3014.0,
                    -1014.0,
                    2014000.0,
                    0.49652432969215493
                ],
                [
                    2500.0,
                    2014,
                    4514.0,
                    486.0,
                    5035000.0,
                    1.2413108242303872
                ],
                [
                    5000.0,
                    2010,
                    7010.0,
                    2990.0,
                    10050000.0,
                    2.487562189054726
                ],
                [
                    1000.0,
                    2010,
                    3010.0,
                    -1010.0,
                    2010000.0,
                    0.4975124378109453
                ],
                [
                    200.0,
                    2010,
                    2210.0,
                    -1810.0,
                    402000.0,
                    0.09950248756218906
                ],
                [
                    7500.0,
                    2010,
                    9510.0,
                    5490.0,
                    15075000.0,
                    3.7313432835820897
                ],
                [
                    2500.0,
                    2014,
                    4514.0,
                    486.0,
                    5035000.0,
                    1.2413108242303872
                ],
                [
                    10000.0,
                    2010,
                    12010.0,
                    7990.0,
                    20100000.0,
                    4.975124378109452
                ],
                [
                    10000.0,
                    2010,
                    12010.0,
                    7990.0,
                    20100000.0,
                    4.975124378109452
                ],
                [
                    2000.0,
                    2010,
                    4010.0,
                    -10.0,
                    4020000.0,
                    0.9950248756218906
                ],
                [
                    25000.0,
                    2010,
                    27010.0,
                    22990.0,
                    50250000.0,
                    12.437810945273633
                ],
                [
                    25000.0,
                    2010,
                    27010.0,
                    22990.0,
                    50250000.0,
                    12.437810945273633
                ],
                [
                    2000.0,
                    2010,
                    4010.0,
                    -10.0,
                    4020000.0,
                    0.9950248756218906
                ]
            ],
            "units": {
                "results": [
                    [
                        "dollar",
                        "dollars"
                    ],
                    [
                        "",
                        ""
                    ],
                    [
                        "",
                        ""
                    ],
                    [
                        "",
                        ""
                    ],
                    [
                        "",
                        ""
                    ],
                    [
                        "",
                        ""
                    ]
                ]
            }
        }

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "sqr_analysis", search_opts)

        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = json.loads(resp.content.decode('utf-8'))
        results['results'] = {tuple(row) for row in results['results']}
        self.assertEqual(expected_results, results)

    def test_manual_standard_deviation_calculation(self):
        search_opts = {}

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

        expected_results = {
            "fieldNames": [
                "sqrt(divide(alias_2//sum(multiply(subtract(Contribution//amount,alias_1//average(Contribution//amount)),subtract(Contribution//amount,alias_1//average(Contribution//amount)))),alias_0//count(Contribution//amount)))"
            ],
            "length": 1,
            "results": [
                [
                    70743.81713509525
                ]
            ],
            "units": {
                "results": [
                    [
                        "",
                        ""
                    ]
                ]
            }
        }

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "sqr_analysis", search_opts)

        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(expected_results, results)

    def test_having_filter(self):
        search_opts = {}

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

        expected_results = {
            "fieldNames": [
                "Contributor//name",
                "count(Contribution//id)"
            ],
            "length": 25,
            "results": [
                [
                    "12TH CONGRESSIONAL DISTRICT OF ILLINOIS AFL-CIO",
                    2
                ],
                [
                    "CHICAGO FEDERATION OF LABOR & INDUSTRIAL UNION COUCIL",
                    2
                ],
                [
                    "CHICAGO FEDERATION OF TEACHERS LOCAL 1",
                    2
                ],
                [
                    "DUPAGE COUNTY BUILDING & CONSTRUCTION TRADES COUNCIL",
                    2
                ],
                [
                    "ELECTRICAL WORKERS LOCAL 51",
                    2
                ],
                [
                    "ILLINOIS AFSCME COUNCIL 31",
                    2
                ],
                [
                    "ILLINOIS EDUCATION ASSOCIATION",
                    2
                ],
                [
                    "ILLINOIS PIPE TRADES ASSOCIATION",
                    2
                ],
                [
                    "ILLINOIS PREVAILING WAGE COUNCIL",
                    2
                ],
                [
                    "INTERNATIONAL UNION OF PAINTERS & ALLIED TRADES / IUPAT",
                    2
                ],
                [
                    "IRONWORKERS LOCAL 63",
                    2
                ],
                [
                    "LABORERS INTERNATIONAL UNION OF NORTH AMERICA / LIUNA",
                    2
                ],
                [
                    "LABORERS LOCAL 309",
                    2
                ],
                [
                    "MACHINERY MOVERS RIGGERS & MACHINERY ERECTORS LOCAL 136",
                    2
                ],
                [
                    "OPERATING ENGINEERS LOCAL 520",
                    2
                ],
                [
                    "OPERATING ENGINEERS LOCAL 649",
                    2
                ],
                [
                    "OPERATING ENGINEERS LOCAL 841",
                    2
                ],
                [
                    "PLUMBERS & PIPEFITTERS LOCAL 422",
                    2
                ],
                [
                    "SEIU LOCAL 73",
                    2
                ],
                [
                    "SOUTHERN & CENTRAL ILLINOIS LABORERS DISTRICT COUNCIL",
                    2
                ],
                [
                    "SOUTHERN ILLINOIS DISTRICT COUNCIL OF CARPENTERS",
                    2
                ],
                [
                    "SPRINKLER FITTERS LOCAL 281",
                    2
                ],
                [
                    "STATE UNIVERSITIES ANNUITANTS ASSOCIATION",
                    2
                ],
                [
                    "TEAMSTERS LOCAL 50",
                    2
                ],
                [
                    "TEAMSTERS LOCAL 705",
                    2
                ]
            ],
            "units": {
                "results": [
                    [
                        "",
                        ""
                    ],
                    [
                        "Contribution",
                        "Contributions"
                    ]
                ]
            }
        }

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "sqr_analysis", search_opts)

        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = json.loads(resp.content.decode('utf-8'))
        results['results'] = {tuple(row) for row in results['results']}
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

        expected_results = {
            "fieldNames": [
                "Contributor//name",
                "count(Contribution//id)"
            ],
            "length": 7,
            "results": [
                [
                    "SOUTHERN ILLINOIS DISTRICT COUNCIL OF CARPENTERS",
                    2
                ],
                [
                    "SOUTHERN & CENTRAL ILLINOIS LABORERS DISTRICT COUNCIL",
                    2
                ],
                [
                    "ILLINOIS PREVAILING WAGE COUNCIL",
                    2
                ],
                [
                    "ILLINOIS PIPE TRADES ASSOCIATION",
                    2
                ],
                [
                    "ILLINOIS EDUCATION ASSOCIATION",
                    2
                ],
                [
                    "ILLINOIS AFSCME COUNCIL 31",
                    2
                ],
                [
                    "12TH CONGRESSIONAL DISTRICT OF ILLINOIS AFL-CIO",
                    2
                ]
            ],
            "units": {
                "results": [
                    [
                        "",
                        ""
                    ],
                    [
                        "Contribution",
                        "Contributions"
                    ]
                ]
            }
        }

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "sqr_analysis", {})

        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(expected_results, results)

    def test_contribution_ranking(self):

        sqr_plan = {
            "|1|": "(retrieve_entity Contribution)",
            "|2|": "(retrieve_attribute |1| id)",
            "|3|": "(retrieve_entity Contributor)",
            "|4|": "(retrieve_attribute |3| name)",
            "|5|": "(groupby |4|)",
            "|6|": "(count |2| |5|)",
            "|7|": "(sort |6| desc |4| asc)",
            "|8|": "(rownum |7|)",
            "|9|": "(collect |8| |4| |6|)",
            "|10|": "(return |9|)"
        }

        expected_results = {
            "fieldNames": [
                "rownum(count(Contribution//id),desc,Contributor//name,asc)",
                "Contributor//name",
                "count(Contribution//id)"
            ],
            "length": 117,
            "results": [
                [
                    1,
                    "INTERNATIONAL BROTHERHOOD OF ELECTRICAL WORKERS / IBEW",
                    10
                ],
                [
                    2,
                    "UAW REGION 4",
                    7
                ],
                [
                    3,
                    "FOOD & COMMERCIAL WORKERS LOCAL 881",
                    5
                ],
                [
                    4,
                    "SEIU HCII",
                    5
                ],
                [
                    5,
                    "CHICAGO & NORTHEASTERN ILLINOIS DISTRICT COUNCIL OF CARPENTERS",
                    4
                ],
                [
                    6,
                    "CHICAGO FRATERNAL ORDER OF POLICE LODGE 7",
                    4
                ],
                [
                    7,
                    "ILLINOIS AFL-CIO",
                    4
                ],
                [
                    8,
                    "PAINTERS & ALLIED TRADES DISTRICT COUNCIL 14",
                    4
                ],
                [
                    9,
                    "THEATRICAL STAGE EMPLOYEES LOCAL 476",
                    4
                ],
                [
                    10,
                    "CHICAGO & COOK COUNTY BUILDING & CONSTRUCTION TRADES COUNCIL",
                    3
                ],
                [
                    11,
                    "CHICAGO & GENERAL LABORERS DISTRICT COUNCIL OF CHICAGO & VICINITY",
                    3
                ],
                [
                    12,
                    "CHICAGO FIRE FIGHTERS LOCAL 2",
                    3
                ],
                [
                    13,
                    "ELECTRICAL WORKERS LOCAL 146",
                    3
                ],
                [
                    14,
                    "ILLINOIS FEDERATION OF TEACHERS",
                    3
                ],
                [
                    15,
                    "PLUMBERS & PIPEFITTERS LOCAL 99",
                    3
                ],
                [
                    16,
                    "PLUMBERS & STEAMFITTERS LOCAL 137",
                    3
                ],
                [
                    17,
                    "SHEET METAL WORKERS LOCAL 265",
                    3
                ],
                [
                    18,
                    "SHEET METAL WORKERS LOCAL 73",
                    3
                ],
                [
                    19,
                    "UNITED TRANSPORTATION UNION / UTU",
                    3
                ],
                [
                    20,
                    "12TH CONGRESSIONAL DISTRICT OF ILLINOIS AFL-CIO",
                    2
                ],
                [
                    21,
                    "CHICAGO FEDERATION OF LABOR & INDUSTRIAL UNION COUCIL",
                    2
                ],
                [
                    22,
                    "CHICAGO FEDERATION OF TEACHERS LOCAL 1",
                    2
                ],
                [
                    23,
                    "DUPAGE COUNTY BUILDING & CONSTRUCTION TRADES COUNCIL",
                    2
                ],
                [
                    24,
                    "ELECTRICAL WORKERS LOCAL 51",
                    2
                ],
                [
                    25,
                    "ILLINOIS AFSCME COUNCIL 31",
                    2
                ],
                [
                    26,
                    "ILLINOIS EDUCATION ASSOCIATION",
                    2
                ],
                [
                    27,
                    "ILLINOIS PIPE TRADES ASSOCIATION",
                    2
                ],
                [
                    28,
                    "ILLINOIS PREVAILING WAGE COUNCIL",
                    2
                ],
                [
                    29,
                    "INTERNATIONAL UNION OF PAINTERS & ALLIED TRADES / IUPAT",
                    2
                ],
                [
                    30,
                    "IRONWORKERS LOCAL 63",
                    2
                ],
                [
                    31,
                    "LABORERS INTERNATIONAL UNION OF NORTH AMERICA / LIUNA",
                    2
                ],
                [
                    32,
                    "LABORERS LOCAL 309",
                    2
                ],
                [
                    33,
                    "MACHINERY MOVERS RIGGERS & MACHINERY ERECTORS LOCAL 136",
                    2
                ],
                [
                    34,
                    "OPERATING ENGINEERS LOCAL 520",
                    2
                ],
                [
                    35,
                    "OPERATING ENGINEERS LOCAL 649",
                    2
                ],
                [
                    36,
                    "OPERATING ENGINEERS LOCAL 841",
                    2
                ],
                [
                    37,
                    "PLUMBERS & PIPEFITTERS LOCAL 422",
                    2
                ],
                [
                    38,
                    "SEIU LOCAL 73",
                    2
                ],
                [
                    39,
                    "SOUTHERN & CENTRAL ILLINOIS LABORERS DISTRICT COUNCIL",
                    2
                ],
                [
                    40,
                    "SOUTHERN ILLINOIS DISTRICT COUNCIL OF CARPENTERS",
                    2
                ],
                [
                    41,
                    "SPRINKLER FITTERS LOCAL 281",
                    2
                ],
                [
                    42,
                    "STATE UNIVERSITIES ANNUITANTS ASSOCIATION",
                    2
                ],
                [
                    43,
                    "TEAMSTERS LOCAL 50",
                    2
                ],
                [
                    44,
                    "TEAMSTERS LOCAL 705",
                    2
                ],
                [
                    45,
                    "525 POLITICAL CLUB",
                    1
                ],
                [
                    46,
                    "AIR LINE PILOTS ASSOCIATION / ALPA",
                    1
                ],
                [
                    47,
                    "BOILERMAKERS LOCAL 363",
                    1
                ],
                [
                    48,
                    "BOILERMAKERS LOCAL 60",
                    1
                ],
                [
                    49,
                    "BROTHERHOOD OF LOCOMOTIVE ENGINEERS & TRAINMEN / BLET",
                    1
                ],
                [
                    50,
                    "BROTHERHOOD OF RAILROAD SIGNALMEN / BRS",
                    1
                ],
                [
                    51,
                    "CARPENTERS & JOINERS LOCAL 1",
                    1
                ],
                [
                    52,
                    "CARPENTERS & JOINERS LOCAL 141",
                    1
                ],
                [
                    53,
                    "CARPENTERS & JOINERS LOCAL 272",
                    1
                ],
                [
                    54,
                    "CARPENTERS & JOINERS LOCAL 790",
                    1
                ],
                [
                    55,
                    "CHICAGO & CENTRAL STATES UNITE HERE!",
                    1
                ],
                [
                    56,
                    "COMMUNICATIONS WORKERS DISTRICT 4",
                    1
                ],
                [
                    57,
                    "ELECTRICAL WORKERS LOCAL 134",
                    1
                ],
                [
                    58,
                    "ELECTRICAL WORKERS LOCAL 145",
                    1
                ],
                [
                    59,
                    "ELECTRICAL WORKERS LOCAL 15",
                    1
                ],
                [
                    60,
                    "ELECTRICAL WORKERS LOCAL 193",
                    1
                ],
                [
                    61,
                    "ELECTRICAL WORKERS LOCAL 197",
                    1
                ],
                [
                    62,
                    "ELECTRICAL WORKERS LOCAL 34",
                    1
                ],
                [
                    63,
                    "ELECTRICAL WORKERS LOCAL 364",
                    1
                ],
                [
                    64,
                    "FOOD & COMMERCIAL WORKERS LOCAL 1546",
                    1
                ],
                [
                    65,
                    "HEAT & FROST INSULATORS LOCAL 17",
                    1
                ],
                [
                    66,
                    "ILLINOIS BROTHERHOOD OF LOCOMOTIVE ENGINEERS & TRAINMEN",
                    1
                ],
                [
                    67,
                    "ILLINOIS FRATERNAL ORDER OF POLICE LABOR COUNCIL",
                    1
                ],
                [
                    68,
                    "ILLINOIS TROOPERS LODGE 41",
                    1
                ],
                [
                    69,
                    "INTERNATIONAL ASSOCIATION OF HEAT & FROST INSULATORS & ALLIED WORKERS / HFIAW",
                    1
                ],
                [
                    70,
                    "INTERNATIONAL ASSOCIATION OF SHEET METAL AIR RAIL & TRANSPORTATION WORKERS / SMART",
                    1
                ],
                [
                    71,
                    "INTERNATIONAL BROTHERHOOD OF TEAMSTERS / IBT",
                    1
                ],
                [
                    72,
                    "IRONWORKERS DISTRICT COUNCIL OF CHICAGO & VICINITY",
                    1
                ],
                [
                    73,
                    "IRONWORKERS LOCAL 111",
                    1
                ],
                [
                    74,
                    "IRONWORKERS LOCAL 392",
                    1
                ],
                [
                    75,
                    "IRONWORKERS LOCAL 498",
                    1
                ],
                [
                    76,
                    "LABORERS LOCAL 32",
                    1
                ],
                [
                    77,
                    "LABORERS LOCAL 397",
                    1
                ],
                [
                    78,
                    "LAKE COUNTY BUILDING & CONSTRUCTION TRADES COUNCIL",
                    1
                ],
                [
                    79,
                    "LAKE COUNTY FEDERATION OF TEACHERS LOCAL 504",
                    1
                ],
                [
                    80,
                    "LIQUOR & WINE SALES REPS & ALLIED WORKERS LOCAL 3",
                    1
                ],
                [
                    81,
                    "MID-CENTRAL ILLINOIS DISTRICT COUNCIL OF CARPENTERS",
                    1
                ],
                [
                    82,
                    "MIDWEST REGION LABORERS",
                    1
                ],
                [
                    83,
                    "MISSOURI PLUMBING INDUSTRY COUNCIL",
                    1
                ],
                [
                    84,
                    "MOTION PICTURE PROJECTIONISTS OPERATORS & VIDEO TECHNICIANS LOCAL 110",
                    1
                ],
                [
                    85,
                    "NORTHWESTERN ILLINOIS BUILDING & CONSTRUCTION TRADES COUNCIL",
                    1
                ],
                [
                    86,
                    "OPERATING ENGINEERS LOCAL 148",
                    1
                ],
                [
                    87,
                    "OPERATING ENGINEERS LOCAL 150",
                    1
                ],
                [
                    88,
                    "OPERATING ENGINEERS LOCAL 965",
                    1
                ],
                [
                    89,
                    "PAINTERS & ALLIED TRADES LOCAL 157",
                    1
                ],
                [
                    90,
                    "PEORIA FIRE FIGHTERS LOCAL 50",
                    1
                ],
                [
                    91,
                    "PLUMBERS & GASFITTERS LOCAL 360",
                    1
                ],
                [
                    92,
                    "PLUMBERS & PIPEFITTERS (UNIDENTIFIABLE)",
                    1
                ],
                [
                    93,
                    "PLUMBERS & PIPEFITTERS LOCAL 501",
                    1
                ],
                [
                    94,
                    "PLUMBERS & PIPEFITTERS LOCAL 533",
                    1
                ],
                [
                    95,
                    "PLUMBERS & PIPEFITTERS LOCAL 597",
                    1
                ],
                [
                    96,
                    "ROOFERS & WATERPROOFERS LOCAL 11",
                    1
                ],
                [
                    97,
                    "S T I P E N D LOCAL 710",
                    1
                ],
                [
                    98,
                    "SEIU ILLINOIS COUNCIL",
                    1
                ],
                [
                    99,
                    "SERVICE EMPLOYEES INTERNATIONAL UNION / SEIU",
                    1
                ],
                [
                    100,
                    "SHEET METAL WORKERS LOCAL 268",
                    1
                ],
                [
                    101,
                    "STEELWORKERS LOCAL 17",
                    1
                ],
                [
                    102,
                    "TEAMSTERS (UNIDENTIFIABLE)",
                    1
                ],
                [
                    103,
                    "TEAMSTERS JOINT COUNCIL 25",
                    1
                ],
                [
                    104,
                    "TEAMSTERS LOCAL 179",
                    1
                ],
                [
                    105,
                    "TEAMSTERS LOCAL 627",
                    1
                ],
                [
                    106,
                    "TEAMSTERS LOCAL 700",
                    1
                ],
                [
                    107,
                    "TEAMSTERS LOCAL 727",
                    1
                ],
                [
                    108,
                    "TEAMSTERS LOCAL 731",
                    1
                ],
                [
                    109,
                    "TEAMSTERS LOCAL 777",
                    1
                ],
                [
                    110,
                    "TEAMSTERS LOCAL 916",
                    1
                ],
                [
                    111,
                    "THEATRICAL STAGE EMPLOYEES LOCAL 2",
                    1
                ],
                [
                    112,
                    "THEATRICAL STAGE EMPLOYEES LOCAL 750",
                    1
                ],
                [
                    113,
                    "UNITED ASSOCIATION OF JOURNEYMEN & APPRENTICES OF THE PLUMBING & PIPE FITTING INDUSTRY OF THE UNITED STATES & CANADA / UA",
                    1
                ],
                [
                    114,
                    "UNITED AUTOMOBILE AEROSPACE & AGRICULTURAL IMPLEMENT WORKERS OF AMERICA / UAW",
                    1
                ],
                [
                    115,
                    "UNITED FOOD & COMMERCIAL WORKERS INTERNATIONAL UNION / UFCW",
                    1
                ],
                [
                    116,
                    "WEST SUBURBAN TEACHERS LOCAL 571",
                    1
                ],
                [
                    117,
                    "WILL-GRUNDY COUNTIES CENTRAL TRADES & LABOR COUNCIL",
                    1
                ]
            ],
            "units": {
                "results": [
                    [
                        "",
                        ""
                    ],
                    [
                        "",
                        ""
                    ],
                    [
                        "Contribution",
                        "Contributions"
                    ]
                ]
            }
        }

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "sqr_analysis", {})

        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = json.loads(resp.content.decode('utf-8'))
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

        expected_results = {
            "fieldNames": [
                "Contribution//contributionDate",
                "Contribution//contributionDate:year",
                "Contribution//contributionDate:month",
                "Contribution//contributionDate:day",
                "Contribution//contributionDate:onlymonth",
                "Contribution//contributionDate:onlyday",
                "Contribution//contributionDate:dayofweek"
            ],
            "length": 1,
            "results": [
                [
                    "2020-04-02 14:30:21",
                    "2020",
                    "2020/04",
                    "2020/04/02",
                    "04",
                    "02",
                    "4"
                ]
            ],
            "units": {
                "results": [
                    [
                        "",
                        ""
                    ],
                    [
                        "",
                        ""
                    ],
                    [
                        "",
                        ""
                    ],
                    [
                        "",
                        ""
                    ],
                    [
                        "",
                        ""
                    ],
                    [
                        "",
                        ""
                    ],
                    [
                        "",
                        ""
                    ]
                ]
            }
        }

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "sqr_analysis", {})

        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(expected_results, results)

    def test_contribution_percent_change(self):
        search_opts = {}

        sqr_plan = {
            "|1|": "(retrieve_entity Contribution)",
            "|2|": "(retrieve_attribute |1| amount)",
            "|3|": "(retrieve_attribute |1| electionYear)",
            "|4|": "(retrieve_entity Contributor)",
            "|5|": "(retrieve_attribute |4| name)",
            "|6|": "(exact |3| 2010)",
            "|7|": "(exact |3| 2014)",
            "|8|": "(sum |2|)",
            "|9|": "(exact |5| 'UAW REGION 4')",
            "|10|": "(and |9| |6|)",
            "|11|": "(and |9| |7|)",
            "|12|": "(collect |8|)",
            "|13|": "(return |12| |10|)",
            "|14|": "(return |12| |11|)",
            "|15|": "(retrieve_attribute |13| |8|)",
            "|16|": "(retrieve_attribute |14| |8|)",
            "|17|": "(percent_change |15| |16|)",
            "|18|": "(collect |17|)",
            "|19|": "(return |18|)"
        }

        expected_results = {
            "fieldNames": [
                "percent_change(alias_1//sum(Contribution//amount),alias_0//sum(Contribution//amount))"
            ],
            "length": 1,
            "results": [
                [
                    2.4237288135593222
                ]
            ],
            "units": {
                "results": [
                    [
                        "",
                        ""
                    ]
                ]
            }
        }

        urllink = make_results_url(self.url, self.ringid, self.versionid, None, "sqr_analysis", search_opts)

        resp = requests.get(urllink, headers=self.headers, json=sqr_plan)
        results = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(expected_results, results)


if __name__ == '__main__':
    unittest.main()