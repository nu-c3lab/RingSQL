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
from satyrn.core.Operations.ArgType import ArgType

class InOperationPlanGenerator:
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


    def get_related_attrs_for_ent(self, 
                                  ent: RingEntity,
                                  remove_ambiguous_joins: bool=False) -> List[List]:
        """
        Returns a list of lists containing information about attributes from 
        other entities that are directly related to attributes of the given 
        entity.
        :param ent: The entity to find related attributes for.
        :type ent: RingEntity
        :param remove_ambiguos_joins: Whether to include attributes for the given entity with multiple directly related attributes in a single related entity.
        :type remove_ambiguos_joins: bool
        :return: A list of lists that look like: [<related_entity>, "<related_ent_name>.<related_attribute>", "<corresponding_attribute_for_ent>"]
        :rtype: List[List]
        """
        related_atts = []
        # want outer query to be on this entity, where one col is in a subquery on another entity
        for e in self.ring.entities:
            if e == ent:
                continue
            # if no valid path ignore other entity
            try:
              paths = self.ring.relationship_graph.get_all_direct_paths(e.name, ent.name)
            except:
                continue
        
            # ignore entities related through multiple direct paths (length 1) if needed
            if remove_ambiguous_joins and len(paths) != 1:
                continue

            for rel in self.ring.relationships:
                if [rel.name] in paths:
                    for join in self.ring.data_source.joins:
                        # assume no multi column joins
                        if len(join.path) > 1:
                            continue
                        
                        if join.name == rel.join[0]:
                            
                            for att_name, value in e.attributes.items():
                                if value.source_columns and len(value.source_columns) == 1:
                                    att_table_ref = value.source_table + "." + value.source_columns[0]

                                    if att_table_ref in join.path[0]:
                                        from_att_name = e.name + "." + att_name
                                        break
                                    
                            for att_name, value in ent.attributes.items():
                                if value.source_columns and len(value.source_columns) == 1:
                                    att_table_ref = value.source_table + "." + value.source_columns[0]
                                    
                                    if att_table_ref in join.path[0]:
                                        to_att_name = att_name
                                        to_att = value
                                        break
                                    
                            related_atts.append([e, from_att_name, to_att_name])

        return related_atts

    # in/not in plans
    def generate_in_operation_plans(self,
                                 ent: RingEntity,
                                 n_plans: int,
                                 filter_proportion: float = 0.5,
                                 negate_proportion: float = 0.5,
                                 max_attrs:int=2,) -> List[Dict]:
        """
        Generates plans that retrieve combinations of non-derived attributes filtered using an in operation.
        :param ent: The entity to generate the plans for.
        :type ent: RingEntity
        :param n_plans: The number of plans to generate.
        :type n_plans: int
        :param filter_proportion: The proportion of plans that should have filters added to them.
        :type filter_proportion: float
        :param negate_proportion: The proportion of plans that should use a negated IN condition.
        :type negate_proportion: float
        :return: A list of dictionaries that look like: { "questions": [], "plan": {}, "base_plan": "" }
        :rtype: List[Dict]
        """

        questions_and_plans = []

        ent_id_atts = []
        for att_type in [ArgType.Identifier, ArgType.CompositeIdentifier]:
            ent_id_atts.extend(ent.get_attributes_with_type(att_type))

        related_atts = self.get_related_attrs_for_ent(ent, remove_ambiguous_joins=False)
        if len(related_atts) == 0:
            raise ValueError(f"No related attributes available for entity {ent.name}")
              
        # Make sure the proportion is between 0.0 and 1.0
        negate_proportion = max(min(negate_proportion, 1.0), 0.0)

        # Determine the number of specs that should have filters added to them
        num_to_negate = int(negate_proportion * n_plans)

        for i in range(n_plans):
            
            related_att_info = random.choice(related_atts)

            # index 0 is related entity
            related_ent = related_att_info[0]
            # index 1 is "<related_ent_name>.<related_att>"
            related_att_name = related_att_info[1].split(".")[-1]
            related_att = related_ent.attributes[related_att_name]
            # index 2 is att in current entity
            in_att_name = related_att_info[2]
            in_attr = ent.attributes[in_att_name]

            available_attributes = [attr for attr_name, attr in ent.attributes.items() if not attr.is_derived() and attr not in ent_id_atts]

            # Determine how many attributes to retrieve at random
            if available_attributes:
                n_attrs = random.randint(1, min(len(available_attributes), max_attrs))
                p1_sampled_attributes = ent_id_atts + random.sample(available_attributes, n_attrs)
            else:
                p1_sampled_attributes = ent_id_atts
            
            # Get the set of attributes to retrieve
            # may not always want id atts - especially if wanting to aggregate
            # p1_sampled_attributes = ent_id_atts + random.sample(available_attributes, n_attrs)

            p2_sampled_attributes = [related_ent.attributes[related_att_name]]

            
            
            # p2 outline
            # retreive related entity
            # retrieve related entity attributes (including att to be used for in)
            # filter on some conditions
            # return att to be used for in op with filter

            # p1 outline
            # retrieve entity of interest
            # retrieve atts
            # filter with in/not in ops
            # collect atts
            # return atts with in/not in filter
            # optionally perform any aggregation on returned atts - not done

            # Init the subplan template
            p1 = {
                "|1|": f"(retrieve_entity {ent.name})",
            }

            # Add the sampled attributes to the plan and keep track of the steps to collect
            p1_collect_args = []
            
            # retrieve in_attr
            p1_retrieve_in_attr_ref = "|2|"

            p1[p1_retrieve_in_attr_ref] = f"(retrieve_attribute |1| {in_attr.name})"
            for step_num, attr in enumerate(p1_sampled_attributes, start=3):
                step_ref = f"|{step_num}|"
                p1_collect_args.append(step_ref)
                p1[step_ref] = f"(retrieve_attribute |1| {attr.name})"

            # Add the collect and return statements to the plan
            p1_collect_step_ref = f"|{len(p1.keys()) + 1}|"
            p1[p1_collect_step_ref] = f"(collect |2| {' '.join(p1_collect_args)})"
            p1[f"|{len(p1.keys()) + 1}|"] = f"(return {p1_collect_step_ref})"
            
            p2_first_step_num = len(p1.keys()) + 1
            # Init the subplan template
            p2 = {
                f"|{p2_first_step_num}|": f"(retrieve_entity {related_ent.name})",
            }

            p2_collect_args = []
            for step_num, attr in enumerate(p2_sampled_attributes, start=p2_first_step_num + 1):
                step_ref = f"|{step_num}|"
                p2_collect_args.append(step_ref)
                p2[step_ref] = f"(retrieve_attribute |{p2_first_step_num}| {attr.name})"

            p2_collect_step_ref = f"|{len(p1.keys()) + len(p2.keys()) + 1}|"
            p2[p2_collect_step_ref] = f"(collect {' '.join(p2_collect_args)})"
            p2[f"|{len(p1.keys()) + len(p2.keys()) + 1}|"] = f"(return {p2_collect_step_ref})"

            negate = i < num_to_negate

            # Generate the question
            q1s = [f"What are the {oxfordcomma([attr.nicename[1] for attr in p1_sampled_attributes])} for {ent.nicename[1]}?",
                   f"For {ent.nicename[1]}?"]
            # q2 = f"with {in_attr.nicename[1]} {'not in' if negate else 'in'} the {related_att.nicename[1]} of {related_ent.nicename[1]}"
            # more spider-like wording
            linking_phrases = random.choices(["without", "with no", "that don't have"] if negate else ["with", "that have"], k=2)
            q2s = [f"{linking_phrases[0]} {related_ent.nicename[1]}?",
            f"{linking_phrases[1]} {related_ent.nicename[1]}?"]
            q3s = ["", f", what are the {oxfordcomma([attr.nicename[0] for attr in p1_sampled_attributes])}"]
            # Store the question and plan pair
            out = {
                "base_plan": None,
                "subplans": [self.analysis_plan_parser.parse(p1), self.analysis_plan_parser.parse(p2)],
                "subquestions": [q1s, q2s, q3s],
                "p1_retrieve_in_attr_ref": p1_retrieve_in_attr_ref,
                "p1_collect_step_ref": p1_collect_step_ref,
                "p2_ent": related_ent,
                "negate": negate,
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
        # if num_to_filter > 0:
        #     random.shuffle(questions_and_plans)
        for i, q_p in enumerate(questions_and_plans):
            # Generate the filter (if possible)
            # number of plans with filters on p1 determined using filter_proportion
            # if i < num_to_filter:
            # randomly sample whether to filter
            if random.random() < filter_proportion:
                p1_filter_steps = self.filter_generator.build_filter_with_entity(ent)
                p2_filter_steps = self.filter_generator.build_filter_with_entity(q_p.pop("p2_ent"))
            else:
                p1_filter_steps = []
                p2_filter_steps = []
            
            parsed_p1, parsed_p2 = [p.plan_steps for p in q_p.pop("subplans")]

            p1_initial_return_ref = self.analysis_plan_parser.get_leaves(self.analysis_plan_parser.create_plan_graph(parsed_p1))[0]
            p1_retrieve_in_attr_ref = q_p.pop("p1_retrieve_in_attr_ref")
            p1_collect_step_ref = q_p.pop("p1_collect_step_ref")
            
            if len(p1_filter_steps) > 0:

                # Parse the access plan and filters into the necessary representation for composition
                p1_parsed_filter = self.analysis_plan_parser.create_analysis_steps(p1_filter_steps)

                # Add the filter to the plan
                p1_with_filter = self.sqr_composer.compose_filter_and_access_plan(parsed_p1, p1_parsed_filter)

            else:
                p1_with_filter = parsed_p1

            if len(p2_filter_steps) > 0:
                # Parse the access plan and filters into the necessary representation for composition
                p2_parsed_filter = self.analysis_plan_parser.create_analysis_steps(p2_filter_steps)

                # Add the filter to the plan
                p2_with_filter = self.sqr_composer.compose_filter_and_access_plan(parsed_p2,
                                                                                    p2_parsed_filter)
            else:
                p2_with_filter = parsed_p2

            combined_plan = {**p1_with_filter, **p2_with_filter}
            p1_return_step = combined_plan.pop(p1_initial_return_ref)
            p1_final_filter_step = p1_return_step.args[1] if len(p1_return_step.args) > 1 else None
            # remove in attr from p1 collect step
            combined_plan[p1_collect_step_ref].args.pop(0)
            
            p2_final_return_ref = self.analysis_plan_parser.get_leaves(self.analysis_plan_parser.create_plan_graph(p2_with_filter))[0]

            # TODO: clean up this mess
            if p2_filter_steps:
                in_steps = (({
                        f"|{len(combined_plan.keys())}|": f"(in {p1_retrieve_in_attr_ref} {p2_final_return_ref})",
                        f"|{len(combined_plan.keys()) + 1}|": f"(not |{len(combined_plan.keys())}|)",
                        f"|{len(combined_plan.keys()) + 2}|": f"(and {p1_final_filter_step} |{len(combined_plan.keys()) + 1}|)",
                        f"|{len(combined_plan.keys()) + 3}|": f"(return {p1_collect_step_ref} |{len(combined_plan.keys()) + 2}|)"
                    } if p1_final_filter_step else {
                        f"|{len(combined_plan.keys())}|": f"(in {p1_retrieve_in_attr_ref} {p2_final_return_ref})",
                        f"|{len(combined_plan.keys()) + 1}|": f"(not |{len(combined_plan.keys())}|)",
                        f"|{len(combined_plan.keys()) + 2}|": f"(return {p1_collect_step_ref} |{len(combined_plan.keys()) + 1}|)"
                    }) if q_p.pop("negate") else
                    ({
                        f"|{len(combined_plan.keys())}|": f"(in {p1_retrieve_in_attr_ref} {p2_final_return_ref})",
                        f"|{len(combined_plan.keys()) + 1}|": f"(and {p1_final_filter_step} |{len(combined_plan.keys())}|)",
                        f"|{len(combined_plan.keys()) + 2}|": f"(return {p1_collect_step_ref} |{len(combined_plan.keys()) + 1}|)"
                    } if p1_final_filter_step else {
                        f"|{len(combined_plan.keys())}|": f"(in {p1_retrieve_in_attr_ref} {p2_final_return_ref})",
                        f"|{len(combined_plan.keys()) + 1}|": f"(return {p1_collect_step_ref} |{len(combined_plan.keys())}|)"
                    }))
            else:
                in_steps = (({
                        f"|{len(combined_plan.keys()) + 2}|": f"(in {p1_retrieve_in_attr_ref} {p2_final_return_ref})",
                        f"|{len(combined_plan.keys()) + 3}|": f"(not |{len(combined_plan.keys()) + 2}|)",
                        f"|{len(combined_plan.keys()) + 4}|": f"(and {p1_final_filter_step} |{len(combined_plan.keys()) + 3}|)",
                        f"|{len(combined_plan.keys()) + 5}|": f"(return {p1_collect_step_ref} |{len(combined_plan.keys()) + 4}|)"
                    } if p1_final_filter_step else {
                        f"|{len(combined_plan.keys()) + 2}|": f"(in {p1_retrieve_in_attr_ref} {p2_final_return_ref})",
                        f"|{len(combined_plan.keys()) + 3}|": f"(not |{len(combined_plan.keys()) + 2}|)",
                        f"|{len(combined_plan.keys()) + 4}|": f"(return {p1_collect_step_ref} |{len(combined_plan.keys()) + 3}|)"
                    }) if q_p.pop("negate") else
                    ({
                        f"|{len(combined_plan.keys()) + 2}|": f"(in {p1_retrieve_in_attr_ref} {p2_final_return_ref})",
                        f"|{len(combined_plan.keys()) + 3}|": f"(and {p1_final_filter_step} |{len(combined_plan.keys()) + 1}|)",
                        f"|{len(combined_plan.keys()) + 4}|": f"(return {p1_collect_step_ref} |{len(combined_plan.keys()) + 3}|)"
                    } if p1_final_filter_step else {
                        f"|{len(combined_plan.keys()) + 2}|": f"(in {p1_retrieve_in_attr_ref} {p2_final_return_ref})",
                        f"|{len(combined_plan.keys()) + 3}|": f"(return {p1_collect_step_ref} |{len(combined_plan.keys()) + 2}|)"
                    }))

            final_return_step_dict = self.analysis_plan_parser.create_analysis_steps(in_steps)
            combined_plan.update(final_return_step_dict)
            # print(combined_plan)
            # Convert it to an AnalysisPlan object
            q_p["plan"] = self.analysis_plan_parser.parse_from_analysis_steps(combined_plan)
            
            q1s, q2s, q3s = q_p.pop("subquestions")
            # print(p1_filter_steps)
            q1s = [self.question_generator.generate_question(q1, {}, parsed_p1, p1_filter_steps) for q1 in q1s]
            # print(p2_filter_steps)
            q2s = [self.question_generator.generate_question(q2, {}, parsed_p2, p2_filter_steps) for q2 in q2s]

            q_p["questions"] = [f"{q1[:-1]} {q2[0].lower()}{q2[1:-1]}{q3}?" for q1, q2, q3 in zip(q1s, q2s, q3s)]


        # Finish processing the plans
        for d in questions_and_plans:
            # Renumber the steps of the plan
            d["plan"] = self.analysis_plan_parser.parse_from_analysis_steps(self.sqr_compiler._renumber(d["plan"].plan_steps))

            # Add source to the output
            d["source"] = "InOperationPlanGenerator"

        return questions_and_plans
