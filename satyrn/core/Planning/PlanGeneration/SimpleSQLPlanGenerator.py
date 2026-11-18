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

import random
from typing import List, Dict
from datetime import datetime
from satyrn.core.RingObjects.Ring import Ring
from satyrn.core.Planning.utils import oxfordcomma
from satyrn.core.RingObjects.RingEntity import RingEntity
from satyrn.core.Planning.SQRComposer import SQRComposer
from satyrn.core.Document.BasePlanStore import BasePlanStore
from satyrn.core.Analysis.OperationOntology import OperationOntology
from satyrn.core.Planning.AnalysisPlanParser import AnalysisPlanParser
from satyrn.core.Analysis.AnalysisPlan import AnalysisPlan
from satyrn.core.Planning.PlanGeneration.FilterGenerator import FilterGenerator
from satyrn.core.Planning.QuestionGeneratorTemplateBased import QuestionGeneratorTemplateBased
from satyrn.core.Planning.SQRCompiler import SQRCompiler
from satyrn.core.Operations.ArgType import ArgType


# TODO: add a */all attribute to entities and refactor these plans into other components
class SimpleSQLPlanGenerator:
    def __init__(self,
                 ring: Ring,
                 operation_ontology: OperationOntology,
                #  sqr_composer: SQRComposer,
                #  base_plan_store: BasePlanStore,
                 filter_generator: FilterGenerator,
                #  analysis_plan_parser: AnalysisPlanParser,
                #  question_generator: QuestionGeneratorTemplateBased
                ):
        self.ring = ring
        self.operation_ontology = operation_ontology
        # self.sqr_composer = sqr_composer
        # self.base_plan_store = base_plan_store
        self.filter_generator = filter_generator
        # self.analysis_plan_parser = analysis_plan_parser
        # self.question_generator = question_generator
        # self.sqr_compiler = SQRCompiler(self.analysis_plan_parser)
        self.special_sql_chars = ["-", " ", "(", ")", "%", "*", "+", "/", "#"]

        self.sql_keywords = set([k.lower() for k in [
            "ADD",
            "ALL",
            "ALL",
            "ALTER",
            "AND",
            "ANY",
            "AS",
            "ASC",
            "AVG",
            "BACKUP",
            "BETWEEN",
            "BY",
            "CASE",
            "CHECK",
            "COLUMN",
            "CONSTRAINT",
            "COUNT",
            "CREATE",
            "DATABASE",
            "DEFAULT",
            "DELETE",
            "DESC",
            "DISTINCT",
            "DROP",
            "EXEC",
            "EXISTS",
            "FOREIGN",
            "FROM",
            "FULL",
            "GROUP",
            "HAVING",
            "IN",
            "INDEX",
            "INNER",
            "INSERT",
            "INTO",
            "IS",
            "JOIN",
            "KEY",
            "LEFT",
            "LIKE",
            "LIMIT",
            "MAX",
            "MIN",
            "NOT",
            "NULL",
            "OR",
            "ORDER",
            "OUTER",
            "PRIMARY",
            "PROCEDURE",
            "REPLACE",
            "RIGHT",
            "ROWNUM",
            "SELECT",
            "SET",
            "SUM",
            "TABLE",
            "TOP",
            "TRUNCATE",
            "UNION",
            "UNIQUE",
            "UPDATE",
            "VALUES",
            "VIEW",
            "WHERE",
        ]])
    
    # TODO: make sure schema name doesn't start with a number?
    def wrap_quotes(self, schema_item):
        if set(self.special_sql_chars).intersection(schema_item) or schema_item[0].isdigit() or schema_item[-1].isdigit() or schema_item in self.sql_keywords:
            return f'"{schema_item}"'
        return schema_item
            

    def generate_simple_sql_plans(self,
                                 ent: RingEntity,
                                 n_plans: int,
                                 filter_proportion: float = 0.5) -> List[Dict]:
        """
        Generates simple SQL queries mainly using * and count(*)
        :param ent: The entity to generate the plans for.
        :type ent: RingEntity
        :param n_plans: The number of plans to generate.
        :type n_plans: int
        :param filter_proportion: The proportion of plans that should have filters added to them.
        :type filter_proportion: float
        :param distinct_proportion: The proportion of plans that should use the distinct operation rather than the collect operation.
        :type distinct_proportion: float
        :return: A list of dictionaries that look like: { "questions": [], "plan": {}, "base_plan": "" }
        :rtype: List[Dict]
        """

        questions_and_plans = []

        available_attributes = [attr for attr_name, attr in ent.attributes.items() if not attr.is_derived() and len(attr.source_columns) == 1 and attr.source_table == ent.primary_table]
        # available_attributes = [attr for attr_name, attr in ent.attributes.items() if attr_name == "status_date"]
        # distinct_proportion = max(min(distinct_proportion, 1.0), 0.0)
        # Determine the number of specs that should use distinct
        num_filtered = int(filter_proportion * n_plans)
        
        selects_and_templates = [("*", ["What is all information for {0}?", "For {0}, can you give me all the available information?"]), ("count(*)", ["How many {0} are there?", "Can you tell me the total number of {0}?"])]

        # filters_and_templates = [("{0} = {1}", "for {0} of {1}"), ("{0} <> {1}", "for {0} other than {1}")]
        # trying generation with != for sqlite - models always seem to use < > instead of  <>
        filters_and_templates = [("{0} = {1}", ["for {0} of {1}", "with {0} equal to {1}"]), ("{0} != {1}", ["for {0} other than {1}", "with {0} not equal to {1}"])]


        for i in range(n_plans):
            # Determine how many attributes to retrieve at random
            
            select, templates = random.choices(selects_and_templates, weights=[0.1, 0.9], k=1)[0]

            query = f"SELECT {select} FROM {self.wrap_quotes(ent.primary_table)}"
            questions = [template.format(ent.nicename[1]) for template in templates]


            # also add filter if the unfiltered query has already been generated
            if available_attributes and (i < num_filtered or query in set([q_p["sql"] for q_p in questions_and_plans])):
                try:
                    filter_op, filter_templates = random.choices(filters_and_templates, weights=[0.8, 0.2], k=1)[0]
                    # print(filter_op)
                    random.shuffle(filter_templates)
                    filter_attr = random.choice(available_attributes)
                    # print(filter_attr)
                    filter_value = self.filter_generator.get_filter_value(filter_attr, "exact")
                    # print(filter_value)
                    # print(filter_attr.type)
                    # print(type(filter_value))
                    # print(isinstance(filter_value, datetime))
                    if isinstance(filter_value, str) or isinstance(filter_value, datetime) or set([ArgType.Datetime, ArgType.EndDate, ArgType.StartDate]).intersection(filter_attr.type):
                        clean_fv = str(filter_value).replace("'", "''")
                        filter_value_str = f"'{clean_fv}'"
                    else:
                        filter_value_str = filter_value
                    questions = [question[:-1] + " " + filter_template.format(filter_attr.nicename[0], filter_value) + "?" for question, filter_template in zip(questions, filter_templates)]
                    query += " WHERE " + filter_op.format(self.wrap_quotes(filter_attr.source_columns[0]), filter_value_str)
                except Exception as e:
                    # print(e)
                    # print(traceback.format_exc())
                    pass
            # Get the set of attributes to retrieve
            # sampled_attributes = random.choices(available_attributes, n_attrs)

            # Store the question and plan pair
            out = {
                "base_plan": None,
                "plan": None,
                "sql": query,
                "questions": questions,
                "source": "SimpleSQLPlanGenerator"
            }
            questions_and_plans.append(out)

        return questions_and_plans
