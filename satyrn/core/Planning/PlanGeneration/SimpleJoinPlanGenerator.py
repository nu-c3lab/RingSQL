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

class SimpleJoinPlanGenerator:
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


    def get_related_ents(self,
                         ent: RingEntity,
                         max_length:int,
                         remove_ambiguous_joins:bool=True) -> List[RingEntity]:
        """
        Returns a list of entities indirectly related to the given entity (by two or more joins).
        :param ent: The entity to find related entities for.
        :type ent: RingEntity
        :return: A list of entites indirectly related to ent.
        :rtype: List[RingEntity]
        """
        related_ents = []
        # want outer query to be on this entity, where one col is in a subquery on another entity
        for e in self.ring.entities:
            if e == ent:
                continue
            try:
                path = self.ring.relationship_graph.get_path(ent.name, e.name)
                if len(path) > max_length:
                    continue
            except:
                continue
        
            # ignore entities related through multiple direct paths (length 1) if needed
            
            # print(path)
            # if len(path) > 1:
            # TODO: handle ambiguos joins
            # if remove_ambiguous_joins and len(paths) != 1:
                # continue
            # else:
                # related_ents.append(e)
            rel_types = []
            intermediate_ent = None
            for r in path:
                rel = self.ring.get_relationship_by_name(r)
                if not intermediate_ent:
                    if rel.fro == ent.name:
                        intermediate_ent = rel.to
                        rel_types.append(rel.type)
                    elif rel.to == ent.name:
                        intermediate_ent = rel.fro
                        rel_types.append(rel.type[::-1])
                else:
                    if rel.fro == intermediate_ent:
                        intermediate_ent = rel.to
                        rel_types.append(rel.type)
                    elif rel.to == intermediate_ent:
                        intermediate_ent = rel.fro
                        rel_types.append(rel.type[::-1])
            # print(path)
            # print(rel_types)
            related_ents.append({"related_ent": e.name, "rel_type": self.simplify_rel_type(rel_types)})
            
            # rel_info = {"path": path, "from": ent.name, "to": e.name}
                # print("FROM:", ent.name)
                # print("TO:", e.name)
                
            # related_ents.append(rel_info)

        return related_ents
    
    def simplify_rel_type(self, rel_types):
        # cases:
        #   -   o2o o2o -> o2o
        #   -   o2o o2m -> o2m
        #   -   o2o m2o -> m2o
        #   -   o2o m2m -> m2m

        #   -   o2m o2o -> o2m
        #   -   o2m o2m -> o2m
        #   -   o2m m2o -> m2m
        #   -   o2m m2m -> m2m

        #   -   m2m o2o -> m2m
        #   -   m2m o2m -> m2m
        #   -   m2m m2o -> m2m
        #   -   m2m m2m -> m2m

        #   -   m2o o2o -> m2o
        #   -   m2o o2m -> m2m
        #   -   m2o m2o -> m2o
        #   -   m2o m2m -> m2m

        if len(rel_types) == 1:
            return rel_types[0]
        
        if "m2m" in rel_types:
            return "m2m"
        
        collapsed_rel_types = [t for t in rel_types if t != "o2o"]
        if len(collapsed_rel_types) == 0:
            return "o2o"
        
        for rel_type in collapsed_rel_types[1:]:
            if rel_type != collapsed_rel_types[0]:
                return "m2m"
        
        return collapsed_rel_types[0]


    # may need to change plan based on type of rels used? m2o o2m different than o2o o2o
    def generate_simple_join_plans(self,
                                 ent: RingEntity,
                                 n_plans: int,
                                 filter_proportion: float = 0.5,
                                 groupby_having_proportion: float = 0.3,
                                 distinct_proportion: float = 0.1,
                                 aggregate_proportion: float = 0.1) -> List[Dict]:
        """
        Generates plans that retrieve combinations of non-derived attributes from multiple related entities.
        :param ent: The entity to generate the plans for.
        :type ent: RingEntity
        :param n_plans: The number of plans to generate.
        :type n_plans: int
        :param filter_proportion: The proportion of plans that should have filters added to them.
        :type filter_proportion: float
        :return: A list of dictionaries that look like: { "questions": [], "plan": {}, "base_plan": "" }
        :rtype: List[Dict]
        """

        questions_and_plans = []

        # ent_id_atts = []
        # for att_type in [ArgType.Identifier, ArgType.CompositeIdentifier]:
        #     ent_id_atts.extend(ent.get_attributes_with_type(att_type))

        # for simple plans only consider paths of length 1
        # may want to increase this for more complex examples
        related_ents = self.get_related_ents(ent, max_length=1)
        # print(related_ents)
        # for e in related_ents:
            # print(self.simplify_rel_type(e["type"]))
        if len(related_ents) == 0:
            raise ValueError(f"No related entities available for entity {ent.name}")
              

        for i in range(n_plans):
            
            related_ent_info = random.choice(related_ents)
            # print(related_ent_info)

            # m2m - select from 1 or 2 tables, filter or sort on other?
            # when selecting from multiple tables need to determine relationships between them??

            # o2m - group by the o, return agg info from the many with info from the o 
            #               - or filter on agg info or both
            # m2o - in this case return aggregate info on the many, for o2m return info about the one, filtered on the many
            related_ent = self.ring.get_entity_by_name(related_ent_info["related_ent"])
            
            # use rel_type to allow for group bys
            rel_type = related_ent_info["rel_type"]
            
            # TODO: handle this better
            # reduces the number of joins with group bys to be closer to spider
            # they have many more simple joins
            if rel_type in ["o2m", "m2o"]:
                if random.random() < 0.4:
                    # if random.random() < 1:
                    rel_type = "m2m"
            
            # print(rel_type)
            
            if rel_type in ["m2m", "o2o"]:
                ent_available_attributes = [attr for attr_name, attr in ent.attributes.items() if not attr.is_derived()]
                related_ent_available_attributes = [attr for attr_name, attr in related_ent.attributes.items() if not attr.is_derived()]
                # no grouping, filter on rel_ent
                n_ent_attrs = random.randint(1, min(3, len(ent_available_attributes)))
                n_rel_ent_attrs = random.randint(0, min(1, len(related_ent_available_attributes)))
            
            elif rel_type == "o2m":
                ent_available_attributes = [attr for attr_name, attr in ent.attributes.items() if not attr.is_derived() and attr_name not in ent.id]
                related_ent_available_attributes = [attr for attr in related_ent.get_attributes_with_type(ArgType.Arithmetic) if not attr.is_derived()]
                # group on ent.id, filter on rel_ent
                n_ent_attrs = random.randint(1, min(2, len(ent_available_attributes)))
                n_rel_ent_attrs = random.randint(0, min(1, len(related_ent_available_attributes)))

            elif rel_type == "m2o":
                ent_available_attributes = [attr for attr in ent.get_attributes_with_type(ArgType.Arithmetic) if not attr.is_derived()]
                related_ent_available_attributes = [attr for attr_name, attr in related_ent.attributes.items() if not attr.is_derived() and attr_name not in related_ent.id]
                # group on rel_ent.id, filter on rel_ent
                n_ent_attrs = random.randint(1, min(2, len(ent_available_attributes)))
                n_rel_ent_attrs = random.randint(0, min(1, len(related_ent_available_attributes)))

            # ent_available_attributes = [attr for attr_name, attr in ent.attributes.items() if not attr.is_derived()]
            # related_ent_available_attributes = [attr for attr_name, attr in related_ent.attributes.items() if not attr.is_derived()]
            
            # Determine how many attributes to retrieve at random
            
            if ent_available_attributes:
                # cap sampled atts to 3
                # n_attrs = random.randint(2, min(3, len(ent_available_attributes)))
                ent_sampled_attributes = random.sample(ent_available_attributes, n_ent_attrs)
            else:
                raise ValueError(f"No available attributes for entity {ent.name}")
            
            
            if related_ent_available_attributes:
                # cap sampled atts to 3
                # n_attrs = random.randint(1, min(2, len(related_ent_available_attributes)))
                related_ent_sampled_attributes = random.sample(related_ent_available_attributes, n_rel_ent_attrs)
            else:
                related_ent_sampled_attributes = []
            
            # Get the set of attributes to retrieve
            # may not always want id atts - especially if wanting to aggregate
            # p1_sampled_attributes = ent_id_atts + random.sample(available_attributes, n_attrs)

            # print(ent_sampled_attributes)
            # print(intermediate_ent_sampled_attributes)
            # print(related_ent_sampled_attributes)


            # plan outline

            # MANY TO MANY

            # p1
            # retreive ent
            # retrieve selected atts from ent
            # <optional> retrieve intermediate ent
            # retrieve atts from intermediate ent
            
            # p2
            # retrieve related ent
            # filter on related ent
            # return p1 with p2 filter


            # ONE TO MANY
            # retreive ent
            # retrieve selected atts from ent
            # retrieve related ent
            # retrieve selected atts from related ent
            # group by ent
            # aggregate related ent atts and return
            
            # MANY TO ONE
            # retrieve ent
            # retreive selected atts from ent
            # retrieve related ent
            # groupby related ent
            # return aggregates for ent (optionally filter on aggregates for ent)

            
            p = {
                "|1|": f"(retrieve_entity {ent.name})",
            }

            # Add the sampled attributes to the plan and keep track of the steps to collect
            ent_collect_args = []
            
            
            for step_num, attr in enumerate(ent_sampled_attributes, start=2):
                step_ref = f"|{step_num}|"
                ent_collect_args.append(step_ref)
                p[step_ref] = f"(retrieve_attribute |1| {attr.name})"

            # add related ent attrs if needed
            if related_ent_sampled_attributes:
                related_ent_collect_args = []
                related_ent_retrieve_step = len(p.keys()) + 1
                related_ent_retrieve_ref = f"|{related_ent_retrieve_step}|"
                p[related_ent_retrieve_ref] = f"(retrieve_entity {related_ent.name})"
                for step_num, attr in enumerate(related_ent_sampled_attributes, start=related_ent_retrieve_step + 1):
                    step_ref = f"|{step_num}|"
                    related_ent_collect_args.append(step_ref)
                    p[step_ref] = f"(retrieve_attribute {related_ent_retrieve_ref} {attr.name})"
            else:
                related_ent_collect_args = []
                related_ent_retrieve_ref = None

            # TODO: check this is comprehensive
            agg_ops = ["count", "count_unique", "count_all", "min", "max", "sum", "average"]
            string_agg_ops = ["count", "count_unique"]

            filter_ref = None
            selected_agg_ops = []
            use_having_count_all = random.random() < groupby_having_proportion
            # group by and aggregate if needed
            if rel_type == "o2m":
                if related_ent_sampled_attributes or use_having_count_all:
                    # aggregate related ent attrs
                    ent_ids = ent.id
                    ent_id_refs = []
                    
                    for id_attr in ent_ids:
                        next_step_num = len(p.keys()) + 1
                        next_step_ref = f"|{next_step_num}|"
                        p[next_step_ref] = f"(retrieve_attribute |1| {id_attr})"
                        ent_id_refs.append(next_step_ref)

                    groupby_step_num = len(p.keys()) + 1
                    groupby_step_ref = f"|{groupby_step_num}|"
                    p[groupby_step_ref] = f"(groupby {' '.join(ent_id_refs)})"

                    ent_collect_args += ent_id_refs

                    related_ent_agg_refs = []
                    for ref in related_ent_collect_args:
                        next_step_num = len(p.keys()) + 1
                        next_step_ref = f"|{next_step_num}|"
                        op = random.choice(agg_ops)
                        selected_agg_ops.append(op)
                        p[next_step_ref] = f"({op} {ref} {groupby_step_ref})"
                        related_ent_agg_refs.append(next_step_ref)

                    related_ent_collect_args = related_ent_agg_refs

                    if use_having_count_all:
                        # add having count(*) filter on related ent
                        if not related_ent_retrieve_ref:
                            related_ent_retrieve_ref = f"|{len(p.keys()) + 1}|"
                            p[related_ent_retrieve_ref] = f"(retrieve_entity {related_ent.name})"
                        
                        p[f"|{len(p.keys()) + 1}|"] = f"(retrieve_attribute {related_ent_retrieve_ref} {related_ent.id[0]})"

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
                        filter_ref = f"|{len(p.keys()) + 1}|"
                        p[filter_ref] = f"({having_op} {count_all_ref} {having_val})"
                        having_expr = " with " + having_op_template.format(related_ent.nicename[1], having_val)
                    else:
                        having_expr = ""

                    # generate question

                    q1 = f"For {ent.nicename[1]}{having_expr}, what {'is' if len(ent_sampled_attributes + ent.id) == 1 else 'are'} the {oxfordcomma([attr.nicename[0] for attr in ent_sampled_attributes + [ent.attributes[e] for e in ent.id]])}"
                    q1 += f" along with the {oxfordcomma([self.operation_ontology.resolve_operation(op).template.format(attr.nicename[0]) for op, attr in zip(selected_agg_ops, related_ent_sampled_attributes)])}?"
                    

                    all_attr_nicenames = [attr.nicename[0] for attr in ent_sampled_attributes + [ent.attributes[e] for e in ent.id]] + [self.operation_ontology.resolve_operation(op).template.format(attr.nicename[0] if attr.name not in ent.attributes else related_ent.nicename[0] + ' ' + attr.nicename[0]) for op, attr in zip(selected_agg_ops, related_ent_sampled_attributes)]
                    q2 = f"What {'is' if len(all_attr_nicenames) == 1 else 'are'} the {oxfordcomma(all_attr_nicenames)} for each {ent.nicename[0]}?"
                    qs = [q1, q2]
                    # question += f" along with the {oxfordcomma([self.operation_ontology.resolve_operation(op).template.format(attr.nicename[0]) for op, attr in zip(selected_agg_ops, related_ent_sampled_attributes)])} for corresponding {related_ent.nicename[1]}?"
                else:
                    q1 = f"For each {ent.nicename[0]}, what {'is' if len(ent_sampled_attributes + ent.id) == 1 else 'are'} the {oxfordcomma([attr.nicename[0] for attr in ent_sampled_attributes + [ent.attributes[e] for e in ent.id]])}?"
                    q2 = f"What {'is' if len(ent_sampled_attributes + ent.id) == 1 else 'are'} the {oxfordcomma([attr.nicename[0] for attr in ent_sampled_attributes + [ent.attributes[e] for e in ent.id]])} for {ent.nicename[1]}?"
                    qs = [q1, q2]
        
            
            elif rel_type == "m2o":
                # aggregate ent attrs
                related_ent_ids = related_ent.id
                related_ent_id_refs = []
                if not related_ent_retrieve_ref:
                    related_ent_retrieve_ref = f"|{len(p.keys()) + 1}|"
                    p[related_ent_retrieve_ref] = f"(retrieve_entity {related_ent.name})"

                for id_attr in related_ent_ids:
                    next_step_num = len(p.keys()) + 1
                    next_step_ref = f"|{next_step_num}|"
                    p[next_step_ref] = f"(retrieve_attribute {related_ent_retrieve_ref} {id_attr})"
                    related_ent_id_refs.append(next_step_ref)

                groupby_step_num = len(p.keys()) + 1
                groupby_step_ref = f"|{groupby_step_num}|"
                p[groupby_step_ref] = f"(groupby {' '.join(related_ent_id_refs)})"

                related_ent_collect_args += related_ent_id_refs

                ent_agg_refs = []
                for ref in ent_collect_args:
                    next_step_num = len(p.keys()) + 1
                    next_step_ref = f"|{next_step_num}|"
                    op = random.choice(agg_ops)
                    selected_agg_ops.append(op)
                    p[next_step_ref] = f"({op} {ref} {groupby_step_ref})"
                    ent_agg_refs.append(next_step_ref)
                
                if use_having_count_all:
                    # add having count(*) filter on related ent
                    
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
                    filter_ref = f"|{len(p.keys()) + 1}|"
                    p[filter_ref] = f"({having_op} {count_all_ref} {having_val})"
                    having_expr = " with " + having_op_template.format(ent.nicename[1], having_val)
                else:
                    having_expr = ""

                # add condition for filtering - do this at the end
                # filter_ref = f"|{len(p.keys()) + 1}|"
                # filter_arg_idx = random.randint(0, len(ent_collect_args) - 1)
                # filter_attr = ent.attributes[p[ent_collect_args[filter_arg_idx]].strip("()").split()[-1]]
                # # print(filter_attr)

                # filter_operation = self.filter_generator.get_filter_operation(filter_attr)
        
                # # Get a random valid value for this attribute
                # filter_value = self.filter_generator.get_filter_value(filter_attr, filter_operation)
                # # print(filter_operation)
                # if not isinstance(filter_value, tuple):
                #     filter_value = tuple([filter_value])
                # # print(filter_value)

                # filter_step = f"({filter_operation} {ent_agg_refs[filter_arg_idx]} {' '.join([str(v) for v in filter_value])})"
                # # print(filter_step)
                # p[filter_ref] = filter_step

                ent_collect_args = ent_agg_refs

                # TODO: sample which to filter?
                # generate expression for filter
                # if filtered:
                # filter_template = self.operation_ontology.resolve_operation(filter_operation).template
                # print(filter_template)
                # filter_agg_template = self.operation_ontology.resolve_operation(selected_agg_ops[filter_arg_idx]).template
                # print(filter_agg_template)
                # filter_expr = filter_template.format(filter_agg_template.format(ent_sampled_attributes[filter_arg_idx].nicename[0]), *filter_value)
                # print(filter_expr)
                # remove attr being used in filter from collect
                # ent_collect_args.pop(filter_arg_idx)
                # ent_sampled_attributes.pop(filter_arg_idx)
                # selected_agg_ops.pop(filter_arg_idx)

                # generate question
                # question = f"For {ent.nicename[1]}, what {'is' if len(ent_sampled_attributes) == 1 else 'are'} the {oxfordcomma([self.operation_ontology.resolve_operation(op).template.format(attr.nicename[0]) for op, attr in zip(selected_agg_ops, ent_sampled_attributes)])}"
                q1 = f"What {'is' if len(ent_sampled_attributes) == 1 else 'are'} the {oxfordcomma([self.operation_ontology.resolve_operation(op).template.format(attr.nicename[0]) for op, attr in zip(selected_agg_ops, ent_sampled_attributes)])}"
                
                if related_ent_sampled_attributes:
                    q1 += f" along with the {oxfordcomma([attr.nicename[0] for attr in related_ent_sampled_attributes + [related_ent.attributes[e] for e in related_ent.id]])} for each {related_ent.nicename[0]}{having_expr}?"
                else:
                    q1 += f" along with the {oxfordcomma([attr.nicename[0] for attr in [related_ent.attributes[e] for e in related_ent.id]])} for each {related_ent.nicename[0]}{having_expr}?"

                all_attr_nicenames = [self.operation_ontology.resolve_operation(op).template.format(attr.nicename[0] if attr.name not in related_ent.attributes else ent.nicename[0] + ' ' + attr.nicename[0]) for op, attr in zip(selected_agg_ops, ent_sampled_attributes)] + [attr.nicename[0] for attr in related_ent_sampled_attributes + [related_ent.attributes[e] for e in related_ent.id]]

                q2 = f"What {'is' if len(all_attr_nicenames) == 1 else 'are'} the {oxfordcomma(all_attr_nicenames)} for {related_ent.nicename[1]}{having_expr}"

                qs = [q1, q2]

                # if filtered:
                # print(self.operation_ontology.resolve_operation(filter_operation).template)
                # question = question[:-1] + f" with {filter_expr}?"
                
                # oxfordcomma([self.operation_ontology.resolve_operation(op).template.format(attr.nicename[0]) for op, attr in zip(selected_agg_ops, related_ent_sampled_attributes)])
                # oxfordcomma([attr.nicename[0] for attr in ent_sampled_attributes])

            elif rel_type in ["m2m", "o2o"]:
                mode = random.choices(["distinct", "agg", None], [distinct_proportion, aggregate_proportion, 1 - distinct_proportion - aggregate_proportion], k=1)[0]
                # generate question
                # question = f"For {ent.nicename[1]}, what {'is' if len(ent_sampled_attributes) == 1 else 'are'} the {oxfordcomma([attr.nicename[0] for attr in ent_sampled_attributes])}"
                # question += f" for {related_ent.nicename[1]}?"
                if mode is None:
                    q1 = f"What {'is' if len(ent_sampled_attributes + related_ent_sampled_attributes) == 1 else 'are'} the {oxfordcomma([attr.nicename[0] for attr in ent_sampled_attributes + related_ent_sampled_attributes])}?"
                    all_attr_nicenames = [attr.nicename[0] if attr.name not in related_ent.attributes else ent.nicename[0] + ' ' + attr.nicename[0] for attr in ent_sampled_attributes] + [attr.nicename[0] if attr.name not in ent.attributes else related_ent.nicename[0] + ' ' + attr.nicename[0] for attr in related_ent_sampled_attributes]
                    q2 = f"Can you tell me what {'is' if len(ent_sampled_attributes + related_ent_sampled_attributes) == 1 else 'are'} the {oxfordcomma(all_attr_nicenames)}?"
                    qs = [q1, q2]
                elif mode == "distinct":
                    # print("DISTINCT")
                    # TODO: wrap all collected things in distinct?
                    distinct_phrases = random.choices(["unique ", "distinct ", "different "], k=2)
                    q1 = f"What {'is' if len(ent_sampled_attributes + related_ent_sampled_attributes) == 1 else 'are'} the {distinct_phrases[0]} {oxfordcomma([attr.nicename[0] for attr in ent_sampled_attributes + related_ent_sampled_attributes])}?"
                    all_attr_nicenames = [attr.nicename[0] if attr.name not in related_ent.attributes else ent.nicename[0] + ' ' + attr.nicename[0] for attr in ent_sampled_attributes] + [attr.nicename[0] if attr.name not in ent.attributes else related_ent.nicename[0] + ' ' + attr.nicename[0] for attr in related_ent_sampled_attributes]
                    q2 = f"Can you tell me what {'is' if len(ent_sampled_attributes + related_ent_sampled_attributes) == 1 else 'are'} the {distinct_phrases[1]} {oxfordcomma(all_attr_nicenames)}?"
                    distinct_collect_step_ref = f"|{len(p.keys()) + 1}|"
                    p[distinct_collect_step_ref] = f"(distinct {' '.join(ent_collect_args + related_ent_collect_args)})"
                    ent_collect_args = [distinct_collect_step_ref]
                    related_ent_collect_args = []
                    qs = [q1, q2]
                elif mode == "agg":
                    # TODO: wrap each retrieved collect arg in agg?
                    ent_agg_refs = []
                    ent_agg_ops = []
                    related_ent_agg_refs = []
                    related_ent_agg_ops = []
                    # print(ent.get_attributes_with_type(ArgType.Arithmetic))
                    for attr_retrieve_ref, is_arith in zip(ent_collect_args, [a in ent.get_attributes_with_type(ArgType.Arithmetic) for a in ent_sampled_attributes]):
                        agg_ref = f"|{len(p.keys()) + 1}|"
                        agg_op = random.choice(agg_ops if is_arith else string_agg_ops)
                        ent_agg_refs.append(agg_ref)
                        ent_agg_ops.append(agg_op)
                        p[agg_ref] = f"({agg_op} {attr_retrieve_ref})"
                    
                    for attr_retrieve_ref, is_arith in zip(related_ent_collect_args, [a in related_ent.get_attributes_with_type(ArgType.Arithmetic) for a in related_ent_sampled_attributes]):
                        agg_ref = f"|{len(p.keys()) + 1}|"
                        agg_op = random.choice(agg_ops if is_arith else string_agg_ops)
                        related_ent_agg_refs.append(agg_ref)
                        related_ent_agg_ops.append(agg_op)
                        p[agg_ref] = f"({agg_op} {attr_retrieve_ref})"
                    
                    # TODO: update language
                    ent_agg_phrases = [self.operation_ontology.resolve_operation(op).template.format(attr.nicename[0]) for op, attr in zip(ent_agg_ops, ent_sampled_attributes)]
                    related_ent_agg_phrases = [self.operation_ontology.resolve_operation(op).template.format(attr.nicename[0]) for op, attr in zip(related_ent_agg_ops, related_ent_sampled_attributes)]
                    q1 = f"What {'is' if len(ent_sampled_attributes + related_ent_sampled_attributes) == 1 else 'are'} the {oxfordcomma(ent_agg_phrases + related_ent_agg_phrases)}?"
                    all_attr_nicenames = [self.operation_ontology.resolve_operation(op).template.format(attr.nicename[0] if attr.name not in related_ent.attributes else ent.nicename[0] + ' ' + attr.nicename[0]) for attr, op in zip(ent_sampled_attributes, ent_agg_ops)] + [self.operation_ontology.resolve_operation(op).template.format(attr.nicename[0] if attr.name not in ent.attributes else related_ent.nicename[0] + ' ' + attr.nicename[0]) for attr, op in zip(related_ent_sampled_attributes, related_ent_agg_ops)]
                    # q2 = f"Can you tell me what {'is' if len(ent_sampled_attributes + related_ent_sampled_attributes) == 1 else 'are'} the {oxfordcomma([attr.nicename[0] for attr in ent_sampled_attributes + related_ent_sampled_attributes])}?"
                    q2 = f"Can you tell me what {'is' if len(ent_sampled_attributes + related_ent_sampled_attributes) == 1 else 'are'} the {oxfordcomma(all_attr_nicenames)}?"
                    qs = [q1, q2]
                    ent_collect_args = ent_agg_refs
                    related_ent_collect_args = related_ent_agg_refs
            else:
                raise ValueError(f"Unhandled relation type {rel_type}")


            all_collect_args = ent_collect_args + related_ent_collect_args
            # Add the collect and return statements to the plan
            collect_step_ref = f"|{len(p.keys()) + 1}|"
            p[collect_step_ref] = f"(collect {' '.join(all_collect_args)})"
            return_step_ref = f"|{len(p.keys()) + 1}|"
            p[return_step_ref] = f"(return {collect_step_ref} {filter_ref})" if filter_ref else f"(return {collect_step_ref})"
            # print(p)
            parsed_plan = self.analysis_plan_parser.parse(p)

            use_filter = random.random() < filter_proportion
            # if rel_type == "m2m":
            if filter_proportion or not related_ent_sampled_attributes:
                # build filter on related_ent
                filter_steps, filter_expression = self.filter_generator.build_filter_with_entity(related_ent)
                parsed_filter = self.analysis_plan_parser.create_analysis_steps(filter_steps)

                # Add the filter to the plan
                plan_with_filter = self.sqr_composer.compose_filter_and_access_plan(parsed_plan.plan_steps, parsed_filter)
                # update question with filter
                parsed_plan = self.analysis_plan_parser.parse_from_analysis_steps(plan_with_filter)
                # TODO: may need some reference to the related ent if none exists already?
                if not filter_expression:
                    qs = [self.question_generator.generate_question(q,
                                                                    {},
                                                                    parsed_plan,
                                                                    filter_steps) for q in qs]
                else:
                    qs = [self.question_generator.combine_filter_expression_with_question(q, filter_expression) for q in qs]
            # print(parsed_plan.plan_steps)
            # print(question)
            out = {
                "base_plan": None,
                "plan": parsed_plan,
                # "filter_ent": related_ent,
                "questions": qs,
            }
            # print(out)
            questions_and_plans.append(out)


        # Finish processing the plans
        for d in questions_and_plans:
            # Renumber the steps of the plan
            # d["plan"] = self.analysis_plan_parser.parse_from_analysis_steps(self.sqr_compiler._renumber(d["plan"].plan_steps))

            # Add source to the output
            d["source"] = "SimpleJoinPlanGenerator"

        return questions_and_plans
