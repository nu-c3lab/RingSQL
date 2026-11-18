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
from copy import deepcopy
import re

class OrderByPlanAugmenter:
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
    def augment_plans_with_order_by(self,
                                    questions_and_plans,
                                    augment_proportion,
                                    limit_proportion: float = 0.9,
                                    remove_sort_attr_proportion: float =0.5,
                                #  ent: RingEntity,
                                #  n_plans: int,
                                #  filter_proportion: float = 0.5,
                                #  max_attrs_per_ent: int = 2,
                                 ) -> List[Dict]:
        """
        Augments plans with order by and limit clauses.
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
        # print(questions_and_plans)
        augment_idxs = random.sample(range(len(questions_and_plans)), int(len(questions_and_plans) * augment_proportion))
        # limit_idxs = random.sample(augment_idxs, int(len(augment_idxs) * limit_proportion))

        # print(augment_idxs)
        # print(int(len(augment_idxs) * limit_proportion))

        # print("limit:", limit_idxs)

        for i in augment_idxs:
                
                q_p = questions_and_plans[i]
                # print(q_p["plan"])
                plan = q_p["plan"]
                # plan = self.analysis_plan_parser.parse_from_analysis_steps(q_p["plan"])
                # print(plan)
                # print(type(plan))
                
                final_return_ref = plan.get_leaves()
                assert len(final_return_ref) == 1
                final_return_ref = final_return_ref[0]

                # penultimate_steps = self.analysis_plan_parser.get_parents(plan.plan_steps[final_return_ref], plan.plan_steps)
                final_return_step = plan.plan_steps[final_return_ref]
                final_collect_step_ref = plan.plan_steps[final_return_ref].args[0]
                # print(final_collect_step_ref)
                final_collect_step = plan.plan_steps[final_collect_step_ref]
                sortable_args = []
                already_sorted = False
                # for arg_ref in final_collect_step.args:
                # only allow first or last so language is better
                for arg_ref in [final_collect_step.args[c_idx] for c_idx in [0, -1]]:
                    # print(arg_ref)
                    # print(plan.plan_steps[arg_ref].operation)
                    # print(self.operation_ontology.resolve_operation(plan.plan_steps[arg].operation))
                    # print(self.operation_ontology.resolve_operation(plan.plan_steps[arg].operation).output_args)
                    sortable = True
                    # TODO: dont allow sorting on aggregations unless they are grouped
                    for arg in self.operation_ontology.resolve_operation(plan.plan_steps[arg_ref].operation).output_args:
                        #  print(arg.arg_types)
                         if ArgType.Sort in arg.arg_types or ArgType.Limit in arg.arg_types:
                              already_sorted = True
                              break
                        #  TODO: may be other types of args that aren't sortable so check that
                        # might be eaiser to specify types that are sortable for safer results
                         if ArgType.Filter in arg.arg_types or ArgType.AttributeCollection in arg.arg_types:
                              sortable = False
                              break
                    if sortable:
                         sortable_args.append(arg_ref)
                    
                    # print(sortable_args)
                # if count_all in sortable args, sort by it
                for a in sortable_args:
                    if plan.plan_steps[a].operation == "count_all":
                        sortable_args = [a]
                        break

                # print("sortable:", sortable_args)
                
                if not already_sorted and sortable_args:
                    # TODO: make sure issues arent cause by subplans 
                    # - plans should already be numbered fine for this but double check
                    sort_arg_ref = random.choice(sortable_args)
                    sort_arg_collect_idx = final_collect_step.args.index(sort_arg_ref)
                    sorted_plan = deepcopy(plan)
                    sort_direction = random.choice(["asc", "desc"])
                    # sorted_plan.plan_steps[final_return_ref] = self.analysis_plan_parser.create_analysis_steps({final_return_ref: f"(sort {sort_arg_ref} {sort_direction})"})[final_return_ref]
                    
                    # use this instead?
                    sort_attr = self.question_generator.statement_generator.step_expressor.get_attribute_name(sort_arg_ref, plan)
                    sort_attr_ent = self.question_generator.statement_generator.step_expressor.get_entity_name(sort_arg_ref, plan)
                    # print(sort_attr)
                    sort_attr_nicenames = self.ring.get_entity_by_name(sort_attr_ent).attributes[sort_attr].nicename
                    # print("nicenames:", sort_attr_nicenames)
                    sort_attr_name_singular = sort_attr_nicenames[0]
                    sort_attr_name_plural = sort_attr_nicenames[1]
                    

                    # try to resolve original attribute type specific question string
                    sorted_by_step = plan.plan_steps[sort_arg_ref]
                    # print(sorted_by_step)
                    # check for retrieve_attribute up to one parent up from sorted by step
                    if sorted_by_step.operation == "retrieve_attribute":
                        retrieve_attr_step = sorted_by_step
                    elif sorted_by_step.operation == "groupby":
                        # TODO: handle grouping by multiple attrs
                        if len(sorted_by_step.args) == 1:
                            retrieve_attr_step = plan.plan_steps[sorted_by_step.args[0]]
                        else:
                            retrieve_attr_step = None
                    else:
                        retrieve_attr_step = None
                    # this causes counts of string attrs to use alphabetical in question
                    # since no aggs return str types, assume all strs are reffed directly by retrieve ops
                    # else:
                    #     # assumes all directly retreived attrs use in an agg are of same type
                    #     retrieve_attr_step = None
                    #     parents = self.analysis_plan_parser.get_parents(sorted_by_step, plan.plan_steps)
                    #     # print(parents)
                    #     for p in parents:
                    #         if p.operation == "retrieve_attribute":
                    #             retrieve_attr_step = p
                    #             break

                                # print("sorted by:", sorted_by_step)
                                # print("parents:", )
                    if retrieve_attr_step:
                        # print(retrieve_attr_step)
                        retrieve_ent_steps = self.analysis_plan_parser.get_parents(retrieve_attr_step, plan.plan_steps)
                        # print(retrieve_ent_steps)
                        assert len(retrieve_ent_steps) == 1
                        retrieved_ent_name = retrieve_ent_steps[0].args[0]
                        retrieve_attr_name = retrieve_attr_step.args[1]
                        # print(retrieved_ent_name)
                        # print(retrieve_attr_name)
                        sorted_by_attr = self.ring.get_entity_by_name(retrieved_ent_name).attributes[retrieve_attr_name]
                        # print(sorted_by_attr)
                    else:
                        sorted_by_attr = None




                    sorted_return_step = deepcopy(final_return_step)

                    # if i in limit_idxs:
                    # randomly sample limits
                    if random.random() < limit_proportion:
                        limit_step_ref = f"|{len(plan.plan_steps.keys()) + 1}|"
                        limit_num = random.choice([1, 3, 5, 10])
                        limit_step = f"(limit {limit_num})"
                        sorted_return_ref = f"|{len(plan.plan_steps.keys()) + 2}|"
                        sorted_return_step.args.extend([final_return_ref, limit_step_ref])
                    else:
                        limit_step_ref = None
                        sorted_return_ref = f"|{len(plan.plan_steps.keys()) + 1}|"
                        sorted_return_step.args.append(final_return_ref)
                                   
                    sort_steps = {final_return_ref: f"(sort {sort_arg_ref} {sort_direction})",
                                  sorted_return_ref: str(sorted_return_step)}
                    if limit_step_ref:
                        sort_steps[limit_step_ref] = limit_step

                    # sample whether to remove sorted by val from returned values
                    remove_sort_attr_from_collect = random.random() < remove_sort_attr_proportion
                    # get expression for sort attr nicename
                    full_sort_attr_expr = self.question_generator.statement_generator.step_expressor.express_step(sort_arg_ref, plan)
                    # print(full_sort_attr_expr)

                    # full_sort_attr_expr, sort_order_expr = sort_step_statement.split(" sorted in ")
                    # sort_expr = f"sorted by {sort_ent_expr} in {sort_order_expr}"
                    # print(full_sort_attr_expr)
                    sort_attr_expr = full_sort_attr_expr.split("grouped by")[0].strip()
                    if not sort_attr_expr:
                        sort_attr_expr = full_sort_attr_expr.split("grouped by")[1].strip()
                    sort_attr_expr_plural = sort_attr_expr.replace(sort_attr_name_singular.lower(), sort_attr_name_plural.lower())
                    # print(sort_attr_expr_plural)
                    # skip access plans and multi join plans due to poor handling of language here
                    if remove_sort_attr_from_collect and q_p["source"] not in ["AccessPlanGenerator", "MultiJoinPlanGenerator"]:
                        num_og_collect_args = len(plan.plan_steps[final_collect_step_ref].args)
                        # only remove if there are other attrs collected
                        if num_og_collect_args > 1:
                            # fix questions
                            # doesn't work for:
                            #   -   access plans - when sorting by id - when not sorting by id resulting question would be empty?
                            #   -   multi join plans - need some way of differentiating attrs with same names in different ents?
                            # simplist fix may be just to skip ordering in these cases
                            #   - relatively infrequent for multi-joins
                            #   - may want to skip this for all access plans
                            sort_attr_re = re.compile(f"(?:(the| and|,(?: and)?|corresponding)( {sort_attr_expr.lower()}| {sort_attr_expr_plural.lower()})( and|, (?:and)?| with|\?| for| along with))")
                            updated_questions = []
                            sort_attr_removable = True
                            for q in q_p["questions"]:
                                
                                # print(q)
                                matches = list(re.finditer(sort_attr_re, q.lower()))
                                if len(matches) != 1:
                                    print("WARNING: not exactly one re match found in question so skipping")
                                    print(q.lower())
                                    print(sort_attr_expr.lower())
                                    print(sort_attr_expr_plural.lower())
                                    print(matches)
                                    sort_attr_removable = False
                                    break
                                # TODO: need some special handling based on matched groups to change language?
                                # group 1: (the|and|,(?: and)?|corresponding)
                                # group 3: ( and|, (?:and)?| with|\?| for| along with)
                                # current issues:
                                #   - need to replace "are" with is if only 1 remaining attr?
                                #   - if removing and may need to insert it earlier?
                                match = matches[0]
                                # print(q)
                                m1 = match.group(1)
                                m3 = match.group(3)
                                # print(f"'{m1}'")
                                # print(f"'{m3}'")
                                start_idx, end_idx = match.span(2)
                                # TODO: if removing and need to add it earlier on?
                                if m1 in [",", " and", ", and"]:
                                    start_idx = match.span()[0]
                                if m3 in [" and", ", and"]:
                                    # special handling for ands depending on num collect args
                                    # if num_og_collect_args == 2:
                                    if sort_arg_collect_idx == 0:
                                        end_idx = match.span()[1]
                                    elif num_og_collect_args == 3 and m3 == ", and":
                                        end_idx += 1

                                if m3 in [", "]:
                                    # TODO: special handling for adding and depending on num collect args
                                    end_idx = match.span()[1] - 1

                                # print(f"'{q[start_idx:end_idx]}'")
                                q = q[:start_idx] + q[end_idx:]
                                # print(q)
                                updated_questions.append(q)

                                
                        
                            if sort_attr_removable:
                                sorted_plan.plan_steps[final_collect_step_ref].args.remove(sort_arg_ref)
                                # print(updated_questions)
                                q_p["questions"] = updated_questions
                    # print(sort_steps)

                    sorted_analysis_steps = self.analysis_plan_parser.create_analysis_steps(sort_steps)
                    # sorted_plan.plan_steps[sorted_return_ref] = sorted_return_step
                    for ref, step in sorted_analysis_steps.items():
                         sorted_plan.plan_steps[ref] = step

                    # print(sorted_plan)
                    parsed_sorted_plan = self.analysis_plan_parser.parse_from_analysis_steps(sorted_plan.plan_steps)
                    q_p["plan"] = parsed_sorted_plan
                    
                    # update question with sort

                    # sort_step_statement = self.question_generator.statement_generator.step_expressor.express_step(final_return_ref, parsed_sorted_plan)
                    # print(sort_step_statement)

                    sort_expr = f"sorted by {sort_attr_expr}"
                    # special handling for sorting on strings
                    if sorted_by_attr:
                        # print(sorted_by_attr)
                        # print(sorted_by_attr.isa)
                        # TODO: fix case of count agg an string using this language
                        if sorted_by_attr.isa == "string":
                            sort_expr += " in alphabetical order" if sort_direction == "asc" else " in reverse alphabetical order"
                    # print(sort_expr)

                    # update question with limit steps if needed
                    if limit_step_ref:
                        limit_step_statement = f"top {limit_num}" if sort_direction == "desc" or (sorted_by_attr and sorted_by_attr.isa == "string") else f"bottom {limit_num}"
                        new_questions = []
                        for q in q_p["questions"]:
                            
                            if limit_num > 1 or (sorted_by_attr and sorted_by_attr.isa == "string"):
                                new_q = q[:-1] + " " + sort_expr + "?"
                                if "what is the" in q:
                                    new_q = new_q.replace("what is the", f"what is the {limit_step_statement}", 1)
                                elif "What is the" in q:
                                    new_q = new_q.replace("What is the", f"What is the {limit_step_statement}", 1)
                                elif "what are the" in q:
                                    new_q = new_q.replace("what are the", f"what are the {limit_step_statement}", 1)
                                elif "What are the" in q:
                                    new_q = new_q.replace("What are the", f"What are the {limit_step_statement}", 1)
                                else:
                                    new_q = new_q[:-1] + f", limited to the {'top' if sort_direction == 'desc' or (sorted_by_attr and sorted_by_attr.isa == 'string') else 'bottom'} {limit_num} results?"
                            else:
                                new_q = q[:-1] + f" with the {'highest' if sort_direction == 'desc' else 'lowest'} {sort_attr_expr}?" 
                            new_questions.append(new_q)
                        q_p["questions"] = new_questions
                    else:
                        q_p["questions"] = [q[:-1] + " " + sort_expr + "?" for q in q_p["questions"]]
                        
                    # print(q_p["questions"])


                    
                    # TODO: sometimes remove the arg being sorted - will need to update language and plan accordingly

                    q_p["source"] += "->OrderByPlanAugmenter"


                # Update the question to include the filter
                # q_p["questions"] = [self.question_generator.generate_question(question,
                #                                                              {},
                #                                                              q_p["plan"],
                #                                                              filter_steps) for question in q_p["questions"]]

        # Finish processing the plans
        # for d in questions_and_plans:
        #     # Renumber the steps of the plan
        #     d["plan"] = self.analysis_plan_parser.parse_from_analysis_steps(self.sqr_compiler._renumber(d["plan"].plan_steps))

        #     # Add source to the output
        #     d["source"] = "SimpleAggergationPlanGenerator"

        return questions_and_plans
