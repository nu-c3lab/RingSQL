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
import networkx as nx

class SetOperationPlanGenerator:
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
        self.directly_related_cols = self.get_directly_related_cols()
        self.related_col_graph = self.get_related_col_graph()

    def get_related_ents(self,
                         ent: RingEntity,
                         remove_ambiguous_joins: bool=True) -> List[RingEntity]:
        """
        Returns a list of entities directly related to the given entity on the many side of a relationship.
        :param ent: The entity to find related entities for.
        :type ent: RingEntity
        :param remove_ambiguos_joins: Whether to include related entities with multiple direct join paths to the given entity.
        :type remove_ambiguos_joins: bool
        :return: A list of entites directly related to ent.
        :rtype: List[RingEntity]
        """
        related_ents = []
        # want outer query to be on this entity, where one col is in a subquery on another entity
        for e in self.ring.entities:
            if e == ent:
                continue
            try:
                paths = self.ring.relationship_graph.get_all_direct_paths(e.name, ent.name)
            except:
                continue
        
            # ignore entities related through multiple direct paths (length 1) if needed
            if remove_ambiguous_joins and len(paths) != 1:
                continue
            else:
                if paths:
                    path = paths[0][0]
                    # find relationship object
                    rel = None
                    for temp_rel in self.ring.relationships:
                        if temp_rel.name == path:
                            rel = temp_rel
                    if rel:
                        to_many = False
                        if rel.fro == ent.name:
                            to_many = rel.type[-1] == "m"
                        elif rel.to == ent.name:
                            to_many = rel.type[0] == "m"
                        if to_many:
                            related_ents.append(e)
        return related_ents
    
    def get_directly_related_cols(self):
        directly_related_cols = []
        for join in self.ring.data_source.joins:
            for path in join.path:
                directly_related_cols.append([path[0], path[1]])
        
        return directly_related_cols

    def get_related_col_graph(self):
        graph = nx.Graph()
        for rel in self.directly_related_cols:
            graph.add_edge(rel[0], rel[1])
        return graph

    
    def get_indirectly_related_attrs(self, ent: RingEntity):
        # get indirectly related attrs for each ent attr
        # along with attrs of same name that aren't ids nor are directly related
        related_attr_info = {}
        directly_related_cols = self.directly_related_cols

        # find indirectly related cols

        for attr_name, attr in ent.attributes.items():
            # skip derived attrs and attrs with multiple cols
            if attr.is_derived() or len(attr.source_columns) != 1:
                continue
            attr_col_ref = attr.source_table + "." + attr.source_columns[0]
            for other_ent in self.ring.entities:
                if other_ent == ent:
                    continue
                
                other_attr = None
                for other_name, rel_attr in other_ent.attributes.items():
                    # skip derived attrs
                    if rel_attr.is_derived():
                        continue
                    other_attr_col_ref = rel_attr.source_table + "." + rel_attr.source_columns[0]
                    # skip id cols and cols with different names unless they are indirectly related
                    # always skip directly related cols
                    # chack if cols are indirectly related
                    try:
                        indirectly_related = len(self.related_col_graph.shortest_path(source=attr_col_ref, target=other_attr_col_ref)) > 1
                    except:
                        indirectly_related = False
                    if (
                            ("id" not in attr_name.lower() and attr_name.lower() == other_name.lower()) 
                            or indirectly_related
                        ) and [other_attr_col_ref, attr_col_ref] not in directly_related_cols and [attr_col_ref, other_attr_col_ref] not in directly_related_cols:
                        other_attr = rel_attr
                        break
                if other_attr:
                    if other_ent.name not in related_attr_info:
                        related_attr_info[other_ent.name] = {"ent": other_ent, "related_attrs": [{"ent_attr": attr, "related_attr": other_attr}]}
                    else:
                        related_attr_info[other_ent.name]["related_attrs"].append({"ent_attr": attr, "related_attr": other_attr})
        
                # TODO: get all indirectly related attrs too
        return related_attr_info
    
    def generate_retrieval_plans_for_attrs(self, ent, attrs, subplan):
        retrieve_ent_ref = f"|1{subplan}|"
        p = {retrieve_ent_ref: f"(retrieve_entity {ent.name})"}
        collect_args = []
        for i, attr in enumerate(attrs, start=2):
            step_ref = f"|{i}{subplan}|"
            p[step_ref] = f"(retrieve_attribute {retrieve_ent_ref} {attr.name})"
            collect_args.append(step_ref)
        
        collect_step_ref = f"|{len(p.keys()) + 1}{subplan}|"
        p[collect_step_ref] = f"(collect {' '.join(collect_args)})"
        
        return_step_ref = f"|{len(p.keys()) + 1}{subplan}|"
        p[return_step_ref] = f"(return {collect_step_ref})"

        return p, return_step_ref

    # set op plans - improved version
    def generate_set_operation_plans(self,
                                 ent: RingEntity,
                                 n_plans: int,
                                 filter_proportion: float = 0.5,
                                 max_attrs: int = 3,) -> List[Dict]:
        """
        Generates plans that retrieve combinations of non-derived attributes.
        :param ent: The entity to generate the plans for.
        :type ent: RingEntity
        :param n_plans: The number of plans to generate.
        :type n_plans: int
        :param filter_proportion: The proportion of plans that should have filters added to them.
        :type filter_proportion: float
        :return: A list of dictionaries that look like: { "questions": [], "plan": {}, "base_plan": "" }
        :rtype: List[Dict]
        """

        # idea:
        #   - spider seems to use 1 col mostly, 2 occasionally and 3 rarely
        #   - intersect plans for "and" on many side of rels (optionally with different filters)
        #       -   and for and across same col name for different tables?
        #       -   for "and" on non-unique cols (value can appear in multiple rows with different vals for other columns)
        #       -   similar concept for joins?
        #   - their excepts can all be covered with not ins
        #       -   treat them as negated intersects (_ and not _)
        #   - many of their unions can be covered with ORs
        #       -   same column name (not directly related or using a many join) but combined with or condition on rows
        #   - unions and excepts should use different, non-directly related cols - can be indirectly related or have same name


        questions_and_plans = []

        related_attr_info = self.get_indirectly_related_attrs(ent)
        
        multi_related_attrs = {k: v for k, v in related_attr_info.items() if len(v["related_attrs"]) > 1}
        single_related_attrs = {k: v for k, v in related_attr_info.items() if len(v["related_attrs"]) == 1}
        
        related_entities = self.get_related_ents(ent)
        
        # 4 cases - if both multi rel attrs and rel ents, randomly choose
        # - if only one of them, use that one
        # - else only use a single rel attr but can only do a union
        if multi_related_attrs and related_entities:
            plan_type_options = ["multi_attr", "rel_ent"]
        elif multi_related_attrs:
            plan_type_options = ["multi_attr"]
        elif related_entities:
            plan_type_options = ["rel_ent"]
        elif single_related_attrs:
            plan_type_options = ["single_attr"]
        else:
            # TODO: allow selecting non-id categorical col with different filters?
            # could use intersects/excepts here with those or handle this case with in plans?
            plan_type_options = []

        if not plan_type_options:
            raise ValueError(f"Entity {ent.name} has no attributes or entites to make a reasonable set operation plan.")

        filter_proportion = max(min(filter_proportion, 1.0), 0.0)

        for _ in range(n_plans):
            
            plan_type = random.choice(plan_type_options)

            if plan_type == "rel_ent":
                set_ops = ["except", "intersect"]
                available_attributes = [attr for attr_name, attr in ent.attributes.items() if not attr.is_derived()]

                # Determine how many attributes to retrieve at random
                # retrieve at least 2 so an IN plan wouldn't suffice
                n_attrs = random.randint(2, min(len(available_attributes), max_attrs))
                
                # Get the set of attributes to retrieve
                # may want to exclude ids to reduce null intersect plans?
                # sampled_attributes = ent_id_atts + random.sample(available_attributes, n_attrs)
                sampled_attributes = random.sample(available_attributes, n_attrs)

                p1_sampled_attributes = sampled_attributes.copy()
                p1_ent = ent
                p2_sampled_attributes = sampled_attributes.copy()
                p2_ent = ent
            
            elif plan_type == "multi_attr":
                set_ops = ["except", "intersect", "union"]
                sampled_attrs_key = random.choice(list(multi_related_attrs.keys()))
                sampled_attrs_info = multi_related_attrs[sampled_attrs_key]
                p1_ent = ent
                p1_sampled_attributes = [a["ent_attr"] for a in sampled_attrs_info["related_attrs"]]
                p2_ent = sampled_attrs_info["ent"]
                p2_sampled_attributes = [a["related_attr"] for a in sampled_attrs_info["related_attrs"]]
            
            elif plan_type == "single_attr":
                set_ops = ["union"]
                sampled_attr_key = random.choice(list(single_related_attrs.keys()))
                sampled_attr_info = single_related_attrs[sampled_attr_key]
                p1_ent = ent
                p1_sampled_attributes = [a["ent_attr"] for a in sampled_attr_info["related_attrs"]]
                p2_ent = sampled_attr_info["ent"]
                p2_sampled_attributes = [a["related_attr"] for a in sampled_attr_info["related_attrs"]]
            
            p1, p1_return_ref = self.generate_retrieval_plans_for_attrs(p1_ent, p1_sampled_attributes, "A")
            p2, p2_return_ref = self.generate_retrieval_plans_for_attrs(p2_ent, p2_sampled_attributes, "B")
            parsed_p1 = self.analysis_plan_parser.parse(p1)
            parsed_p2 = self.analysis_plan_parser.parse(p2)

            set_op = random.choice(set_ops)
            set_op_exprs = {
                "except": ["have", "but not"],
                "intersect": ["have both", "and"],
                "union": ["have either", "or"],
            }[set_op]
            q1s = [f"Which {oxfordcomma([a.nicename[1] for a in p1_sampled_attributes])} {set_op_exprs[0]} {p1_ent.nicename[1]}?",
                   f"Can you give me the {oxfordcomma([a.nicename[1] for a in p1_sampled_attributes])} that {set_op_exprs[0]} {p1_ent.nicename[1]}?"]
            q2s = [f"{set_op_exprs[1]} {p2_ent.nicename[1]}?", f"{set_op_exprs[1]} {p2_ent.nicename[1]}?"]
            q3s = ["",""]
            # print(q1)
            # TODO: add filters for rel_ent plans or according to filter prop
            if plan_type == "rel_ent":
                p1_rel_ent = random.choice(related_entities)
                p2_rel_ent = random.choice(related_entities)
                p1_filter_steps, p1_filter_expression = self.filter_generator.build_filter_with_entity(p1_rel_ent, max_atomic_filters=1)
                p2_filter_steps, p2_filter_expression = self.filter_generator.build_filter_with_entity(p2_rel_ent, max_atomic_filters=1)
                q1s = [f"What are the {oxfordcomma([a.nicename[1] for a in p1_sampled_attributes])} for {p1_ent.nicename[1]} that {set_op_exprs[0]} {p1_rel_ent.nicename[1]}?",
                       f"For {p1_ent.nicename[1]} that {set_op_exprs[0]} {p1_rel_ent.nicename[1]}?"]
                q3s = ["", f", what are the {oxfordcomma([a.nicename[1] for a in p1_sampled_attributes])}"]
                # q1 = f"What {oxfordcomma([a.nicename[1] for a in p1_sampled_attributes])} {set_op_exprs[0]} {p1_ent.nicename[1]}?"
                if p1_rel_ent == p2_rel_ent:
                    q2s = [f"{set_op_exprs[1]}?", f"{set_op_exprs[1]}?"]
                else:
                    q2s = [f"{set_op_exprs[1]} {p2_rel_ent.nicename[1]}?",
                           f"{set_op_exprs[1]} {p2_rel_ent.nicename[1]}?"]

            elif random.random() < filter_proportion:
                    # sometimes sample to only filter on one?
                    p1_filter_steps, p1_filter_expression = self.filter_generator.build_filter_with_entity(p1_ent, max_atomic_filters=1)
                    p2_filter_steps, p2_filter_expression = self.filter_generator.build_filter_with_entity(p2_ent, max_atomic_filters=1)
            
            else:
                p1_filter_steps = []
                p1_filter_expression = ""
                p2_filter_steps = []
                p2_filter_expression = ""

            if p1_filter_steps:
                p1_parsed_filter = self.analysis_plan_parser.create_analysis_steps(p1_filter_steps)
                p1_with_filter = self.sqr_composer.compose_filter_and_access_plan(
                    parsed_p1.plan_steps,
                    p1_parsed_filter,
                )
                if not p1_filter_expression:
                    q1s = [self.question_generator.generate_question(q1, {}, parsed_p1, p1_filter_steps) for q1 in q1s]
                else:
                    q1s = [self.question_generator.combine_filter_expression_with_question(q1, p1_filter_expression) for q1 in q1s]

            else:
                p1_with_filter = parsed_p1.plan_steps
            
            if p2_filter_steps:
                p2_parsed_filter = self.analysis_plan_parser.create_analysis_steps(p2_filter_steps)
                p2_with_filter = self.sqr_composer.compose_filter_and_access_plan(
                    parsed_p2.plan_steps,
                    p2_parsed_filter,
                )
                if not p2_filter_expression:
                    q2s = [self.question_generator.generate_question(q2, {}, parsed_p2, p2_filter_steps) for q2 in q2s]
                else:
                    q2s = [self.question_generator.combine_filter_expression_with_question(q2, p2_filter_expression) for q2 in q2s]

            else:
                p2_with_filter = parsed_p2.plan_steps
        
            # combined_plan = {**p1, **p2}
            combined_plan = {**p1_with_filter, **p2_with_filter}

            final_return_step_dict = self.analysis_plan_parser.create_analysis_steps({f"|{len(combined_plan.keys())}|": f"({set_op} {p1_return_ref} {p2_return_ref})"})
            combined_plan.update(final_return_step_dict)
            
            # print(combined_plan)
            qs = [f"{q1[:-1]} {q2[0].lower()}{q2[1:-1]}{q3}?" for q1, q2, q3 in zip(q1s, q2s, q3s)]

            # Store the question and plan pair
            out = {
                "base_plan": None,
                # "subplans": [self.analysis_plan_parser.parse(p1), self.analysis_plan_parser.parse(p2)],
                "plan": self.analysis_plan_parser.parse_from_analysis_steps(combined_plan),
                # "subquestions": [q1, q2],
                "questions": qs
                # "related_entity": related_ent
            }
            questions_and_plans.append(out)

        # Finish processing the plans
        for d in questions_and_plans:
            # Renumber the steps of the plan
            d["plan"] = self.analysis_plan_parser.parse_from_analysis_steps(self.sqr_compiler._renumber(d["plan"].plan_steps))

            # Add source to the output
            d["source"] = "SetOperationPlanGenerator"

        return questions_and_plans