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

import copy
import random
from typing import List, Dict

from satyrn.core.RingObjects.Ring import Ring
from satyrn.core.RingObjects.RingEntity import RingEntity
from satyrn.core.Planning.SQRComposer import SQRComposer
from satyrn.core.Document.BasePlanStore import BasePlanStore
from satyrn.core.Analysis.OperationOntology import OperationOntology
from satyrn.core.Planning.AnalysisPlanParser import AnalysisPlanParser
from satyrn.core.Planning.PlanGeneration.FilterGenerator import FilterGenerator
from satyrn.core.Planning.QuestionGeneratorTemplateBased import QuestionGeneratorTemplateBased
from satyrn.core.Planning.SQRCompiler import SQRCompiler

class AccessPlanGenerator:
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

    def generate_with_access_plans(self,
                                   ent: RingEntity,
                                   n_plans_per_attribute: int,
                                   filter_proportion: float = 0.5) -> List[Dict]:
        """
        Generates a set of SQR plans and associated questions using the ring attributes and their access plans.
        :param ent: The entity whose access plans will be used to generate the final plans with.
        :type ent: RingEntity
        :param n_plans_per_attribute: The number of plans to generate for each access plan.
        :type n_plans_per_attribute: int
        :param filter_proportion: The proportion of plans that should have filters added to them.
        :type filter_proportion: float
        :return: A list of dictionaries that look like: { "questions": [], "plan": {}, "base_plan": "" }
        :rtype: List[Dict]
        """

        questions_and_plans = []  # Each output should look like: { "questions": [], "plan": {}, "base_plan": "" }

        for attr_name, attr in ent.attributes.items():
            # TODO: dynamically remove aggregate functions not in sqlite
            # this just skips attrs that use functions not in sqlite
            if attr_name.startswith("median") or attr_name.startswith("stdev"):
                continue
            # Get the access plan
            access_plan_generation = {
                "plan": self.analysis_plan_parser.parse_plan_snippet(attr.access_plan),
                "questions": attr.get_questions(),
                "base_plan": None
            }

            # Make n_plan number of copies of this access plan
            current_questions_and_plans = [copy.deepcopy(access_plan_generation) for _ in range(n_plans_per_attribute)]

            ########################################################################
            #  Generate filters for a specific proportion of these generated plans
            ########################################################################
            # Make sure the proportion is between 0.0 and 1.0
            filter_proportion = max(min(filter_proportion, 1.0), 0.0)

            # Determine the number of specs that should have filters added to them
            num_to_filter = int(filter_proportion * len(current_questions_and_plans))

            # Randomly select the specs to add filters to, generate filters, and add them to the specs
            if num_to_filter > 0:
                random.shuffle(current_questions_and_plans)
            for q_p in current_questions_and_plans[:num_to_filter]:
                # Generate the filter (if possible)
                filter_steps = self.filter_generator.build_filter_with_entity(ent)
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
                    q_p["questions"] = [self.question_generator.generate_question(question,
                                                                                  {},
                                                                                  q_p["plan"],
                                                                                  filter_steps) for question in q_p["questions"]]

            # Save all of the plans generated for this attribute
            questions_and_plans.extend(current_questions_and_plans)

        # Finish processing the plans
        for d in questions_and_plans:
            # Renumber the steps of the plan
            d["plan"] = self.analysis_plan_parser.parse_from_analysis_steps(self.sqr_compiler._renumber(d["plan"].plan_steps))

            # Add source to the output
            d["source"] = "AccessPlanGenerator"

        return questions_and_plans