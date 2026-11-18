'''
Satyrn is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software Foundation,
either version 3 of the License, or (at your option) any later version.
Satyrn is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with Satyrn.
This file is part of Satyrn.
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
from satyrn.core.Operations.ArgType import ArgType

class SimpleAggregationPlanGenerator:
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


    # generate very simple plans (retrieve at most 2 aggregates of attrs)
    def generate_simple_aggregation_plans(self,
                                 ent: RingEntity,
                                 n_plans: int,
                                 filter_proportion: float = 0.5,
                                 max_attrs_per_ent: int = 3,
                                groupby_proportion: float = 0.85,
                                 groupby_having_proportion: float = 0.3,
                                 ) -> List[Dict]:
        """
        Generates simple plans that retrieve combinations of aggregated attributes.
        :param ent: The entity to generate the plans for.
        :type ent: RingEntity
        :param n_plans: The number of plans to generate.
        :type n_plans: int
        :param filter_proportion: The proportion of plans that should have filters added to them.
        :type filter_proportion: float
        # TODO: add param
        :return: A list of dictionaries that look like: { "questions": [], "plan": {}, "base_plan": "" }
        :rtype: List[Dict]
        """

        questions_and_plans = []

        available_attributes = [attr for attr_name, attr in ent.attributes.items() if not attr.is_derived()]
        # num_grouped = int(groupby_proportion * n_plans)
        for i in range(n_plans):
            
            # Determine how many attributes to retrieve at random
            if available_attributes:
                n_attrs = random.choice(range(1, min(len(available_attributes), max_attrs_per_ent + 1)))
                sampled_attributes = random.sample(available_attributes, k=n_attrs)
            else:
                raise ValueError(f"No available attributes for entity {ent.name}")
            
            # TODO: check this is comprehensive
            # temporarily handle issue with using count_all in isolation
            general_agg_ops = ["count", "count_unique", "count_all"] if len(sampled_attributes) > 1 else ["count", "count_unique"]
            arithmetic_agg_ops = ["sum", "min", "max", "average"]
            random.shuffle(general_agg_ops)
            random.shuffle(arithmetic_agg_ops)

            sampled_agg_ops = []

            for attr in sampled_attributes:
                if ArgType.Arithmetic in attr.type:
                    op = arithmetic_agg_ops.pop(0)
                else:
                    op = general_agg_ops.pop(0)
                sampled_agg_ops.append(op)


            # Init the plan template
            p = {
                "|1|": f"(retrieve_entity {ent.name})"
            }


            # TODO: debug these plans - occasionally get errors when using count_all???
            # issue when only thing selected from a table is count_all - not sure why but should fix

            # Add the sampled attributes to the plan and keep track of the steps to collect
            retrieve_refs = []
            for step_num, attr in enumerate(sampled_attributes, start=2):
                step_ref = f"|{step_num}|"
                retrieve_refs.append(step_ref)
                p[step_ref] = f"(retrieve_attribute |1| {attr.name})"

            use_groupby = random.random() < groupby_proportion
            # use_groupby = i < num_grouped
            groupby_step_ref = None
            groupby_attr = None
            groupby_attr_retrieve_step = None
            use_having_count_all = use_groupby and random.random() < groupby_having_proportion
            if use_groupby:
                groupable_attrs = [attr for attr_name, attr in ent.attributes.items() if not attr.is_derived() and attr_name not in ent.id and ArgType.Categorical in attr.type]
                if groupable_attrs:
                    groupby_attr = random.choice(groupable_attrs)
                    groupby_attr_retrieve_step = f"|{len(p.keys()) + 1}|"
                    p[groupby_attr_retrieve_step] = f"(retrieve_attribute |1| {groupby_attr.name})"
                    groupby_step_ref = f"|{len(p.keys()) + 1}|"
                    p[groupby_step_ref] = f"(groupby |{len(p.keys())}|)"
                    


            # aggregate retrieved attrs
            collect_args = []
            for step_num, (op, ref) in enumerate(zip(sampled_agg_ops, retrieve_refs), start=len(p.keys()) + 1):
                step_ref = f"|{step_num}|"
                retrieve_refs.append(step_ref)
                p[step_ref] = f"({op} {ref}{(' ' + groupby_step_ref) if groupby_step_ref else ''})"
                collect_args.append(step_ref)

            # need to handle case wehre id is removed from attributes due in condensed rings
            if use_having_count_all and groupby_step_ref and ent.id[0] in ent.attributes.keys():
                p[f"|{len(p.keys()) + 1}|"] = f"(retrieve_attribute |1| {ent.id[0]})"
                count_all_ref = f"|{len(p.keys()) + 1}|"
                p[count_all_ref] = f"(count_all |{len(p.keys())}| {groupby_step_ref})"
                having_op, having_op_template = random.choice([
                    ("exact", "exactly {1} {0}"),
                    ("greaterthan", "more than {1} {0}"),
                    ("greaterthan_eq", "at least {1} {0}"),
                    ("lessthan", "less than {1} {0}"),
                    ("lessthan_eq", "at most {1} {0}"),
                ])
                having_val = random.randint(1,5)
                having_step_ref = f"|{len(p.keys()) + 1}|"
                p[having_step_ref] = f"({having_op} {count_all_ref} {having_val})"
                having_expr = " with " + having_op_template.format(ent.nicename[1], having_val)
            else:
                having_step_ref = None
                having_expr = ""

            # Add the collect and return statements to the plan
            collect_step_ref = f"|{len(p.keys()) + 1}|"
            
            p[collect_step_ref] = f"(collect {(groupby_attr_retrieve_step + ' ') if groupby_attr_retrieve_step else ''}{' '.join(collect_args)})"
            p[f"|{len(p.keys()) + 1}|"] = f"(return {collect_step_ref}{(' ' + having_step_ref) if having_step_ref else ''})"

            # Generate the question
            if not groupby_attr:
                qs = [f"For {ent.nicename[1]}, what {'is' if len(sampled_attributes) == 1 else 'are'} the {oxfordcomma([self.operation_ontology.resolve_operation(op).template.format(attr.nicename[0]) for op, attr in zip(sampled_agg_ops, sampled_attributes)])}?",
                      f"What {'is' if len(sampled_attributes) == 1 else 'are'} the {oxfordcomma([self.operation_ontology.resolve_operation(op).template.format(attr.nicename[0]) for op, attr in zip(sampled_agg_ops, sampled_attributes)])} for {ent.nicename[1]}?"]
            else:
                # collect_description = oxfordcomma([groupby_attr.nicename[1]] + [self.operation_ontology.resolve_operation(op).template.format(attr.nicename[0]) for op, attr in zip(sampled_agg_ops, sampled_attributes)])
                collect_description = oxfordcomma([self.operation_ontology.resolve_operation(op).template.format(attr.nicename[0]) for op, attr in zip(sampled_agg_ops, sampled_attributes)])
                qs = [f"For each {ent.nicename[0]} {groupby_attr.nicename[0]}{having_expr}, what are the {collect_description}?",
                      f"What are the {collect_description} for each {ent.nicename[0]} {groupby_attr.nicename[0]}{having_expr}?"]

            # print(p)
            # print(q)
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

                # Update the question to include the filter
                if not filter_expression:
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
            d["source"] = "SimpleAggregationPlanGenerator"

        return questions_and_plans
