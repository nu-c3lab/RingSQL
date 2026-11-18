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
from typing import List, Dict

from satyrn.core.RingObjects.Ring import Ring
from satyrn.core.RingObjects.RingEntity import RingEntity
from satyrn.core.Document.BasePlanStore import BasePlanStore
from satyrn.core.Analysis.OperationOntology import OperationOntology
from satyrn.core.RingObjects.RingAttribute import RingAttribute
from satyrn.core.Operations.ArgType import ArgType
from satyrn.core.Planning.utils import intersect_lists
from satyrn.core.Planning.PlanGeneration.PlanSlot import PlanSlot
from satyrn.core.Planning.PlanGeneration.InputAssignment import InputAssignment
from satyrn.core.Planning.CompositionSpecification import CompositionSpecification

class ExhaustiveBasePlanInputAssigner:
    """
    A class for identifying and assigning values to slots in a base plan.
    """

    def __init__(self,
                 ring: Ring,
                 operation_ontology: OperationOntology,
                 base_plan_store: BasePlanStore):
        self.ring = ring
        self.operation_ontology = operation_ontology
        self.base_plan_store = base_plan_store

    def get_input_assignments_for_base_plan(self,
                                            base_plan: Dict,
                                            ent: RingEntity) -> List[Dict]:
        """
        Determines the set of valid assignment of attributes to the given base plan.
        :param base_plan: The base plan to use.
        :type base_plan: Dict
        :param ent: The RingEntity whose attributes will be considered
        :type ent: RingEntity
        :return: A list of dictionaries containing the slot assignments.
        :rtype: List[Dict]
        """

        # Assign attributes of the entity to inputs of the base plan
        input_assignments = self.init_input_assignment_dict(base_plan['input'])
        input_associated_slots = { input_label: input_info["associated_slots"] for input_label, input_info in base_plan['input'].items() }
        input_slot_assignments = self.assign_attributes_to_input_slots(copy.deepcopy(input_assignments),
                                                                       copy.deepcopy(input_associated_slots),
                                                                       copy.deepcopy(ent.attributes),
                                                                       [],
                                                                       base_plan)

        # Get rid of duplicate and invalid assignments
        input_slot_assignments = self.remove_duplicate_input_slot_assignments(input_slot_assignments)
        input_slot_assignments = self.remove_invalid_input_slot_assignments(input_slot_assignments)

        return input_slot_assignments

    def init_input_assignment_dict(self,
                                   base_plan_inputs: Dict) -> Dict:
        """
        Initialize the dictionary of input slots associated with the inputs of the base plan.
        Note: This does not include the input filters.
        :param base_plan_inputs: The dictionary containing all the base plan inputs.
        :type base_plan_inputs: Dict
        :return: A dictionary mapping each
        :rtype: Dict
        """

        plan_slots = {}
        for input_label, input_info in base_plan_inputs.items():
            input_slot_values = input_info["associated_slots"]
            for slot_string in input_slot_values:
                plan_slot = PlanSlot.from_string(slot_string)
                if str(plan_slot) not in plan_slots:
                    plan_slots[str(plan_slot)] = InputAssignment()
                plan_slots[str(plan_slot)].inputs.add(input_label)
        return plan_slots

    def assign_attributes_to_input_slots(self,
                                         input_assignments: Dict[str, InputAssignment],
                                         remaining_input_slots: Dict[str, List[str]],
                                         available_attributes: Dict[str, RingAttribute],
                                         valid_input_slot_assignments: List[Dict[str, InputAssignment]],
                                         base_plan: Dict) -> List[Dict[str, InputAssignment]]:
        """
        Maps available attributes to inputs of the base plan.
        :param input_assignments: A dictionary mapping slots associated with the input to an InputAssignment object
        :type input_assignments: Dict[str, InputAssignment]
        :param remaining_input_slots: A dictionary mapping base plan input names to slots associated with the input that still need to be assigned
        :type remaining_input_slots: Dict[str, List[str]]
        :param available_attributes: The list of attributes remaining that can be assigned to the slots (i.e. ones that are valid for at least one of the slots and which has not already been assigned to a slot).
        :type available_attributes: Dict[str, RingAttribute]
        :param valid_input_slot_assignments: A list of valid assignment dictionaries.
        :type valid_input_slot_assignments: List[Dict[str, InputAssignment]]
        :param base_plan: A base plan definition.
        :type base_plan: Dict
        :return: A list of dictionaries mapping slots (e.g. {Metric:0}) associated with the input to InputAssignment objects
        :rtype: List[Dict[str, InputAssignment]]
        """

        # Base Case: There are no input slots remaining to be filled
        if len(remaining_input_slots.keys()) == 0:
            return [input_assignments]

        # Base Case: All slots are assigned
        if all([input_assignments[slot_name].attr for slot_name, slot_info in input_assignments.items()]):
            return [input_assignments]

        # Base Case: No more attributes to assign to the slots
        if len(available_attributes) == 0:
            return []

        # Get rid of all attributes that can't be assigned to any of the remaining input slots
        attributes_to_ignore = []
        for attr_name, attr in available_attributes.items():
            if not any([self.can_attribute_fill_input_slot(attr, base_plan['input'][input_name]) for input_name in remaining_input_slots.keys()]):
                attributes_to_ignore.append(attr_name)
        for attr_name in attributes_to_ignore:
            del available_attributes[attr_name]

        # Assign the next available attribute
        for attr_name, attr in available_attributes.items():
            # Assign this attribute to each of the viable available slots
            for input_name, input_slot_values in remaining_input_slots.items():
                if self.can_attribute_fill_input_slot(attr, base_plan['input'][input_name]):
                    # Since this input slot has been assigned, remove it from the remaining_input_slots
                    updated_remaining_input_slots = copy.deepcopy(remaining_input_slots)
                    del updated_remaining_input_slots[input_name]

                    # Assign the attribute to the plan slot in plan_slots
                    updated_input_assignments = copy.deepcopy(input_assignments)
                    for input_slot in input_slot_values:
                        updated_input_assignments[input_slot].attr = attr

                        # Remove from consideration all input slots associated with this plan slot (since this attribute has to be used as input there as well)
                        for associated_input_slot in updated_input_assignments[input_slot].inputs:
                            if associated_input_slot in updated_remaining_input_slots:
                                del updated_remaining_input_slots[associated_input_slot]

                    # Remove this attribute from the list of available attributes moving forward
                    updated_available_attributes = copy.deepcopy(available_attributes)
                    del updated_available_attributes[attr_name]

                    # Make the recursive call to continue assigning attributes to slots
                    valid_input_slot_assignments.extend(self.assign_attributes_to_input_slots(updated_input_assignments,
                                                                                              updated_remaining_input_slots,
                                                                                              updated_available_attributes,
                                                                                              valid_input_slot_assignments,
                                                                                              base_plan))

        return valid_input_slot_assignments

    def can_attribute_fill_input_slot(self,
                                      attr: RingAttribute,
                                      base_plan_input: Dict) -> bool:
        """
        Checks whether or not the attribute can fill the base plan input.
        :param attr: The ring attribute to check.
        :type attr: RingAttribute
        :param base_plan_input: A single input definition for the base plan.
        :type base_plan_input: Dict
        :return: True or false based on if the attribute has a matching type for the base plan input.
        :rtype: bool
        """

        input_types = [ArgType.from_str(a_type) for a_type in base_plan_input['attribute_type']]
        return len(intersect_lists([attr.type, input_types])) > 0

    def remove_duplicate_input_slot_assignments(self,
                                                input_slot_assignments: List[Dict[str, InputAssignment]]) -> List[Dict[str, InputAssignment]]:
        """
        Returns a copy of the given input_slot_assignments with no duplicate assignments.
        :param input_slot_assignments: The list of dictionaries mapping slots (e.g. {Metric:0}) to InputAssignment objects.
        :type input_slot_assignments: List[Dict[str, InputAssignment]]
        :return: A list of input slot assignments
        :rtype:  List[Dict[str, InputAssignment]]
        """

        deduped_plan_slot_assignments = []
        for assignment in input_slot_assignments:
            if assignment not in deduped_plan_slot_assignments:
                deduped_plan_slot_assignments.append(assignment)
        return deduped_plan_slot_assignments

    def remove_invalid_input_slot_assignments(self,
                                              input_slot_assignments: List[Dict[str, InputAssignment]]) -> List[Dict[str, InputAssignment]]:
        """
        Returns a copy of the given input_slot_assignments with only valid input slot assignments.
        Currently, invalid assignments are ones with no attributes assigned to them.
        :param input_slot_assignments: The list of dictionaries mapping slots (e.g. {Metric:0}) to InputAssignment objects.
        :type input_slot_assignments: List[Dict[str, InputAssignment]]
        :return: A list of input slot assignments
        :rtype:  List[Dict[str, InputAssignment]]
        """

        valid_plan_slot_assignments = []
        for assignment in input_slot_assignments:
            add_assignment = True
            for slot_name, input_assignment in assignment.items():
                if not input_assignment.attr:
                    add_assignment = False
            if add_assignment:
                valid_plan_slot_assignments.append(assignment)
        return valid_plan_slot_assignments

    def get_attributes_for_input(self,
                                 input_name: str,
                                 input_info: Dict,
                                 ent: RingEntity) -> List[RingAttribute]:
        """
        Determine which attributes of the entity satisfy the requirements of the given base plan input.
        :param input_name: The name of the base plan input (e.g. "|A|")
        :type input_name: str
        :param input_info: The definition for the base plan input specifying its requirements.
        :type input_info: Dict
        :param ent: The ring entity whose attributes will be considered.
        :type ent: RingEntity
        :return: A list of ring attributes that can be used as input for the given base plan input.
        :rtype: List[RingAttribute]
        """
        valid_attributes = []
        input_types = [ArgType.from_str(a_type) for a_type in input_info['attribute_type']]
        for attr_name, attr in ent.attributes.items():
            if len(intersect_lists([attr.type, input_types])):
                valid_attributes.append(attr)
        return valid_attributes

    def convert_assignment_to_composition_spec(self,
                                               assignments: Dict,
                                               base_plan_name: str) -> CompositionSpecification:
        """
        Transforms the base plan input assignments into a corresponding composition specification.
        :param assignments: The dictionary containing the assignment of attributes to inputs for the base plan.
        :type assignments: Dict
        :param base_plan_name: The name of the base plan the assignment is for.
        :type base_plan_name: str
        :return: The composition specification
        :rtype: CompositionSpecification
        """

        base_plan_inputs = {}
        slot_fillers = {}
        for slot, input_assignment in assignments.items():
            for assigned_slot_name in input_assignment.inputs:
                # Add the access plan for this input
                base_plan_inputs[assigned_slot_name] = {
                    "access_plan": input_assignment.attr.access_plan
                }

                # Add the filters
                if self.base_plan_store.templates[base_plan_name]['input'][assigned_slot_name]['filter']:
                    # Get the filter and default joiner
                    default_filter = self.base_plan_store.templates[base_plan_name]['input'][assigned_slot_name]['filter']
                    default_filter_joiner = "and"

                    base_plan_inputs[assigned_slot_name]["access_plan_filters"] = {
                        "filters": [default_filter],
                        "filter_joiner": default_filter_joiner
                    }
                else:
                    base_plan_inputs[assigned_slot_name]["access_plan_filters"] = {
                        "filters": [],
                        "filter_joiner": None
                    }

                # Add the RingAttribute that was assigned to this input
                base_plan_inputs[assigned_slot_name]["ring_attribute"] = input_assignment.attr

                # Add attributes assigned to the inputs to the slots they will correspond to
                for associated_slot in self.base_plan_store.templates[base_plan_name]['input'][assigned_slot_name]['associated_slots']:
                    slot_fillers[associated_slot] = input_assignment.attr

        # Create the specification object
        spec = CompositionSpecification(base_plan_name=base_plan_name,
                                        base_plan=self.base_plan_store.templates[base_plan_name],
                                        base_plan_inputs=base_plan_inputs,
                                        slot_fillers=slot_fillers,
                                        input_fillers=assignments)
        return spec
