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

import re
import json
import itertools
from pathlib import Path
from copy import deepcopy
from typing import List, Dict

from satyrn.core.RingObjects.Ring import Ring
from satyrn.core.Analysis.OperationOntology import OperationOntology
from satyrn.core.Analysis.AnalysisPlan import AnalysisPlan
from satyrn.core.Analysis.AnalysisStep import AnalysisStep
from satyrn.core.Planning.AnalysisPlanParser import AnalysisPlanParser
from satyrn.core.Operations.ArgType import ArgType
from satyrn.core.Document.DocumentType import DocumentType
from satyrn.core.Document.SQRPlanFiller import SQRPlanFiller

class DocumentPlanner:
    def __init__(self,
                 ring: Ring,
                 operation_ontology: OperationOntology):
        self.ring = ring
        self.ontology = operation_ontology
        self.analysis_plan_parser = AnalysisPlanParser(self.ontology)
        self.template_token_matcher = '({([^}]+)})'
        self.template_token_matcher_regex = re.compile(self.template_token_matcher)
        self.plan_filler = SQRPlanFiller(ring)

        # Read in the JSON file of info_requirements.json
        p = Path(__file__).with_name('base_plan_templates.json')
        with p.open('r') as f:
            self.base_plan_templates = json.load(f)


    def generate_plans(self,
                       document_to_generate: DocumentType) -> List[AnalysisPlan]:
        """
        Generate the set of plans to be executed based on the given document type, ring, and available analytics.
        :param document_to_generate: The type of document to generate.
        :type document_to_generate: DocumentType
        :return: A list of analysis plans that should be executed in order to generate the information for the given document.
        :rtype: A list of analysis plans
        """
        # Get the information requirements for given document to generate
        # Note: This maps the plan_template_type to a list of slot fillers
        info_requirements = document_to_generate.get_information_requirements()

        # Iterate over all the information requirements / plan templates
        all_plan_steps = []
        for plan_template_type, specified_slot_fillers in info_requirements.items():
            # Get the plan template
            plan_template = self.plan_templates[plan_template_type]

            # Build AnalysisStep objects for the steps of the plan template
            plan_steps = self.analysis_plan_parser.create_analysis_steps(plan_template['plan_template'])

            # Build valid combinations of slot fillers
            all_valid_combos = self.build_filler_combinations(specified_slot_fillers, {})

            # Deduplicate valid_combos
            deduped_combos = self.plan_filler.dedupe_list_of_dict(all_valid_combos)

            # TODO: Validate the deduped_combos (check that the attributes to be retrieved are valid for the entity, the analyses to run make sense to run on those attributes, etc.)

            # Use the set of valid_combos to produce partial plans
            partial_plans = []
            for combo in deduped_combos:
                partial_plans.append(self.plan_filler.fill_plan(plan_steps, combo))
            partial_plans = list(filter(lambda item: item is not None, partial_plans))
            deduped_partial_plans = self.plan_filler.dedupe_list_of_dict(partial_plans)
            # partial_plans = self.generate_plans_with_specified_slots(plan_steps, deduped_combos)

            # Fill in the remaining slots for each of these plans using all combinations of valid values from the ring
            for partial_plan in deduped_partial_plans:
                # Get the set of all plan steps with all of the retrieve_entity slots filled in
                steps_with_entities = []
                if self.contains_unfilled_retrieve_entity(partial_plan):
                    steps_with_entities.extend(self.fill_retrieve_entity_slots(partial_plan))
                else:
                    steps_with_entities.append(partial_plan)

                # Get the set of plans with all of the retrieve_attribute slots filled in
                steps_with_entities_attributes = []
                for partial_plan in steps_with_entities:
                    if self.contains_unfilled_retrieve_attribute(partial_plan):
                        steps_with_entities_attributes.extend(self.fill_retrieve_attribute_slots(partial_plan))
                    else:
                        steps_with_entities_attributes.append(partial_plan)

                # Get the set of plans with all of the analysis operation slots filled in
                steps_with_entities_attributes_analysis = []
                for partial_plan in steps_with_entities_attributes:
                    if self.contains_unfilled_analysis(partial_plan):
                        steps_with_entities_attributes_analysis.extend(self.fill_analysis_operation_slots(partial_plan))
                    else:
                        steps_with_entities_attributes_analysis.append(partial_plan)

                # Add these plans to the set of all plans
                all_plan_steps.extend(steps_with_entities_attributes_analysis)

        # Convert the steps to AnalysisPlan objects
        final_plans = [self.analysis_plan_parser.parse_from_analysis_steps(p_steps) for p_steps in all_plan_steps]

        return final_plans

    def build_filler_combinations(self,
                                  fillers: List[Dict[str, str]],
                                  slots_filled: Dict[str, str]) -> List[Dict[str, str]]:
        """
        Recursively builds the set of all combinations of filler values.
        This will build the set of all slot filler combinations for which there are no conflicts
        (i.e. two filler sets specify the same slot).
        :param fillers: The list of possible slots and their fillers.
        :type fillers: List of dicts
        :param slots_filled: The slots which have already been filled.
        :type slots_filled: Dict
        :return: The set of slot filler combinations
        :rtype: List of dicts
        """

        out = []
        for current_filler_set in fillers:
            # Check if there is any overlap between the two sets of keys
            if len(current_filler_set.keys() & slots_filled.keys()) == 0:
                slots_filled_copy = deepcopy(slots_filled)

                # Add current_filler_set to the slots to fill
                slots_filled_copy.update(current_filler_set)

                # Create a new fillers without the filler that was added
                fillers_copy = deepcopy(fillers)
                fillers_copy.remove(current_filler_set)

                # Make the recursive call
                out.extend(self.build_filler_combinations(fillers_copy, slots_filled_copy))
        if len(out) == 0:
            return [slots_filled]
        else:
            return out

    def contains_unfilled_retrieve_entity(self,
                                          partial_plan: Dict[str, AnalysisStep]) -> bool:
        """
        Determines if the given plan steps have a "retrieve_entity" operation slot to fill in.
        :param partial_plan: The plan steps to check.
        :type partial_plan: Dict mapping step ref strings to AnalysisStep objects.
        :return: A boolean denoting if there are "retrieve_entity" operation slots to fill in.
        :rtype: bool
        """

        for step_ref, step in partial_plan.items():
            if step.operation == 'retrieve_entity':
                arg_idx = 0
                match = re.search(self.template_token_matcher_regex, step.args[arg_idx])
                if match:
                    return True
        return False

    def contains_unfilled_retrieve_attribute(self,
                                             partial_plan: Dict[str, AnalysisStep]) -> bool:
        """
        Determines if the given plan steps have a "retrieve_attribute" operation slot to fill in.
        :param partial_plan: The plan steps to check.
        :type partial_plan: Dict mapping step ref strings to AnalysisStep objects.
        :return: A boolean denoting if there are "retrieve_attribute" operation slots to fill in.
        :rtype: bool
        """

        for step_ref, step in partial_plan.items():
            if step.operation == 'retrieve_attribute':
                arg_idx = 1
                match = re.search(self.template_token_matcher_regex, step.args[arg_idx])
                if match:
                    return True
        return False

    def contains_unfilled_analysis(self,
                                   partial_plan: Dict[str, AnalysisStep]) -> bool:
        """
        Determines if the given plan steps have a an Analysis operation slot to fill in.
        :param partial_plan: The plan steps to check.
        :type partial_plan: Dict mapping step ref strings to AnalysisStep objects.
        :return: A boolean denoting if there are Analysis operation slots to fill in.
        :rtype: bool
        """

        for step_ref, step in partial_plan.items():
            arg_idx = -1
            match = re.search(self.template_token_matcher_regex, step.args[arg_idx])
            if match:
                match_str = match.string
                if match_str.startswith("{Analysis:"):
                    return True
        return False

    def fill_retrieve_entity_slots(self,
                                   partial_plan: Dict[str, AnalysisStep]) -> List[Dict[str, AnalysisStep]]:
        """
        Fills in empty slots for "retrieve_entity" operations.
        :param partial_plan: AnalysisPlan steps for which "retrieve_entity" operations will be filled in.
        :type partial_plan: Dict mapping step ref strings to AnalysisStep objects.
        :return: A list of dictionaries mapping step references to AnalysisStep objects which have all
                    "retrieve_entity" operations filled in with valid values.
        :rtype: List of AnalysisStep dictionaries
        """

        # First, fill in any of the {Entity:n} slots and make copies of the plans
        slots_to_fillers = {}
        for step_ref, step in partial_plan.items():
            if step.operation == 'retrieve_entity':
                arg_idx = 0
                match = re.search(self.template_token_matcher_regex, step.args[arg_idx])
                if match:
                    match_str = match.string
                    if match_str.startswith("{Entity:") and match_str not in slots_to_fillers:
                        # Get all of the values that can be slotted into this slot
                        slots_to_fillers[match_str] = [ent.name for ent in self.ring.entities]

        plans_with_ents = self.fill_slots(partial_plan, slots_to_fillers)

        # Second, fill in the {RelatedEntity_|n|} slots
        plans_with_ents_and_related_ents = []
        for updated_partial_plan in plans_with_ents:
            slots_to_fillers = {}
            for step_ref, step in updated_partial_plan.items():
                if step.operation == 'retrieve_entity':
                    arg_idx = 0
                    match = re.search(self.template_token_matcher_regex, step.args[arg_idx])
                    if match:
                        match_str = match.string
                        if match_str.startswith("{RelatedEntity"):
                            # Determine the retrieve_entity step from which the entity type should be gotten
                            tokens = match_str.split("_")
                            ent_step_ref = tokens[1]

                            # Get the original entity
                            ent_name = updated_partial_plan[ent_step_ref].args[0]
                            entity_to_relate_to = [ent for ent in self.ring.entities if ent.name == ent_name][0]

                            # Get all of the values that can be slotted into this slot
                            slots_to_fillers[match_str] = [rel_ent.name for rel_ent in self.ring.get_related_entities(entity_to_relate_to)]

            plans_with_ents_and_related_ents.extend(self.fill_slots(updated_partial_plan, slots_to_fillers))

        return plans_with_ents_and_related_ents


    def fill_retrieve_attribute_slots(self,
                                      partial_plan: Dict[str, AnalysisStep]) -> List[Dict[str, AnalysisStep]]:
        """
        Fills in empty slots for "retrieve_attribute" operations.
        :param partial_plan: AnalysisPlan steps for which "retrieve_attribute" operations will be filled in.
        :type partial_plan: Dict mapping step ref strings to AnalysisStep objects.
        :return: A list of dictionaries mapping step references to AnalysisStep objects which have all
                    "retrieve_attribute" operations filled in with valid values.
        :rtype: List of AnalysisStep dictionaries
        """

        plans_with_attrs = []
        slots_to_fillers = {}
        for step_ref, step in partial_plan.items():
            if step.operation == 'retrieve_attribute':
                arg_idx = 1
                match = re.search(self.template_token_matcher_regex, step.args[arg_idx])
                if match:
                    # Determine the entity from which the attributes will be retrieved
                    ret_entity_step_ref = step.args[0]
                    entity_name = partial_plan[ret_entity_step_ref].args[0]
                    entity = [ent for ent in self.ring.entities if ent.name == entity_name][0]

                    # Determine the kinds of attributes we need to retrieve
                    attr_slot_name = match.string.strip("{}")
                    attr_type_str = attr_slot_name.split(":")[0]
                    attr_type = ArgType.from_str(attr_type_str)

                    # Get the attributes of that type
                    slots_to_fillers[match.string] = [attr.name for attr in entity.get_attributes_with_type(attr_type)]

        return self.fill_slots(partial_plan, slots_to_fillers)

    def fill_analysis_operation_slots(self,
                                      partial_plan: Dict[str, AnalysisStep]) -> List[Dict[str, AnalysisStep]]:
        """
        Fills in all empty slots for analysis operations, if possible.
        :param plan_steps: AnalysisPlan steps for which analysis operations will be filled in.
        :type plan_steps: Dict mapping step ref strings to AnalysisStep objects.
        :return: A list of dictionaries mapping step references to AnalysisStep objects which have all
                 analysis operations filled in with valid values. If no valid value is found to fill
                 in one of the slots, an empty listed is returned.
        :rtype: List of AnalysisStep dictionaries
        """

        plans_with_analysis = []
        slots_to_fillers = {}
        for step_ref, step in partial_plan.items():
            arg_idx = -1
            match = re.search(self.template_token_matcher_regex, step.args[arg_idx])
            if match:
                match_str = match.string
                if match_str.startswith("{Analysis:"):
                    slots_to_fillers[match_str] = [op.name for op in self.ontology.analysis_operations.values() if op.name != 'correlation']

        return plans_with_analysis

    def fill_slots(self,
                   partial_plan: Dict[str, AnalysisStep],
                   slots_to_fillers: Dict[str, List[str]]) -> List[Dict[str, AnalysisStep]]:
        """
        Fills in the slots of the given plan steps using the given mapping.
        :param partial_plan: An analysis plan whose slots have been partially filled in.
        :type partial_plan: Dict mapping step references to analysis plan steps
        :param slots_to_fillers: The mapping from slot names to a list of valid values for that slot.
        :type slots_to_fillers: Dict
        :return: A list of partial plans whose slots have been filled in more.
        :rtype:
        """

        # Init the list of plans to return
        filled_plans = []

        slot_fillers = []
        for k, v in slots_to_fillers.items():
            slot_fillers.append([{k:filler} for filler in v])

        # Get all the permutations of the slot fillers
        filler_list = slot_fillers
        filler_combos = [list(tup) for tup in itertools.product(*filler_list)]

        # Fill in the plan template with each of the slot filler operations
        plan_slot_info = self.plan_filler.identify_slots_in_plan_template(partial_plan)
        for combo in filler_combos:
            # Make a copy of the original steps
            partial_plan_copy = deepcopy(partial_plan)

            combo_dict = {}
            for item in combo:
                combo_dict.update(item)

            # Fill in the slots
            for slot, filler in combo_dict.items():
                if slot in plan_slot_info:
                    for slot_location_dict in plan_slot_info[slot]:
                        step_idx = slot_location_dict['step_idx']
                        arg_idx = slot_location_dict['arg_idx']
                        if arg_idx == -1:
                            # The filler is meant to replace the operation, not one of the step arguments
                            partial_plan_copy[step_idx].operation = filler
                        else:
                            partial_plan_copy[step_idx].args[arg_idx] = filler

            # Save the raw plan
            filled_plans.append(partial_plan_copy)

        return filled_plans

    def is_slot_specified(self,
                          slot: str,
                          slot_fillers: List[Dict[str, str]]) -> bool:
        """
        Checks if any of the slot_fillers specify this slot already.
        :param slot: THe name of the slot to check for.
        :type slot: str
        :param slot_fillers: A list of slots and their corresponding filler values.
        :type slot_fillers: List of dictionaries mapping slot name string to filler value string
        :return: Boolean denoting whether or not this slot is specified by the given slot fillers.
        :rtype: bool
        """
        return any([slot == k for slot_filler in slot_fillers for k in slot_filler.keys()])
