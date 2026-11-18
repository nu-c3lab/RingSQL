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


from satyrn.core.RingObjects.Ring import Ring
from satyrn.core.Operations.ArgType import ArgType
from satyrn.core.RingObjects.RingEntity import RingEntity
from satyrn.core.Planning.SQRComposer import SQRComposer
from satyrn.core.Document.BasePlanStore import BasePlanStore
from satyrn.core.Analysis.OperationOntology import OperationOntology
from satyrn.core.Planning.AnalysisPlanParser import AnalysisPlanParser
from satyrn.core.Planning.PlanGeneration.FilterGenerator import FilterGenerator
from satyrn.core.Planning.QuestionGeneratorTemplateBased import QuestionGeneratorTemplateBased
from satyrn.core.Planning.SQRCompiler import SQRCompiler
from satyrn.core.Planning.PlanGeneration.CustomExceptions import NoValidAttribute
from satyrn.core.Planning.utils import oxfordcomma

class GroupingPlanGenerator:
    def __init__(self,
                 ring: Ring,
                 operation_ontology: OperationOntology,
                 sqr_composer: SQRComposer,
                 base_plan_store: BasePlanStore,
                 filter_generator: FilterGenerator,
                 analysis_plan_parser: AnalysisPlanParser,
                 question_generator: QuestionGeneratorTemplateBased):
        self.ring = ring
        self.operation_ontology = operation_ontology
        self.sqr_composer = sqr_composer
        self.base_plan_store = base_plan_store
        self.filter_generator = filter_generator
        self.analysis_plan_parser = analysis_plan_parser
        self.question_generator = question_generator
        self.sqr_compiler = SQRCompiler(self.analysis_plan_parser)

    def generate_grouping_plans(self,
                                 ent: RingEntity,
                                 n_plans: int,
                                 filter_proportion: float = 0.5,
                                 having_proportion: float = 0.5) -> List[Dict]:
        """
        Generates plans that retrieve combinations of non-derived attributes and perform groupings/aggregations.
        :param ent: The entity to generate the plans for.
        :type ent: RingEntity
        :param n_plans: The number of plans to generate.
        :type n_plans: int
        :param filter_proportion: The proportion of plans that should have filters added to them.
        :type filter_proportion: float
        :param having_proportion: The proportion of plans that should have filters on the aggregated metric (to use HAVING in SQL).
        :type having_proportion: float
        :return: A list of dictionaries that look like: { "questions": [], "plan": {}, "base_plan": "" }
        :rtype: List[Dict]
        """

        questions_and_plans = []

        # Get the non-derived, categorical attributes
        categorical_attributes = [attr for attr_name, attr in ent.attributes.items() if not attr.is_derived() and ArgType.Categorical in attr.type]
        # Get the non-derived, arithmetic attributes
        arithmetic_attributes = [attr for attr_name, attr in ent.attributes.items() if not attr.is_derived() and ArgType.Arithmetic in attr.type]

        if len(arithmetic_attributes) < 1:
            raise NoValidAttribute(f"No Arithmetic attributes for {ent.name} to use for generating plans in GroupingPlanGenerator.")
        if len(categorical_attributes) < 1:
            raise NoValidAttribute(f"No Categorical attributes for {ent.name} to use for generating plans in GroupingPlanGenerator.")

        # Get the set of aggregations that can be applied
        # aggregations = ["average", "count", "count_unique", "max", "median", "min", "sum", "stddev"]
        # TODO: dynamically allow different ops based on db type
        # these are for sqlite dbs
        aggregations = ["average", "count", "count_unique", "max", "min", "sum"]


        having_proportion = max(min(having_proportion, 1.0), 0.0)
        # Determine the number of specs that should use having
        num_having = int(having_proportion * n_plans)

        for i in range(n_plans):
            # Get the attributes to group and aggregate with
            sampled_categorical_attributes = random.sample(categorical_attributes, 1)
            sampled_arithmetic_attributes = random.sample(arithmetic_attributes, 1)
            sampled_aggregation_ops = random.sample(aggregations, 1)

            categorical_attribute = sampled_categorical_attributes[0]
            arithmetic_attribute = sampled_arithmetic_attributes[0]
            aggregation_op = sampled_aggregation_ops[0]

            # Init the plan template
            p = {
                "|1|": f"(retrieve_entity {ent.name})",
                "|2|": f"(retrieve_attribute |1| {categorical_attribute.name})",
                "|3|": f"(retrieve_attribute |1| {arithmetic_attribute.name})",
                "|4|": f"(groupby |2|)",
                "|5|": f"({aggregation_op} |3| |4|)",
                "|6|": "(collect |2| |5|)",
            }
            
            if i < num_having:
                # add filter on arithmetic attribute
                filter_op = self.filter_generator.get_filter_operation(arithmetic_attribute)

                # Get a random valid value for this attribute
                filter_val = self.filter_generator.get_filter_value(arithmetic_attribute, filter_op)

                if not isinstance(filter_val, tuple):
                    filter_val = tuple([filter_val])
                filter_step = f"({filter_op} |5| {' '.join([str(x) for x in filter_val])})"
                p["|7|"] = filter_step
                p["|8|"] = "(return |6| |7|)"
            else:
                p["|7|"] = "(return |6|)"
                filter_op = None

            # Generate the question
            q = self.question_generator.statement_generator.question_generator.generate_question_from_raw_plan(p)
            
            agg_op = self.operation_ontology.resolve_operation(aggregation_op)
            agg_str = agg_op.template.format(arithmetic_attribute.nicename[1])
            
            if filter_op:
                filt_op = self.operation_ontology.resolve_operation(filter_op)
                filter_str = filt_op.template.format(agg_str, *filter_val)
            agg_nicename = f"{aggregation_op} {arithmetic_attribute.nicename[1]}"
            having_str = f" with {filter_str}" if filter_op else ""
            # multiple question templates
            q1s = [f"What are the {categorical_attribute.nicename[1]} and {agg_str} for {ent.nicename[1]} grouped by {categorical_attribute.nicename[0]}{having_str}?",
                  f"For each {categorical_attribute.nicename[0]}{having_str}?"]
            
            q2s = ["", f", what are the {categorical_attribute.nicename[1]} and {agg_str}"]
            
            # Store the question and plan pair
            out = {
                "base_plan": None,
                "plan": self.analysis_plan_parser.parse(p),
                "questions": zip(q1s, q2s)
            }
            questions_and_plans.append(out)

        ########################################################################
        #  Generate filters for a specific proportion of these generated plans
        ########################################################################
        # Make sure the proportion is between 0.0 and 1.0
        filter_proportion = max(min(filter_proportion, 1.0), 0.0)

        # Determine the number of specs that should have filters added to them
        num_to_filter = int(filter_proportion * len(questions_and_plans))

        # Randomly select the specs to add filters to, generate filters, and add them to the specs
        if num_to_filter > 0:
            random.shuffle(questions_and_plans)
        for i, q_p in enumerate(questions_and_plans):
            if i < num_to_filter:
            # Generate the filter (if possible)
                filter_steps, filter_expression = self.filter_generator.build_filter_with_entity(ent)
                if len(filter_steps) > 0:

                    # Parse the access plan and filters into the necessary representation for composition
                    parsed_plan = q_p["plan"].plan_steps
                    parsed_filter = self.analysis_plan_parser.create_analysis_steps(filter_steps)

                    # Add the filter to the plan
                    plan_with_filter = self.sqr_composer.compose_filter_and_access_plan(parsed_plan,
                                                                                        parsed_filter)

                    # Convert it to an AnalysisPlan object
                    q_p["plan"] = self.analysis_plan_parser.parse_from_analysis_steps(plan_with_filter)

                    # Update the question to include the filter
                    if not filter_expression:
                        q_p["questions"] = [f"""{self.question_generator.generate_question(q1,
                                                                                {},
                                                                                q_p["plan"],
                                                                                filter_steps)[:-1]}{q2}?""" for q1, q2 in q_p["questions"]]
                    else:
                        q_p["questions"] = [f"""{self.question_generator.combine_filter_expression_with_question(q1, filter_expression).strip("?")} {q2}?""" for q1, q2 in q_p["questions"]]
                else:
                    q_p["questions"] = [q1[:-1] + q2 + "?" for q1, q2 in q_p["questions"]]
            else:
                    q_p["questions"] = [q1[:-1] + q2 + "?" for q1, q2 in q_p["questions"]]
        # Finish processing the plans
        for d in questions_and_plans:
            # Renumber the steps of the plan
            d["plan"] = self.analysis_plan_parser.parse_from_analysis_steps(self.sqr_compiler._renumber(d["plan"].plan_steps))

            # Add source to the output
            d["source"] = "GroupingPlanGenerator"

        return questions_and_plans
