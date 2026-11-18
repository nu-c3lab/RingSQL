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

import itertools, random, re
from copy import deepcopy
from typing import List, Dict, Tuple
from contextlib import closing

from satyrn.core.RingObjects.Ring import Ring
from satyrn.core.Analysis.OperationOntology import OperationOntology
from satyrn.core.Document.InformationRequirement import InformationRequirement
from satyrn.core.Analysis.AnalysisPlan import AnalysisPlan
from satyrn.core.Analysis.AnalysisStep import AnalysisStep
from satyrn.core.Planning.AnalysisPlanParser import AnalysisPlanParser
from satyrn.core.Operations.ArgType import ArgType

class InformationPlanner:
    def __init__(self,
                 ring: Ring,
                 operation_ontology: OperationOntology):
        self.ring = ring
        self.ontology = operation_ontology
        self.analysis_plan_parser = AnalysisPlanParser(self.ontology)
        self.template_token_matcher = '({([^}]+)})'
        self.template_token_matcher_regex = re.compile(self.template_token_matcher)
        self.distinct_value_cache = {}

    def get_raw_plans_from_requirements(self,
                                        info_requirements: List[InformationRequirement]) -> List[dict]:
        """
        Uses the analytics ontology to produce plans given the set of information requirements.
        :param info_requirements:
        :type info_requirements: List of InformationRequirement objects
        :return: The analysis plans needed to satisfy the information requirements.
        :rtype: A List of analysis plans
        """

        # Init var to store all the list of plan steps. This will be a list of dicts.
        raw_plans = []

        for requirement in info_requirements:
            # Get the raw plan templates
            raw_plans.extend(requirement.get_plan_templates())
        return raw_plans

    def generate_plans_from_raw_plans(self,
                                      raw_plans: List[dict]) -> List[AnalysisPlan]:
        """
        Uses the analytics ontology to produce plans given the set of information requirements.
        :param info_requirements:
        :type info_requirements: List of InformationRequirement objects
        :return: The analysis plans needed to satisfy the information requirements.
        :rtype: A List of analysis plans
        """

        # Init var to store all the list of plan steps. This will be a list of dicts.
        all_plan_steps = []

        for i, raw_plan in enumerate(raw_plans):
            print(i+1, '/', len(raw_plans))

            # Get the steps of the plan template
            plan_steps = self.analysis_plan_parser.create_analysis_steps(raw_plan)

            # Get the set of all plan steps with all of the retrieve_entity slots filled in
            steps_with_entities = []
            # Check if the template contains any unfilled retrieve_entity operations
            if self.contains_unfilled_retrieve_entity(plan_steps):
                steps_with_entities.extend(self.fill_retrieve_entity_slots(plan_steps))
            else:
                steps_with_entities.append(plan_steps)

            # Get the set of plans with all of the retrieve_attribute slots filled in
            steps_with_entities_attributes = []
            for plan_steps in steps_with_entities:
                if self.contains_unfilled_retrieve_attribute(plan_steps):
                    steps_with_entities_attributes.extend(self.fill_retrieve_attribute_slots(plan_steps))
                else:
                    steps_with_entities_attributes.append(plan_steps)

            # Get the set of plans with all of the analysis operation slots filled in
            steps_with_entities_attributes_analysis = []
            for plan_steps in steps_with_entities_attributes:
                if self.contains_unfilled_analysis(plan_steps):
                    steps_with_entities_attributes_analysis.extend(self.fill_analysis_operation_slots(plan_steps))
                else:
                    steps_with_entities_attributes_analysis.append(plan_steps)

            steps_with_entities_attributes_analysis_filters = []
            for plan_steps in steps_with_entities_attributes_analysis:
                steps_with_entities_attributes_analysis_filters.extend(self.fill_filter_slots(plan_steps))

            # Add these plans to the set of all plans
            all_plan_steps.extend(steps_with_entities_attributes_analysis_filters)

        # Convert the steps to AnalysisPlan objects
        final_plans = [self.analysis_plan_parser.parse_from_analysis_steps(p_steps) for p_steps in all_plan_steps]

        return final_plans

    def contains_unfilled_retrieve_entity(self,
                                          plan_steps: Dict[str, AnalysisStep]) -> bool:
        """
        Determines if the given plan steps have a "retrieve_entity" operation slot to fill in.
        :param plan_steps: The plan steps to check.
        :type plan_steps: Dict mapping step ref strings to AnalysisStep objects.
        :return: A boolean denoting if there are "retrieve_entity" operation slots to fill in.
        :rtype: bool
        """

        for step_ref, step in plan_steps.items():
            if step.operation == 'retrieve_entity':
                arg_idx = 0
                match = re.search(self.template_token_matcher_regex, step.args[arg_idx])
                if match:
                    return True
        return False

    def contains_unfilled_retrieve_attribute(self,
                                             plan_steps: Dict[str, AnalysisStep]) -> bool:
        """
        Determines if the given plan steps have a "retrieve_attribute" operation slot to fill in.
        :param plan_steps: The plan steps to check.
        :type plan_steps: Dict mapping step ref strings to AnalysisStep objects.
        :return: A boolean denoting if there are "retrieve_attribute" operation slots to fill in.
        :rtype: bool
        """

        for step_ref, step in plan_steps.items():
            if step.operation == 'retrieve_attribute':
                arg_idx = 1
                match = re.search(self.template_token_matcher_regex, step.args[arg_idx])
                if match:
                    return True
        return False

    def contains_unfilled_analysis(self,
                                   plan_steps: Dict[str, AnalysisStep]) -> bool:
        """
        Determines if the given plan steps have a an Analysis operation slot to fill in.
        :param plan_steps: The plan steps to check.
        :type plan_steps: Dict mapping step ref strings to AnalysisStep objects.
        :return: A boolean denoting if there are Analysis operation slots to fill in.
        :rtype: bool
        """

        for step_ref, step in plan_steps.items():
            if step.operation == '{Analysis}':
                return True
        return False

    def fill_retrieve_entity_slots(self,
                                   plan_steps: Dict[str, AnalysisStep]) -> List[Dict[str, AnalysisStep]]:
        """
        Fills in empty slots for "retrieve_entity" operations.
        :param plan_steps: AnalysisPlan steps for which "retrieve_entity" operations will be filled in.
        :type plan_steps: Dict mapping step ref strings to AnalysisStep objects.
        :return: A list of dictionaries mapping step references to AnalysisStep objects which have all
                 "retrieve_entity" operations filled in with valid values.
        :rtype: List of AnalysisStep dictionaries
        """

        # Fill in any of the Entity slots and make copies of the plans
        filled_plan_steps = []
        for step_ref, step in plan_steps.items():
            if step.operation == 'retrieve_entity':
                arg_idx = 0
                match = re.search(self.template_token_matcher_regex, step.args[arg_idx])
                if match:
                    match_str = match.string.strip("{}")
                    if match_str.startswith("RelatedEntity"):
                        # Determine the retrieve_entity step from which the entity type should be gotten
                        tokens = match_str.split("_")
                        ent_step_ref = tokens[1]

                        # Get the original entity
                        ent_name = plan_steps[ent_step_ref].args[0]
                        entity_to_relate_to = [ent for ent in self.ring.entities if ent.name == ent_name][0]

                        # Get all the other entities which this one is related to
                        related_entities = self.ring.get_related_entities(entity_to_relate_to)

                        # Create a copy of the plan steps and fill in the related entity slot
                        if len(related_entities) > 0:
                            for rel_ent in related_entities:
                                # Make a copy of the original steps
                                new_plan_steps = deepcopy(plan_steps)

                                # Slot in the related entity
                                new_plan_steps[step_ref].args[arg_idx] = rel_ent.name

                                # Save this plan
                                filled_plan_steps.append(new_plan_steps)
        return filled_plan_steps

    def fill_retrieve_attribute_slots(self,
                                      plan_steps: Dict[str, AnalysisStep]) -> List[Dict[str, AnalysisStep]]:
        """
        Fills in all empty slots for "retrieve_entity" operations, if possible.
        :param plan_steps: AnalysisPlan steps for which "retrieve_attribute" operations will be filled in.
        :type plan_steps: Dict mapping step ref strings to AnalysisStep objects.
        :return: A list of dictionaries mapping step references to AnalysisStep objects which have all
                 "retrieve_attributes" operations filled in with valid values. If no valid value is found to fill
                 in one of the slots, an empty listed is returned.
        :rtype: List of AnalysisStep dictionaries
        """

        slots_to_fillers = {}
        for step_ref, step in plan_steps.items():
            if step.operation == 'retrieve_attribute':
                arg_idx = 1
                match = re.search(self.template_token_matcher_regex, step.args[arg_idx])
                if match:
                    # Determine the entity from which the attributes will be retrieved
                    ret_entity_step_ref = step.args[0]
                    entity_name = plan_steps[ret_entity_step_ref].args[0]
                    entity = [ent for ent in self.ring.entities if ent.name == entity_name][0]

                    # Determine the kinds of attributes we need to retrieve
                    attr_type_str = match.string.strip("{}")
                    attr_type = ArgType.from_str(attr_type_str)

                    # Get the attributes of that type
                    attributes = entity.get_attributes_with_type(attr_type)

                    # Save these attributes somewhere so we know to slot these into this
                    slots_to_fillers[(step_ref, arg_idx)] = [attr.name for attr in attributes]

        # Ensure that all of the required slots has at least one valid input to put there
        for slot, fillers in slots_to_fillers.items():
            if len(fillers) < 1:
                return []

        # Fill the slots
        return self.fill_slots(slots_to_fillers, plan_steps)

    def fill_analysis_operation_slots(self,
                                      plan_steps: Dict[str, AnalysisStep]) -> List[Dict[str, AnalysisStep]]:
        """
        Fills in all empty slots for analysis operations, if possible.
        :param plan_steps: AnalysisPlan steps for which analysis operations will be filled in.
        :type plan_steps: Dict mapping step ref strings to AnalysisStep objects.
        :return: A list of dictionaries mapping step references to AnalysisStep objects which have all
                 analysis operations filled in with valid values. If no valid value is found to fill
                 in one of the slots, an empty listed is returned.
        :rtype: List of AnalysisStep dictionaries
        """

        slots_to_fillers = {}
        for step_ref, step in plan_steps.items():
            if step.operation == '{Analysis}':
                # Note: The index -1 means this should replace the step.operation string, and not one of the step.args
                slots_to_fillers[(step_ref, -1)] = [op.name for op in self.ontology.analysis_operations.values() if op.name != 'correlation']

        return self.fill_slots(slots_to_fillers, plan_steps)

    def fill_filter_slots(self,
                          plan_steps: Dict[str, AnalysisStep]) -> List[Dict[str, AnalysisStep]]:
        """
        Fills in all empty slots for filter operations, if possible.
        :param plan_steps: AnalysisPlan steps for which filter operations will be filled in.
        :type plan_steps: Dict mapping step ref strings to AnalysisStep objects.
        :return: A list of dictionaries mapping step references to AnalysisStep objects which have all
                 filter operations filled in with valid values. If no valid value is found to fill
                 in one of the slots, an empty list is returned.
        :rtype: List of AnalysisStep dictionaries
        """

        slots_to_fillers = {}
        for step_ref, step in plan_steps.items():
            if self.ontology.is_boolean_operation(step.operation):
                arg_idx = 1
                match = re.search(self.template_token_matcher_regex, str(step.args[arg_idx]))
                if match:
                    # Determine the entity from which the attributes will be retrieved
                    ret_attribute_step_ref = step.args[0]
                    attribute_name = plan_steps[ret_attribute_step_ref].args[1]
                    ret_entity_step_ref = plan_steps[ret_attribute_step_ref].args[0]

                    # Determine the entity from which the attributes will be retrieved
                    entity_name = plan_steps[ret_entity_step_ref].args[0]
                    entity = [ent for ent in self.ring.entities if ent.name == entity_name][0]
                    attribute = [attr[1] for attr in entity.attributes.items() if attr[0] == attribute_name][0]

                    if attribute.source_table not in self.distinct_value_cache:
                        self.distinct_value_cache[attribute.source_table] = {}
                    if attribute.source_columns[0] in self.distinct_value_cache[attribute.source_table]:
                        distinct_attribute_values = self.distinct_value_cache[attribute.source_table][attribute.source_columns[0]]
                    else:
                        with closing(self.ring.db_interface.db.session_maker()) as session:
                            # session = self.ring.db_interface.db.session_maker()
                            # Get the SQL Alchemy model associated with the model name string
                            model = getattr(self.ring.db_interface.db, attribute.source_table)

                            # Get the SQL Alchemy object representing this field
                            field = getattr(model, attribute.source_columns[0])

                            distinct_attribute_values = session.query(field).distinct().all()

                        self.distinct_value_cache[attribute.source_table][attribute.source_columns[0]] = distinct_attribute_values

                    # Save these attributes somewhere so we know to slot these into this
                    slots_to_fillers[(step_ref, arg_idx)] = [value[0] for value in distinct_attribute_values]

        # Ensure that all of the required slots has at least one valid input to put there
        for slot, fillers in slots_to_fillers.items():
            if len(fillers) < 1:
                return []

        # Fill the slots
        return self.fill_slots(slots_to_fillers, plan_steps)

    def fill_slots(self,
                   slots_to_fillers: Dict[Tuple, List[str]],
                   plan_steps: Dict[str, AnalysisStep]) -> List[Dict[str, AnalysisStep]]:
        """
        Fills in the slots of the given plan steps using the given mapping.
        :param slots_to_fillers: A dictionary mapping a tuple of (<sqr_step_ref>, <arg_idx>) to a list of possible values to put in that slot.
        :type slots_to_fillers: Dict mapping tuples to list of str
        :param plan_steps: The plan steps to put the fillers into.
        :type plan_steps: Dict mapping step ref strings to AnalysisStep objects.
        :return: A list of dictionaries mapping step references to AnalysisStep objects which have their specified slots filled in.
        :rtype: List of AnalysisStep dictionaries
        """

        # Init the list to return
        filled_plan_steps = []

        # Get all the permutations of the slot fillers
        filler_list = list(slots_to_fillers.values())
        filler_combos = [list(tup) for tup in itertools.product(*filler_list)]

        # selected_combos = random.sample(filler_combos, 1000) if len(filler_combos) > 1000 else filler_combos

        # Fill in the plan template with each of the slot filler operations
        for combo in filler_combos:
            # Make a copy of the original steps
            plan_steps_copy = deepcopy(plan_steps)

            # Replace the appropriate values in order to fill in the slots
            slots = list(slots_to_fillers.keys())
            for slot_idx, filler in enumerate(combo):
                slot = slots[slot_idx]
                step_ref = slot[0]
                arg_idx = slot[1]
                if arg_idx == -1:  # An arg_idx of -1 means we need to replace the operation and not one of the step args
                    plan_steps_copy[step_ref].operation = filler
                else:
                    plan_steps_copy[step_ref].args[arg_idx] = filler

            # Save the raw plan
            filled_plan_steps.append(plan_steps_copy)

        return filled_plan_steps
