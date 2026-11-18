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
import time
from itertools import product
from typing import Dict, List, Optional

from satyrn.core.RingObjects.Ring import Ring
from satyrn.core.RingObjects.RingEntity import RingEntity
from satyrn.core.Planning.SQRComposer import SQRComposer
from satyrn.core.Document.BasePlanStore import BasePlanStore
from satyrn.core.Analysis.OperationOntology import OperationOntology
from satyrn.core.Planning.utils import extract_slots
from satyrn.core.Planning.CompositionSpecification import CompositionSpecification
from satyrn.core.Planning.PlanGeneration.FillerIdentifier import FillerIdentifier
from satyrn.core.Planning.PlanGeneration.FilterGenerator import FilterGenerator
from satyrn.core.Planning.PlanGeneration.ExhaustiveBasePlanInputAssigner import ExhaustiveBasePlanInputAssigner
from satyrn.core.Planning.PlanGeneration.SamplingBasePlanInputAssigner import SamplingBasePlanInputAssigner
from satyrn.core.Planning.PlanGeneration.SlotIdentifier import SlotIdentifier
from satyrn.core.Planning.PlanGeneration.SlotExpressor import SlotExpressor
from satyrn.core.Planning.AnalysisPlanParser import AnalysisPlanParser
from satyrn.core.Planning.QuestionGeneratorTemplateBased import QuestionGeneratorTemplateBased
from satyrn.core.Planning.PlanGeneration.PlanSlot import PlanSlot
from satyrn.core.Planning.PlanGeneration.RetrievalPlanGenerator import RetrievalPlanGenerator
from satyrn.core.Planning.PlanGeneration.GroupingPlanGenerator import GroupingPlanGenerator
from satyrn.core.Planning.PlanGeneration.AccessPlanGenerator import AccessPlanGenerator
from satyrn.core.Planning.PlanGeneration.SetOperationPlanGenerator import SetOperationPlanGenerator
from satyrn.core.Planning.PlanGeneration.InOperationPlanGenerator import InOperationPlanGenerator
from satyrn.core.Planning.PlanGeneration.MultiJoinPlanGenerator import MultiJoinPlanGenerator
from satyrn.core.Planning.PlanGeneration.SimpleAggregationPlanGenerator import SimpleAggregationPlanGenerator
from satyrn.core.Planning.PlanGeneration.SimpleSQLPlanGenerator import SimpleSQLPlanGenerator
from satyrn.core.Planning.PlanGeneration.OrderByPlanAugmenter import OrderByPlanAugmenter
from satyrn.core.Planning.PlanGeneration.SimpleJoinPlanGenerator import SimpleJoinPlanGenerator
from satyrn.core.Planning.PlanGeneration.CacheManager import CacheManager
from satyrn.core.Planning.SQRCompiler import SQRCompiler
from satyrn.core.Planning.PlanGeneration.CustomExceptions import NoValidAttribute
from satyrn.core.Operations.ArgType import ArgType

class PlanGenerator:
    def __init__(self,
                 ring: Ring,
                 operation_ontology: OperationOntology,
                 sqr_composer: SQRComposer,
                 base_plan_store: BasePlanStore,
                 cache_manager: CacheManager = None):
        self.ring = ring
        self.operation_ontology = operation_ontology
        self.sqr_composer = sqr_composer
        self.base_plan_store = base_plan_store
        self.cache_manager = cache_manager if cache_manager else CacheManager(self.ring)
        self.filler_identifier = FillerIdentifier(self.ring, self.operation_ontology, cache_manager=self.cache_manager)
        self.exhaustive_assigner = ExhaustiveBasePlanInputAssigner(self.ring, self.operation_ontology, self.base_plan_store)
        self.sampling_assigner = SamplingBasePlanInputAssigner(self.base_plan_store)
        self.slot_identifier = SlotIdentifier()
        self.slot_expressor = SlotExpressor(self.ring, self.operation_ontology, self.sqr_composer, self.base_plan_store)
        self.filter_generator = FilterGenerator(self.ring, self.operation_ontology, cache_manager=self.cache_manager, base_plan_store=self.base_plan_store, filler_identifier=self.filler_identifier, slot_expressor=self.slot_expressor)
        self.analysis_plan_parser = AnalysisPlanParser(self.operation_ontology)
        self.question_generator = QuestionGeneratorTemplateBased(self.ring, self.operation_ontology, self.base_plan_store)
        self.sqr_compiler = SQRCompiler(self.analysis_plan_parser)

        # Init the other plan generators
        self.retrieval_plan_generator = None
        self.access_plan_generator = None
        self.grouping_plan_generator = None
        self.set_operation_plan_generator = None
        self.in_operation_plan_generator = None
        self.multi_join_plan_generator = None
        self.simple_aggregation_plan_generator = None
        self.order_by_plan_augmenter = None
        self.simple_sql_plan_generator = None
        self.simple_join_plan_generator = None

    def determine_entities_to_use(self,
                                  desired_entities: List[str]) -> List[RingEntity]:
        if len(desired_entities) > 0:
            return [ent for ent in self.ring.entities if ent.name in desired_entities]
        else:
            return [ent for ent in self.ring.entities]

    def determine_base_plans_to_use(self,
                                    desired_base_plans: List[str]) -> Dict:
        if len(desired_base_plans) > 0:
            return {base_plan_name: self.base_plan_store.templates[base_plan_name] for base_plan_name in desired_base_plans}
        else:
            return self.base_plan_store.templates

    def augment_slots_for_composite_id(self, slots, num_ids):
        augmented_slots = []
        for slot in slots:
            if slot[:11] == "{Identifier":
                # TODO: handle cases with multiple composite id entities
                replacements = ["{" + f"CompositeIdentifier[{i}" + slot[13:] for i in range(num_ids)]
                # replace single id slot with multiple slots for each composite id field
                # for i, val in enumerate(filler):
                    # new_slot = "{" + f"CompositeIdentifier[{i}" + slot[13:]
                    # replacements.append(new_slot)
                augmented_slots.extend(replacements)
            else:
                augmented_slots.append(slot)
        return augmented_slots

    def augment_template_for_composite_id(self, template, num_ids):
        words = template.split()
        augmented_words = []
        for word in words:
        

            if word[:11] == "{Identifier":
                # TODO: handle cases with multiple composite id entities
                split_idx = word.index("}") + 1
                punct = word[split_idx:]
                replacements = ["{" + f"CompositeIdentifier[{i}" + word[13:split_idx] for i in range(num_ids)]
                # replace single id slot with multiple slots for each composite id field
                # for i, val in enumerate(filler):
                    # new_slot = "{" + f"CompositeIdentifier[{i}" + slot[13:]
                    # replacements.append(new_slot)
                replacements[-1] += punct
                augmented_words.extend(replacements)
            else:
                augmented_words.append(word)
        return " ".join(augmented_words)

    def augment_plan_for_composite_id(self, plan, num_ids):
        # may want to adjust this with value filling for more sensible questions?
        # sometimes uses part of composite id as a filter when using Instance questions - lots of empty results
        # also may want to select values for both composite id fields at the same time to ensure the entity exists
        if not plan:
            return plan
        slot_replacements = {}
        for k, step in plan.items():
            for arg in step.strip("()").split(" "):
                # check that slot is for an id
                if arg[:11] == "{Identifier":
                    # TODO: may not work if there is a case using multiple entities with different composite ids
                    replacements = ["{" + f"CompositeIdentifier[{i}" + arg[13:] for i in range(num_ids)]
                    # replace single id slot with multiple slots for each composite id field
                    slot_replacements[arg] = replacements
                elif arg[:12] == '"{Identifier':
                    replacements = ['"{' + f"CompositeIdentifier[{i}" + arg[14:] for i in range(num_ids)]
                    slot_replacements[arg] = replacements

        augmented_plan = {}
        replaced_steps = {}
        renamed_steps = {}
        next_step_num = min([int(x.strip("|")) for x in plan.keys()])
        
        for k, step in sorted(plan.items(), key=lambda x: int(x[0].strip("|"))):
            args = step.strip("()").split(" ")
            op = args[0]
            args = args[1:]

            # TODO: assumes only one slot needs to be replaced in each step - should hold
            arg_idx = None
            for i, arg in enumerate(args):
                if arg in slot_replacements:
                    arg_idx = i

            if arg_idx:
                # insert replacement steps using composite slot fillers
                replaced_steps[k] = []
                # handle replaced args
                replaced_arg_idxs = []
                replaced_args = []
                for i, arg in enumerate(args):
                    if arg in replaced_steps:
                        replaced_args.append(replaced_steps[arg])
                        replaced_arg_idxs.append(i)
                
                replacement_fillers = slot_replacements[args[arg_idx]]
                for replacement, replaced_arg in zip(replacement_fillers, *replaced_args) if replaced_args else zip(replacement_fillers, [[]for i in replacement_fillers]):
                    
                    new_k = f"|{next_step_num}|"
                    
                    for j, replaced_arg_idx in enumerate(replaced_arg_idxs):
                        args[replaced_arg_idx] = replaced_arg if type(replaced_arg) != list else replaced_arg[j]
                    args[arg_idx] = replacement
                    
                    augmented_plan[new_k] = "(" + op + " " + " ".join(args) + ")"
                    
                    replaced_steps[k].append(new_k)
                    next_step_num += 1
                if op == "exact":
                    # combine exact ops with and
                    new_k = f"|{next_step_num}|"
                    new_step = "(and " + " ".join(replaced_steps[k]) + ")"
                    augmented_plan[new_k] = new_step
                    replaced_steps[k] = [new_k]
                    next_step_num += 1
                # TODO: handle count/count_unique on part of composite id - may need a concat op?
            else:
                # handle renamed/replaced steps in existing steps
                if op != "retrieve_attribute":
                    idx = 0
                    while idx < len(args):
                        if args[idx] in renamed_steps:
                            args[idx] = renamed_steps[args[idx]]
                            idx += 1
                        elif args[idx] in replaced_steps:
                            replacement_steps = replaced_steps[args[idx]]
                            # insert refs to replacement steps
                            args = (
                                args[:idx] + replacement_steps + args[idx + 1 :]
                            )
                            idx += len(replacement_steps)
                        else:
                            idx += 1
                else:
                    # handle retrieve attribute to get composite ids
                    if args[0] in renamed_steps:
                        args[0] = renamed_steps[args[0]]
                    if args[1] in replaced_steps:
                        replacement_steps = replaced_steps[args[1]]
                        # insert refs to replacement steps
                        replaced_steps[k] = []
                        for replacement_step in replacement_steps:
                            new_k = f"|{next_step_num}|"
                            args[1] = replacement_step
                            augmented_plan[new_k] = "(" + op + " " + " ".join(args) + ")"
                            
                            replaced_steps[k].append(new_k)
                            next_step_num += 1
                        continue
                    elif args[1] in renamed_steps:
                        args[1] = renamed_steps[args[1]]


                new_k = f"|{next_step_num}|"
                next_step_num += 1
                augmented_plan[new_k] = "(" + op + " " + " ".join(args) + ")"
                if new_k != k:
                    renamed_steps[k] = new_k

        return augmented_plan
    
    # sample assignemnt of varying number of attrs?
    def sample_assignments(self, sampling_cfg, ent):
        assignment = {}
        for slot, cfg in sampling_cfg.items():
            # print(slot)
            # TODO: allow sampling from multiple ents?
            # TODO: parse argtyp from slot
            # get possible attrs for sampling
            slot_name = slot.strip("{}")
            possible_attrs = [attr for _, attr in ent.attributes.items() if ArgType.from_str(slot_name.split("[")[0]) in attr.type]
            # print("POSSIBLE ATTRS:", possible_attrs)
            # TODO: handle different sampling functions?
            sampled_attrs = random.sample(possible_attrs, random.randint(cfg["min"], min(cfg["max"], len(possible_attrs))))
            assignment[slot] = ["{" + f"{slot_name}[{i}]" + "}" for i in range(len(sampled_attrs))]

        return assignment

    # TODO: when doing this may also have to update the attribute type list corresponding to associated slots?
    def augment_slots_for_sampling_num_attributes(self, slots, sampling_info):
        augmented_slots = []
        for slot in slots:
            if slot in sampling_info.keys():
                replacements = sampling_info[slot]
                augmented_slots.extend(replacements)
            else:
                augmented_slots.append(slot)
        return augmented_slots

    def augment_template_for_sampling_num_attributes(self, template, sampling_info):
        words = template.split()
        augmented_words = []
        for word in words:
        
            for sampled_slot in sampling_info.keys():

                if sampled_slot.strip("{}") in word:
                    # TODO: handle cases with multiple composite id entities
                    split_idx = word.index("}") + 1
                    punct = word[split_idx:]
                    no_punct_word = word[:split_idx]

                    replacements = [no_punct_word.replace(sampled_slot.strip("{}"), repl.strip("{}")) + "," for i, repl in enumerate(sampling_info[sampled_slot])]
                    # remove comma from last replacement

                    replacements[-1] = replacements[-1][:-1]
                    
                    # TODO: oxford comma this?
                    if len(replacements) > 1:
                        replacements = replacements[:-1] + ["and"] + replacements[-1:]    

                    # replace single id slot with multiple slots for each composite id field
                    # for i, val in enumerate(filler):
                        # new_slot = "{" + f"CompositeIdentifier[{i}" + slot[13:]
                        # replacements.append(new_slot)
                    replacements[-1] += punct
                    augmented_words.extend(replacements)
                    break
            else:
                augmented_words.append(word)
        return " ".join(augmented_words)

    def augment_plan_for_sampling_num_attributes(self, plan, sampling_info):
        # may want to adjust this with value filling for more sensible questions?
        # sometimes uses part of composite id as a filter when using Instance questions - lots of empty results
        # also may want to select values for both composite id fields at the same time to ensure the entity exists
        # print(sampling_info)
        if not plan:
            return plan
        slot_replacements = {}
        for k, step in plan.items():
            for arg in step.strip("()").split(" "):
                # check that slot is for an id
                if arg in sampling_info.keys():
                    slot_replacements[arg] = sampling_info[arg]

        # print(slot_replacements)
        augmented_plan = {}
        replaced_steps = {}
        renamed_steps = {}
        next_step_num = min([int(x.strip("|")) for x in plan.keys()])
        
        for k, step in sorted(plan.items(), key=lambda x: int(x[0].strip("|"))):
            args = step.strip("()").split(" ")
            op = args[0]
            args = args[1:]

            # TODO: assumes only one slot needs to be replaced in each step - should hold
            arg_idx = None
            for i, arg in enumerate(args):
                if arg in slot_replacements:
                    arg_idx = i

            if arg_idx:
                # insert replacement steps using composite slot fillers
                replaced_steps[k] = []
                # handle replaced args
                replaced_arg_idxs = []
                replaced_args = []
                for i, arg in enumerate(args):
                    if arg in replaced_steps:
                        replaced_args.append(replaced_steps[arg])
                        replaced_arg_idxs.append(i)
                
                replacement_fillers = slot_replacements[args[arg_idx]]
                for replacement, replaced_arg in zip(replacement_fillers, *replaced_args) if replaced_args else zip(replacement_fillers, [[]for i in replacement_fillers]):
                    
                    new_k = f"|{next_step_num}|"
                    
                    for j, replaced_arg_idx in enumerate(replaced_arg_idxs):
                        args[replaced_arg_idx] = replaced_arg if type(replaced_arg) != list else replaced_arg[j]
                    args[arg_idx] = replacement
                    
                    augmented_plan[new_k] = "(" + op + " " + " ".join(args) + ")"
                    
                    replaced_steps[k].append(new_k)
                    next_step_num += 1
                if op == "exact":
                    # combine exact ops with and
                    new_k = f"|{next_step_num}|"
                    new_step = "(and " + " ".join(replaced_steps[k]) + ")"
                    augmented_plan[new_k] = new_step
                    replaced_steps[k] = [new_k]
                    next_step_num += 1
                # TODO: handle count/count_unique on part of composite id - may need a concat op?
            else:
                # handle renamed/replaced steps in existing steps
                if op != "retrieve_attribute":
                    idx = 0
                    while idx < len(args):
                        if args[idx] in renamed_steps:
                            args[idx] = renamed_steps[args[idx]]
                            idx += 1
                        elif args[idx] in replaced_steps:
                            replacement_steps = replaced_steps[args[idx]]
                            # insert refs to replacement steps
                            args = (
                                args[:idx] + replacement_steps + args[idx + 1 :]
                            )
                            idx += len(replacement_steps)
                        else:
                            idx += 1
                else:
                    # handle retrieve attribute to get composite ids
                    if args[0] in renamed_steps:
                        args[0] = renamed_steps[args[0]]
                    if args[1] in replaced_steps:
                        replacement_steps = replaced_steps[args[1]]
                        # insert refs to replacement steps
                        replaced_steps[k] = []
                        for replacement_step in replacement_steps:
                            new_k = f"|{next_step_num}|"
                            args[1] = replacement_step
                            augmented_plan[new_k] = "(" + op + " " + " ".join(args) + ")"
                            
                            replaced_steps[k].append(new_k)
                            next_step_num += 1
                        continue
                    elif args[1] in renamed_steps:
                        args[1] = renamed_steps[args[1]]


                new_k = f"|{next_step_num}|"
                next_step_num += 1
                augmented_plan[new_k] = "(" + op + " " + " ".join(args) + ")"
                if new_k != k:
                    renamed_steps[k] = new_k

        return augmented_plan
    
    def update_bp_input_for_sampling_assignment(self, sampled_bp_info, sampled_assignment):
        augmented_inputs = {}
        for k, input_info in sampled_bp_info["input"].items():
            augmented_inputs[k] = input_info
            augmented_inputs[k]["filter"] = self.augment_plan_for_sampling_num_attributes(input_info["filter"], sampled_assignment)
            augmented_inputs[k]["associated_slots"] = self.augment_slots_for_sampling_num_attributes(input_info["associated_slots"], sampled_assignment)
            # print("ASSOCIATED SLOTS", augmented_inputs[k]["associated_slots"])
            augmented_inputs[k]["attribute_type"] = [str(ArgType.from_str(slot.strip("{}").split("[")[0])).split(".")[-1] for slot in augmented_inputs[k]["associated_slots"]]
        sampled_bp_info["input"] = augmented_inputs
        sampled_bp_info["analysis_template"] = self.augment_plan_for_sampling_num_attributes(sampled_bp_info["analysis_template"], sampled_assignment)
        # handle question/statement templates
        sampled_bp_info["statement_templates"] = [self.augment_template_for_sampling_num_attributes(t, sampled_assignment) for t in sampled_bp_info["statement_templates"]]
        sampled_bp_info["question_templates"] = [self.augment_template_for_sampling_num_attributes(t, sampled_assignment) for t in sampled_bp_info["question_templates"]]
        sampled_bp_info["general_question_templates"] = [self.augment_template_for_sampling_num_attributes(t, sampled_assignment) for t in sampled_bp_info["general_question_templates"]]
        # print("AUGMENTED BP INFO:", sampled_bp_info)
        return sampled_bp_info

    def generate_with_access_plans(self,
                                   desired_entities: List[str],
                                   n_plans: int,
                                   filter_proportion: float = 0.5) -> List[Dict]:
        """
        Generates a set of SQR plans and associated questions using the ring attributes and their access plans.
        :param desired_entities: The set of entities to generate the plans for. If this is empty, defaults to all entities in the ring.
        :type desired_entities: List[str]
        :param n_plans: The number of plans to generate for each attribute of each entity.
        :type n_plans: int
        :param filter_proportion: The proportion of plans that should have filters added to them.
        :type filter_proportion: float
        :return: A list of dictionaries that look like: { "questions": [], "plan": {}, "base_plan": "" }
        :rtype: List[Dict]
        """

        # Make sure the retrieval plan generator is initialized
        if not self.access_plan_generator:
            self.access_plan_generator = AccessPlanGenerator(self.ring, self.operation_ontology,
                                                                   self.sqr_composer, self.base_plan_store,
                                                                   self.filter_generator, self.analysis_plan_parser,
                                                                   self.question_generator)

        # Determine the set of entities and base plans to use based on the input
        entities = self.determine_entities_to_use(desired_entities)

        plans_and_questions = []
        for ent in entities:
            plans_and_questions.extend(self.access_plan_generator.generate_with_access_plans(ent, n_plans, filter_proportion))
        return plans_and_questions

    def generate_with_base_plans(self,
                                 desired_entities: List[str],
                                 desired_base_plans: List[str],
                                 n_per_base_plan_per_entity: int = 50,
                                 filter_proportion: float = 0.5,
                                 timeout_seconds: Optional[float] = 10) -> List[Dict]:
        """
        Generates a set of SQR plans and associated questions using base plans.
        :param desired_entities: The set of entities to generate the plans for. If this is empty, defaults to all entities in the ring.
        :type desired_entities: List[str]
        :param desired_base_plans: The set of base plans to use for generating plans. If this is empty, defaults to all base plans.
        :type desired_base_plans: List[str]
        :param filter_proportion: The proportion of plans that should have filters added to them.
        :type filter_proportion: float
        :param timeout_seconds: Optional timeout (seconds) for plan generation. If exceeded, raises TimeoutError.
        :type timeout_seconds: Optional[float]
        :return: A list of dictionaries that look like: { "questions": [], "plan": {}, "base_plan": "" }
        :rtype: List[Dict]
        """

        start_time = time.monotonic()

        def check_timeout() -> None:
            if timeout_seconds is not None and (time.monotonic() - start_time) > timeout_seconds:
                raise TimeoutError(f"generate_with_base_plans timed out after {timeout_seconds}s")

        
        # TODO: allow filling related ents with indirectly related ents?
        #       - should be allowed when constraints are passed in
        # TODO: allow sampling from multiple entities?
        #       - handle this by allowing a base plan input to specify use of related entity
        # TODO: allow template to disallow ids as attributes?

        # Determine the set of entities and base plans to use based on the input
        entities = self.determine_entities_to_use(desired_entities)
        base_plans = self.determine_base_plans_to_use(desired_base_plans)

        specs = []
        for ent in entities:
            check_timeout()
            valid_input_assignments = []
            sampled_bp_infos = []
            for base_plan_name, base_plan_info in base_plans.items():
                check_timeout()
                # Get the set of valid attribute assignments for the inputs of the current base plan
                
                # copy bp info to allow for multiple entities with different ids
                tmp_bp_info = copy.deepcopy(base_plan_info)
                # print("TMP INFO:", tmp_bp_info)
                
                num_ids = len(ent.id)
                if num_ids > 1:
                    # augment bp info to handle composite ids
                    # TODO: store dict of original ids mapping to CompositeIdentifier indices?
                    # would need to fill the related entites first, then update the templates
                    # may involve RelatedIdentifier slots?
                    # no cases of this in template base plans so not an issue for now
                    augmented_inputs = {}
                    for k, input_info in tmp_bp_info["input"].items():
                        augmented_inputs[k] = input_info
                        augmented_inputs[k]["filter"] = self.augment_plan_for_composite_id(input_info["filter"], num_ids)
                        augmented_inputs[k]["associated_slots"] = self.augment_slots_for_composite_id(input_info["associated_slots"], num_ids)

                        augmented_inputs[k]["attribute_type"] = [att_type if att_type != "Identifier" else "CompositeIdentifier" for att_type in augmented_inputs[k]["attribute_type"]]
                    tmp_bp_info["input"] = augmented_inputs
                    tmp_bp_info["analysis_template"] = self.augment_plan_for_composite_id(tmp_bp_info["analysis_template"], num_ids)
                    # handle question/statement templates
                    tmp_bp_info["statement_templates"] = [self.augment_template_for_composite_id(t, num_ids) for t in tmp_bp_info["statement_templates"]]
                    tmp_bp_info["question_templates"] = [self.augment_template_for_composite_id(t, num_ids) for t in tmp_bp_info["question_templates"]]
                    tmp_bp_info["general_question_templates"] = [self.augment_template_for_composite_id(t, num_ids) for t in tmp_bp_info["general_question_templates"]]
                try:
                    for i in range(n_per_base_plan_per_entity):
                        check_timeout()
                        # expand plan if sampling multiple attributes for a slot
                        sampled_bp_info = copy.deepcopy(tmp_bp_info)
                        if sampled_bp_info.get("sample_config", {}):
                            sampled_assignment = self.sample_assignments(sampled_bp_info["sample_config"], ent)
                            sampled_bp_info = self.update_bp_input_for_sampling_assignment(sampled_bp_info, sampled_assignment)
                            # print("SAMPLED ASSIGNMENT:", sampled_assignment)
                        # TODO: support bp inputs retrieving attrs from related ents
                        # may want to distinguish between a DirectlyRelatedAttribute and a RelatedAttribute
                        # TODO: use sampled_assignment here instead of resampling everything?
                        valid_input_assignments.append(self.sampling_assigner.get_input_assignment(sampled_bp_info, ent))
                        sampled_bp_infos.append(sampled_bp_info)
                    # print("VIAs:", len(valid_input_assignments))
                    # Produce new CompositionSpecifications for each of the valid assignments
                    for assignment, sampled_bp_info in zip(valid_input_assignments, sampled_bp_infos):
                        check_timeout()
                        # print("SAMPLED INFO:", sampled_bp_info)
                        # print("ASSIGNMENT:", assignment)
                        # pass False to not include id along with attribute in access plan
                        # specs.append(self.sampling_assigner.convert_new_assignment_to_composition_spec(assignment, base_plan_name, sampled_bp_info, False))
                        specs.append(self.sampling_assigner.convert_new_assignment_to_composition_spec(assignment, base_plan_name, sampled_bp_info))
                except Exception as e:
                    import traceback
                    print(e)
                    print(traceback.format_exc())
                    print(f"Unable to generate plans with base plan '{base_plan_name}' and entity '{ent.name}'")

        # Fill in the EntityClass slots (e.g. {EntityClass[A]}, {RelatedEntityClass[A]})
        check_timeout()
        specs = [self.fill_slots_for_spec(spec,
                                          slot_types_to_consider=["EntityClass", "RelatedEntityClass"],
                                          use_plan_template=True,
                                          include_filled_slots=False,
                                          use_filter_ents=True) for spec in specs]

        # Fill in the attribute slots (e.g. {Identifier[0]}, {Categorical[0]})
        # may need a try catch on these if multiple entities provided
        check_timeout()
        specs = [self.fill_slots_for_spec(spec,
                                          include_filled_slots=False,
                                          ignore_value_slots=True,
                                          use_plan_template=True) for spec in specs]
        
        # Fill in the slots that require specific values for attributes (e.g. {Identifier[0].Value[0]}, {Datetime[0].Value[3]})
        check_timeout()
        specs = [self.fill_slots_for_spec(spec,
                                          include_filled_slots=False,
                                          ignore_value_slots=False,
                                          use_plan_template=True) for spec in specs]

        # filter out specs that didn't produce valid plans for some reason (no available values, mismatched attr types, etc.)
        specs = filter(None, specs)

        # Fill in the FilterExpression slots with empty string defaults (these will be overridden if any filters are added to the spec)
        check_timeout()
        specs = [self.fill_filter_expression_slots_with_defaults(spec) for spec in specs]

        # Make sure the proportion is between 0.0 and 1.0
        filter_proportion = max(min(filter_proportion, 1.0), 0.0)

        # Determine the number of specs that should have filters added to them
        num_to_filter = int(filter_proportion * len(specs))

        # Randomly select the specs to add filters to, generate filters, and add them to the specs
        # TODO: add requirement for filter on both inputs??
        if num_to_filter > 0:
            random.shuffle(specs)
        for i, spec in enumerate(specs):
            check_timeout()
            # TODO: handle case where "require_filter" not provided
            if i < num_to_filter or any(map(lambda input: "require_filter" in input.keys() and input["require_filter"], spec.base_plan["input"].values())):
            # TODO: make this work?
            # Generate the filter (if possible)
                filters = self.filter_generator.generate_spec_input_filters(spec, i < num_to_filter)
                if len(filters) > 0:
                    for filter_info in filters:
                        # Generate the language expression for the generated filter and add it to the slot fillers for this
                        # spec before combining the generated filter with the pre-existing filters on the inputs of the base plan
                        filter_expression_slot = f"{{Filter[{filter_info['input_to_filter'].strip('|')}].Expression}}"

                        # Parse the plan into the necessary object (i.e. AnalysisPlan)
                        filter_plan = self.analysis_plan_parser.parse_plan_snippet(filter_info["filter"])

                        # Get the reference of the final filter step
                        final_step_ref = filter_plan.get_leaves()[0]

                        # Call the step_expressor to express the filter step in natural language
                        filter_expression = filter_info["expression"]
                        if not filter_expression:
                            filter_expression = self.slot_expressor.step_expressor.express_filter_step(final_step_ref, filter_plan)

                        # add word to filter - TODO: sample this?    
                        filter_expression = "with " + filter_expression
                        # Store the generated filter expression
                        spec.slot_fillers[filter_expression_slot] = filter_expression

                        # Add the filter to the spec
                        spec.base_plan_inputs[filter_info["input_to_filter"]]["access_plan_filters"]["filters"].append(filter_info["filter"])
                        if len(spec.base_plan_inputs[filter_info["input_to_filter"]]["access_plan_filters"]["filters"]) > 1:
                            spec.base_plan_inputs[filter_info["input_to_filter"]]["access_plan_filters"]["filter_joiner"] = 'and'

        # Get the fillers for slots in the language templates (this is done in place at the moment)
        for spec in specs:
            check_timeout()
            self.get_template_expression_fillers(spec, template_type="question_templates")

        # Compose the plans based on the composition specs
        final_outputs = []
        for spec in specs:
            check_timeout()
            # Use the spec to compose the plan
            plan = self.sqr_composer.compose(spec)[0]

            # Generate questions for this plan
            questions = [self.question_generator.generate_question(question_template,
                                                                   spec.slot_fillers,
                                                                   plan,
                                                                   {},
                                                                   plan_slot_fillers=spec.input_fillers) for question_template in spec.base_plan['question_templates']]
                                                                #    plan_slot_fillers=spec.input_fillers) for question_template in self.base_plan_store.templates[spec.base_plan_name]['question_templates']]
            # Renumber the steps of the plan
            plan = self.analysis_plan_parser.parse_from_analysis_steps(self.sqr_compiler._renumber(plan.plan_steps))

            try:
                access_plans = {
                        v["ring_attribute"].parent_entity.name + "." + v["ring_attribute"].name: v["access_plan"] for k, v in spec.base_plan_inputs.items()
                    }
            except:
                access_plans = None

            final_outputs.append({
                "plan": plan,
                "questions": questions,
                "base_plan": spec.base_plan_name,
                "source": "BasePlanGenerator",
                "access_plans": access_plans
            })
            self.sqr_composer.alphabet_idx = 0

        #  Return a list of dictionaries looking like: { "questions": [], "plan": {} }
        return final_outputs

    def fill_slots_for_spec(self,
                            spec: CompositionSpecification,
                            include_filled_slots: bool = False,
                            slot_types_to_consider: List[str] = None,
                            ignore_value_slots: bool = False,
                            use_plan_template: bool = False,
                            use_question_templates: bool = False,
                            use_general_question_templates: bool = False,
                            use_statement_templates: bool = False,
                            use_filter_ents: bool = False) -> CompositionSpecification:

        try:
            # Identify the slots that need to be filled
            slots_to_values = self.slot_identifier.identify_slots_to_fill(spec,
                                                                        include_filled_slots=include_filled_slots,
                                                                        slot_types_to_consider=slot_types_to_consider,
                                                                        ignore_value_slots=ignore_value_slots,
                                                                        use_plan_template=use_plan_template,
                                                                        use_question_templates=use_question_templates,
                                                                        use_general_question_templates=use_general_question_templates,
                                                                        use_statement_templates=use_statement_templates,
                                                                        use_filter_ents=use_filter_ents)
            # TODO: assign all vals together? - probably don't want to do this for all vals
            # when this is desirable depends on the base plan
            # for now at least assign composite ids together
            if slots_to_values:
                # If there are any slots that need to be filled in the plan itself (not any of its language templates), then...
                for slot in slots_to_values.keys():
                    spec.slot_fillers[slot] = self.filler_identifier.sample_value_for_slot(slot, spec)

            return spec
        except:
            return None

    def fill_filter_expression_slots_with_defaults(self,
                                                   spec: CompositionSpecification) -> CompositionSpecification:
        """
        Fills in all of the {Filter[].Expression} slots with empty strings.
        :param spec: The composition specification to fill in the slots for.
        :type spec: CompositionSpecification
        :return: The composition specification with its filter expression slots filled with empty strings.
        :rtype: CompositionSpecification
        """
        for base_plan_input_name in spec.base_plan_inputs.keys():
            spec.slot_fillers[f"{{Filter[{base_plan_input_name.strip('|')}].Expression}}"] = ""
        return spec

    def generate_composition_specs_with_specific_slots_and_templates(self,
                                                                     specs: List[CompositionSpecification],
                                                                     include_filled_slots: bool = False,
                                                                     slot_types_to_consider: List[str] = None,
                                                                     ignore_value_slots: bool = False,
                                                                     use_plan_template: bool = False,
                                                                     use_question_templates: bool = False,
                                                                     use_general_question_templates: bool = False,
                                                                     use_statement_templates: bool = False) -> List[CompositionSpecification]:

        new_specs = []
        for spec in specs:
            # Note: At this point in the pipeline, only slots in the SQR plan or their filters are considered

            # Identify the slots that need to be filled
            slots_to_values = self.slot_identifier.identify_slots_to_fill(spec,
                                                                          include_filled_slots=include_filled_slots,
                                                                          slot_types_to_consider=slot_types_to_consider,
                                                                          ignore_value_slots=ignore_value_slots,
                                                                          use_plan_template=use_plan_template,
                                                                          use_question_templates=use_question_templates,
                                                                          use_general_question_templates=use_general_question_templates,
                                                                          use_statement_templates=use_statement_templates)

            if slots_to_values:
                # If there are any slots that need to be filled in the plan itself (not any of its language templates), then...
                for slot in slots_to_values.keys():
                    # Identify the values to fill the slots with
                    slots_to_values[slot].extend(self.filler_identifier.identify_filler(slot, spec))

                    # Produce combinations of the values and use them to create new composition specifications based on the original
                    new_specs.extend(self.generate_new_specs_with_value_combinations(slots_to_values, spec))

            else:
                # If there are no slots in the plan that need to be filled, then just keep the spec as is
                new_specs.append(spec)
        return new_specs

    def generate_new_specs_with_value_combinations(self,
                                                   slots_to_values: Dict,
                                                   spec: CompositionSpecification) -> List[CompositionSpecification]:
        # Put the product inputs into the required form
        product_inputs = []
        for slot, values in slots_to_values.items():
            product_inputs.append([(slot, val) for val in values])

        # Get combinations of all these values
        slot_value_combinations = [list(tup) for tup in product(*product_inputs)]

        # Assign each combination to a copy of the spec
        new_specs = []
        for combo in slot_value_combinations:
            # Create a copy
            new_spec = copy.deepcopy(spec)

            # Assign the slot fillers
            for slot_tup in combo:
                new_spec.slot_fillers[slot_tup[0]] = slot_tup[1]

            # Get the question template slot fillers for this combination
            # self.get_template_expression_fillers(new_spec, template_type='question_templates')

            # Save this new spec
            new_specs.append(new_spec)

        # Return a list of the filled in spec copies
        return new_specs

    def identify_slots_to_fill(self,
                               spec: CompositionSpecification,
                               include_filled_slots: bool = False,
                               slot_types_to_consider: List[str] = None) -> Dict[str, List]:
        """
        Determine which slots need to be filled in the base plan of the given composition specification.
        :param spec: The composition specification to check.
        :type spec: CompositionSpecification
        :param include_filled_slots: Should slots that already have filler values in the spec be included in the output.
        :type include_filled_slots: bool
        :param slot_types_to_consider: Used to constrain the identification of slots to fill to a pre-specified list.
        :type slot_types_to_consider: List[str]
        :return:  A dictionary mapping slots to be filled to an empty list.
        :rtype: Dict[str, List]
        """
        # Get the slots to fill for the current spec
        slots_to_possible_values = {}
        for step in spec.base_plan['analysis_template'].values():
            slots = extract_slots(step)
            for slot in slots:
                slots_to_possible_values[slot] = []
        # Get slots to fill for the filters associated with the base plan
        for input_label, input_info in spec.base_plan['input'].items():
            for step in input_info["filter"].values():
                slots = extract_slots(step)
                for slot in slots:
                    plan_slot = PlanSlot.from_string(slot)
                    if plan_slot.s_type != "EntityClass":
                        slots_to_possible_values[slot] = []

        # Remove slots that already have filler values in the spec
        if not include_filled_slots:
            for filled_slot in spec.input_fillers.keys():
                del slots_to_possible_values[filled_slot]

        # Remove slots that are not ones that have been flagged for consideration
        if slot_types_to_consider:
            keys = list(slots_to_possible_values.keys())
            for slot in keys:
                plan_slot = PlanSlot.from_string(slot)
                if plan_slot.s_type not in slot_types_to_consider:
                    del slots_to_possible_values[slot]

        return slots_to_possible_values


    def get_template_expression_fillers(self,
                                        spec: CompositionSpecification,
                                        template_type: str = "question_templates") -> None:
        """

        :param spec:
        :type spec: CompositionSpecification
        :param template_type: The type of template to consider. Valid values are ['question_templates', 'general_question_templates']
        :type template_type: str
        :return: None (values are added spec's slot_fillers property)
        :rtype: None
        """

        # Do some error checking
        if template_type not in ['question_templates', 'general_question_templates']:
            raise ValueError(f"Invalid template_type: {template_type}. Valid values are ['question_templates', 'general_question_templates']")

        # Get filler values for the expression slots of the question template
        slots_to_fill = self.slot_identifier.identify_slots_to_fill(spec,
                                                                    include_filled_slots=False,
                                                                    use_question_templates=True if template_type == "question_templates" else False,
                                                                    use_general_question_templates=True if template_type == "general_question_templates" else False)

        for slot in slots_to_fill:
            plan_slot = PlanSlot.from_string(slot)
            spec.slot_fillers[str(plan_slot)] = self.slot_expressor.get_slot_expression(plan_slot, spec)

        return None



    def generate_retrieval_plans(self,
                                 desired_entities: List[str],
                                 n_plans: int,
                                 filter_proportion: float = 0.5,
                                 distinct_proportion:float= 0.2) -> List[Dict]:
        """
        Generates plans that retrieve combinations of non-derived attributes.
        :param desired_entities: The set of entities to generate the plans for. If this is empty, defaults to all entities in the ring.
        :type desired_entities: List[str]
        :param n_plans: The number of plans to generate.
        :type n_plans: int
        :param filter_proportion: The proportion of plans that should have filters added to them.
        :type filter_proportion: float
        :return: A list of dictionaries that look like: { "questions": [], "plan": {}, "base_plan": "" }
        :rtype: List[Dict]
        """

        # Make sure the retrieval plan generator is initialized
        if not self.retrieval_plan_generator:
            self.retrieval_plan_generator = RetrievalPlanGenerator(self.ring, self.operation_ontology, self.sqr_composer, self.base_plan_store, self.filter_generator, self.analysis_plan_parser, self.question_generator)

        # Determine the set of entities and base plans to use based on the input
        entities = self.determine_entities_to_use(desired_entities)

        plans_and_questions = []
        for ent in entities:
            plans_and_questions.extend(self.retrieval_plan_generator.generate_retrieval_plans(ent, n_plans, filter_proportion, distinct_proportion))
        return plans_and_questions

    def generate_grouping_plans(self,
                                desired_entities: List[str],
                                n_plans: int,
                                filter_proportion: float = 0.5,
                                having_proportion:float = 0.5) -> List[Dict]:
        """
        Generates plans that aggregates attributes for the desired entities.
        :param desired_entities: The set of entities to generate the plans for. If this is empty, defaults to all entities in the ring.
        :type desired_entities: List[str]
        :param n_plans: The number of plans to generate.
        :type n_plans: int
        :param filter_proportion: The proportion of plans that should have filters added to them.
        :type filter_proportion: float
        :return: A list of dictionaries that look like: { "questions": [], "plan": {}, "base_plan": "" }
        :rtype: List[Dict]
        """

        # Make sure the grouping plan generator is initialized
        if not self.grouping_plan_generator:
            self.grouping_plan_generator = GroupingPlanGenerator(self.ring, self.operation_ontology, self.sqr_composer, self.base_plan_store, self.filter_generator, self.analysis_plan_parser, self.question_generator)

        # Determine the set of entities and base plans to use based on the input
        entities = self.determine_entities_to_use(desired_entities)

        plans_and_questions = []
        for ent in entities:
            try:
                plans_and_questions.extend(self.grouping_plan_generator.generate_grouping_plans(ent, n_plans, filter_proportion, having_proportion))
            except NoValidAttribute as e:
                print(f"Error: {e}")
        return plans_and_questions
    
    def generate_set_operation_plans(self,
                                desired_entities: List[str],
                                n_plans: int,
                                filter_proportion: float = 0.5) -> List[Dict]:
        """
        Generates plans that perform set operations on subqueries for the desired entities.
        :param desired_entities: The set of entities to generate the plans for. If this is empty, defaults to all entities in the ring.
        :type desired_entities: List[str]
        :param n_plans: The number of plans to generate.
        :type n_plans: int
        :param filter_proportion: The proportion of plans that should have filters added to them.
        :type filter_proportion: float
        :return: A list of dictionaries that look like: { "questions": [], "plan": {}, "base_plan": "" }
        :rtype: List[Dict]
        """

        # Make sure the grouping plan generator is initialized
        if not self.set_operation_plan_generator:
            self.set_operation_plan_generator = SetOperationPlanGenerator(self.ring, self.operation_ontology, self.sqr_composer, self.base_plan_store, self.filter_generator, self.analysis_plan_parser, self.question_generator)

        # Determine the set of entities and base plans to use based on the input
        entities = self.determine_entities_to_use(desired_entities)

        plans_and_questions = []
        for ent in entities:
            try:
                plans_and_questions.extend(self.set_operation_plan_generator.generate_set_operation_plans(ent, n_plans, filter_proportion))
            except NoValidAttribute as e:
                print(f"Error: {e}")
        return plans_and_questions
    
    def generate_in_operation_plans(self,
                                desired_entities: List[str],
                                n_plans: int,
                                filter_proportion: float = 0.5,
                                negate_proportion: float = 0.5) -> List[Dict]:
        """
        Generates plans that perform in operations on subqueries for the desired entities.
        :param desired_entities: The set of entities to generate the plans for. If this is empty, defaults to all entities in the ring.
        :type desired_entities: List[str]
        :param n_plans: The number of plans to generate.
        :type n_plans: int
        :param filter_proportion: The proportion of plans that should have filters added to them.
        :type filter_proportion: float
        :param negate_proportion: The proportion of plans that should negate the in condition.
        :type negate_proportion: float
        :return: A list of dictionaries that look like: { "questions": [], "plan": {}, "base_plan": "" }
        :rtype: List[Dict]
        """

        # Make sure the grouping plan generator is initialized
        if not self.in_operation_plan_generator:
            self.in_operation_plan_generator = InOperationPlanGenerator(self.ring, self.operation_ontology, self.sqr_composer, self.base_plan_store, self.filter_generator, self.analysis_plan_parser, self.question_generator)

        # Determine the set of entities and base plans to use based on the input
        entities = self.determine_entities_to_use(desired_entities)

        plans_and_questions = []
        for ent in entities:
            try:
                plans_and_questions.extend(self.in_operation_plan_generator.generate_in_operation_plans(ent, n_plans, filter_proportion, negate_proportion))
            except NoValidAttribute as e:
                print(f"Error: {e}")
        return plans_and_questions
    
    def generate_multi_join_plans(self,
                                desired_entities: List[str],
                                n_plans: int,
                                filter_proportion: float = 0.5) -> List[Dict]:
        """
        Generates plans that perform multi join queries for the desired entities.
        :param desired_entities: The set of entities to generate the plans for. If this is empty, defaults to all entities in the ring.
        :type desired_entities: List[str]
        :param n_plans: The number of plans to generate.
        :type n_plans: int
        :param filter_proportion: The proportion of plans that should have filters added to them.
        :type filter_proportion: float
        :return: A list of dictionaries that look like: { "questions": [], "plan": {}, "base_plan": "" }
        :rtype: List[Dict]
        """

        # Make sure the milti join plan generator is initialized
        if not self.multi_join_plan_generator:
            self.multi_join_plan_generator = MultiJoinPlanGenerator(self.ring, self.operation_ontology, self.sqr_composer, self.base_plan_store, self.filter_generator, self.analysis_plan_parser, self.question_generator)

        # Determine the set of entities and base plans to use based on the input
        entities = self.determine_entities_to_use(desired_entities)

        plans_and_questions = []
        for ent in entities:
            try:
                plans_and_questions.extend(self.multi_join_plan_generator.generate_multi_join_plans(ent, n_plans, filter_proportion))
            except NoValidAttribute as e:
                print(f"Error: {e}")
        return plans_and_questions


    def generate_simple_aggregation_plans(self,
                                desired_entities: List[str],
                                n_plans: int,
                                filter_proportion: float = 0.5) -> List[Dict]:
        """
        Generates plans that retrieve aggregated values for the desired entities.
        :param desired_entities: The set of entities to generate the plans for. If this is empty, defaults to all entities in the ring.
        :type desired_entities: List[str]
        :param n_plans: The number of plans to generate.
        :type n_plans: int
        :param filter_proportion: The proportion of plans that should have filters added to them.
        :type filter_proportion: float
        :return: A list of dictionaries that look like: { "questions": [], "plan": {}, "base_plan": "" }
        :rtype: List[Dict]
        """

        # Make sure the milti join plan generator is initialized
        if not self.simple_aggregation_plan_generator:
            self.simple_aggregation_plan_generator = SimpleAggregationPlanGenerator(self.ring, self.operation_ontology, self.sqr_composer, self.base_plan_store, self.filter_generator, self.analysis_plan_parser, self.question_generator)

        # Determine the set of entities and base plans to use based on the input
        entities = self.determine_entities_to_use(desired_entities)

        plans_and_questions = []
        for ent in entities:
            try:
                plans_and_questions.extend(self.simple_aggregation_plan_generator.generate_simple_aggregation_plans(ent, n_plans, filter_proportion))
            except NoValidAttribute as e:
                print(f"Error: {e}")
        return plans_and_questions
    
    def generate_simple_sql_plans(self,
                                desired_entities: List[str],
                                n_plans: int,
                                filter_proportion: float = 0.5) -> List[Dict]:
        """
        Generates simple SQL queries using * and count(*)
        :param desired_entities: The set of entities to generate the plans for. If this is empty, defaults to all entities in the ring.
        :type desired_entities: List[str]
        :param n_plans: The number of plans to generate.
        :type n_plans: int
        :param filter_proportion: The proportion of plans that should have filters added to them.
        :type filter_proportion: float
        :return: A list of dictionaries that look like: { "questions": [], "plan": {}, "base_plan": "" }
        :rtype: List[Dict]
        """

        # Make sure the milti join plan generator is initialized
        if not self.simple_sql_plan_generator:
            self.simple_sql_plan_generator = SimpleSQLPlanGenerator(self.ring, self.operation_ontology, self.filter_generator)

        # Determine the set of entities and base plans to use based on the input
        entities = self.determine_entities_to_use(desired_entities)

        plans_and_questions = []
        for ent in entities:
            try:
                plans_and_questions.extend(self.simple_sql_plan_generator.generate_simple_sql_plans(ent, n_plans, filter_proportion))
            except NoValidAttribute as e:
                print(f"Error: {e}")
        return plans_and_questions

    def generate_simple_join_plans(self,
                                desired_entities: List[str],
                                n_plans: int,
                                filter_proportion: float = 0.5) -> List[Dict]:
        """
        Generates plans that use joins queries for the desired entities.
        :param desired_entities: The set of entities to generate the plans for. If this is empty, defaults to all entities in the ring.
        :type desired_entities: List[str]
        :param n_plans: The number of plans to generate.
        :type n_plans: int
        :param filter_proportion: The proportion of plans that should have filters added to them.
        :type filter_proportion: float
        :return: A list of dictionaries that look like: { "questions": [], "plan": {}, "base_plan": "" }
        :rtype: List[Dict]
        """

        # Make sure the milti join plan generator is initialized
        if not self.simple_join_plan_generator:
            self.simple_join_plan_generator = SimpleJoinPlanGenerator(self.ring, self.operation_ontology, self.sqr_composer, self.base_plan_store, self.filter_generator, self.analysis_plan_parser, self.question_generator)

        # Determine the set of entities and base plans to use based on the input
        entities = self.determine_entities_to_use(desired_entities)

        plans_and_questions = []
        for ent in entities:
            try:
                plans_and_questions.extend(self.simple_join_plan_generator.generate_simple_join_plans(ent, n_plans, filter_proportion))
            except NoValidAttribute as e:
                print(f"Error: {e}")
        return plans_and_questions

    def augment_plans_with_order_by(self,
                                # desired_entities: List[str],
                                # n_plans: int,
                                # filter_proportion: float = 0.5
                                plans_and_questions,
                                augment_proportion) -> List[Dict]:
        """ TODO fix doc string
        Generates plans that retrieve aggregated values for the desired entities.
        :param desired_entities: The set of entities to generate the plans for. If this is empty, defaults to all entities in the ring.
        :type desired_entities: List[str]
        :param n_plans: The number of plans to generate.
        :type n_plans: int
        :param filter_proportion: The proportion of plans that should have filters added to them.
        :type filter_proportion: float
        :return: A list of dictionaries that look like: { "questions": [], "plan": {}, "base_plan": "" }
        :rtype: List[Dict]
        """

        # Make sure the milti join plan generator is initialized
        if not self.order_by_plan_augmenter:
            self.order_by_plan_augmenter = OrderByPlanAugmenter(self.ring, self.operation_ontology, self.sqr_composer, self.base_plan_store, self.filter_generator, self.analysis_plan_parser, self.question_generator)

        # Determine the set of entities and base plans to use based on the input
        # entities = self.determine_entities_to_use(desired_entities)

        # plans_and_questions = []
        # for ent in entities:
        try:
            plans_and_questions = self.order_by_plan_augmenter.augment_plans_with_order_by(plans_and_questions, augment_proportion)
        except NoValidAttribute as e:
            print(f"Error: {e}")
        return plans_and_questions
