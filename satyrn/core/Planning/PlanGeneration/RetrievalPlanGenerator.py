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
from satyrn.core.Planning.utils import oxfordcomma
from satyrn.core.RingObjects.RingEntity import RingEntity
from satyrn.core.Planning.SQRComposer import SQRComposer
from satyrn.core.Document.BasePlanStore import BasePlanStore
from satyrn.core.Analysis.OperationOntology import OperationOntology
from satyrn.core.Planning.AnalysisPlanParser import AnalysisPlanParser
from satyrn.core.Planning.PlanGeneration.FilterGenerator import FilterGenerator
from satyrn.core.Planning.QuestionGeneratorTemplateBased import QuestionGeneratorTemplateBased
from satyrn.core.Planning.SQRCompiler import SQRCompiler

class RetrievalPlanGenerator:
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

    def generate_retrieval_plans(self,
                                 ent: RingEntity,
                                 n_plans: int,
                                 filter_proportion: float = 0.5,
                                 distinct_proportion: float = 0.2,
                                 max_attrs_per_plan=3,
                                #  filter_with_subquery_prop: float = 0.2,
                                #  subquery_filter_prop: float = 0.5
                                # filter_with_subquery_prop: float = 0,
                                #  subquery_filter_prop: float = 0
                                 ) -> List[Dict]:
        """
        Generates plans that retrieve combinations of non-derived attributes.
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

        available_attributes = [attr for attr_name, attr in ent.attributes.items() if not attr.is_derived()]
        distinct_proportion = max(min(distinct_proportion, 1.0), 0.0)
        # Determine the number of specs that should use distinct
        num_distinct = int(distinct_proportion * n_plans)
        
        for i in range(n_plans):
            # Determine how many attributes to retrieve at random
            n_attrs = random.randint(1, min(len(available_attributes), max_attrs_per_plan))

            # Get the set of attributes to retrieve
            sampled_attributes = random.sample(available_attributes, n_attrs)

            # Init the plan template
            p = {
                "|1|": f"(retrieve_entity {ent.name})"
            }

            # Add the sampled attributes to the plan and keep track of the steps to collect
            collect_args = []
            for step_num, attr in enumerate(sampled_attributes, start=2):
                step_ref = f"|{step_num}|"
                collect_args.append(step_ref)
                p[step_ref] = f"(retrieve_attribute |1| {attr.name})"

            # Add the collect and return statements to the plan
            use_distinct = i < num_distinct
            collect_step_ref = f"|{len(p.keys()) + 1}|"
            if use_distinct:
                p[collect_step_ref] = f"(distinct {' '.join(collect_args)})"
                collect_args = [collect_step_ref]
                collect_step_ref = f"|{len(p.keys()) + 1}|"
            
            p[collect_step_ref] = f"(collect {' '.join(collect_args)})"
            p[f"|{len(p.keys()) + 1}|"] = f"(return {collect_step_ref})"

            distinct_phrases = random.choices(["unique ", "distinct ", "different "], k=2)
            # Generate the question
            qs = [f"For {ent.nicename[1]}, what are the {distinct_phrases[0] if use_distinct else ''}{oxfordcomma([attr.nicename[1] for attr in sampled_attributes])}?",
            f"What are the {distinct_phrases[1] if use_distinct else ''}{oxfordcomma([attr.nicename[1] for attr in sampled_attributes])} for {ent.nicename[1]}?"]

            # Store the question and plan pair
            out = {
                "base_plan": None,
                "plan": self.analysis_plan_parser.parse(p),
                "questions": qs
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
        for q_p in questions_and_plans[:num_to_filter]:
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

                if not filter_expression:
                    # Update the question to include the filter
                    q_p["questions"] = [self.question_generator.generate_question(question,
                                                                                {},
                                                                                q_p["plan"],
                                                                                filter_steps) for question in q_p["questions"]]
                else:
                    q_p["questions"] = [self.question_generator.combine_filter_expression_with_question(question, filter_expression) for question in q_p["questions"]]

        # Finish processing the plans
        for d in questions_and_plans:
            # Renumber the steps of the plan
            d["plan"] = self.analysis_plan_parser.parse_from_analysis_steps(self.sqr_compiler._renumber(d["plan"].plan_steps))

            # Add source to the output
            d["source"] = "RetrievalPlanGenerator"

        return questions_and_plans
