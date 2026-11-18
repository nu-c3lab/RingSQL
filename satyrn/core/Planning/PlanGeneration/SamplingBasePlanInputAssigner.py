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
from collections import defaultdict

from satyrn.core.RingObjects.RingEntity import RingEntity
from satyrn.core.RingObjects.RingAttribute import RingAttribute
from satyrn.core.Operations.ArgType import ArgType
from satyrn.core.Planning.utils import intersect_lists
from satyrn.core.Document.BasePlanStore import BasePlanStore
from satyrn.core.Planning.PlanGeneration.PlanSlot import PlanSlot
from satyrn.core.Planning.PlanGeneration.BasePlanInput import BasePlanInput
from satyrn.core.Planning.PlanGeneration.InputAssignment import InputAssignment
from satyrn.core.Planning.CompositionSpecification import CompositionSpecification

class SamplingBasePlanInputAssigner:
    def __init__(self,
                 base_plan_store: BasePlanStore):
        self.base_plan_store = base_plan_store

    def get_input_assignment(self,
                             base_plan: Dict,
                             ent: RingEntity) -> Dict:
        assignment = {}
        remaining_input = [BasePlanInput.from_dict(input_name, input_dict) for input_name, input_dict in base_plan["input"].items()]
        available_attributes = defaultdict(list)
        for attr_name, attr in ent.attributes.items():
            # don't use derived attributes
            if attr.is_derived() and attr.name.startswith("median_"):
                continue
            for t in attr.type:
                available_attributes[t].append(attr)

        # Shuffle the available_attribute lists so we can just pop from them later to sample
        for arg_type, attr_list in available_attributes.items():
            random.shuffle(attr_list)

        while remaining_input:
            # Get the next input to be filled
            next_input_to_fill = self.get_next_input_to_fill(remaining_input, available_attributes)
            if len(next_input_to_fill.attribute_type) == 1:
                # Sample from the available_attributes
                if len(available_attributes[next_input_to_fill.attribute_type[0]]) < 1:
                    raise ValueError("No attributes of the entity can be assigned to the input slot of the base plan.")
                attr_to_assign = available_attributes[next_input_to_fill.attribute_type[0]].pop(0)

                # TODO: Throw error (or maybe catch error from above) if there are no available attributes to assign to this slot

                # Assign this sample to this input
                assignment[next_input_to_fill.name] = attr_to_assign

                # Update the remaining_inputs (remove this input from consideration; also remove other attributes that share slots with this input and assign them the same attribute)
                remaining_input.remove(next_input_to_fill)
                for input in remaining_input:
                    if len(intersect_lists([input.associated_slots, next_input_to_fill.associated_slots])) > 0:
                        assignment[input.name] = assignment[next_input_to_fill.name]

                # Clean up the remaining_input list by removing elements (i.e. inputs) that are already assigned
                for assigned_input_name in assignment.keys():
                    for ri in remaining_input:
                        if assigned_input_name == ri.name:
                            remaining_input.remove(ri)
                            break

                # Remove this attribute from every list it's in within available_attributes
                for t in attr_to_assign.type:
                    if attr_to_assign in available_attributes[t]:
                        available_attributes[t].remove(attr_to_assign)
            else:
                # handle multiple input slots
                assigned_attrs = []
                for attr_idx in range(len(next_input_to_fill.attribute_type)):
                    if len(available_attributes[next_input_to_fill.attribute_type[attr_idx]]) < 1:
                        raise ValueError("No attributes of the entity can be assigned to the input slot of the base plan.")
                    attr_to_assign = available_attributes[next_input_to_fill.attribute_type[attr_idx]].pop(0)

                    # TODO: Throw error (or maybe catch error from above) if there are no available attributes to assign to this slot

                    # Assign this sample to this input
                    assigned_attrs.append(attr_to_assign)


                    # Remove this attribute from every list it's in within available_attributes
                    for t in attr_to_assign.type:
                        if attr_to_assign in available_attributes[t]:
                            available_attributes[t].remove(attr_to_assign)
                assignment[next_input_to_fill.name] = assigned_attrs

                # Update the remaining_inputs (remove this input from consideration; also remove other attributes that share slots with this input and assign them the same attribute)
                remaining_input.remove(next_input_to_fill)
                for input in remaining_input:
                    if len(intersect_lists([input.associated_slots, next_input_to_fill.associated_slots])) > 0:
                        assignment[input.name] = assignment[next_input_to_fill.name]

                # Clean up the remaining_input list by removing elements (i.e. inputs) that are already assigned
                for assigned_input_name in assignment.keys():
                    for ri in remaining_input:
                        if assigned_input_name == ri.name:
                            remaining_input.remove(ri)
                            break
        return assignment

    def get_next_input_to_fill(self,
                               remaining_input: List[BasePlanInput],
                               available_attributes: Dict[ArgType, List[RingAttribute]]) -> BasePlanInput:
        next_input = remaining_input[0]
        for input in remaining_input[1:]:
            if self.get_input_priority(input, available_attributes) < self.get_input_priority(next_input, available_attributes):
                next_input = input

        return next_input

    def get_input_priority(self,
                           input: BasePlanInput,
                           available_attributes: Dict[ArgType, List[RingAttribute]]) -> int:
        return len(available_attributes[input.attribute_type[0]])

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

    def convert_new_assignment_to_composition_spec(self,
                                                   assignment: Dict,
                                                   base_plan_name: str) -> CompositionSpecification:
        """
        Transforms the base plan input assignments into a corresponding composition specification.
        :param assignment: The dictionary containing the mapping of base plan input name to the ring attribute that was assigned.
        :type assignment: Dict
        :param base_plan_name: The name of the base plan the assignment is for.
        :type base_plan_name: str
        :return: The composition specification
        :rtype: CompositionSpecification
        """

        base_plan_inputs = {}
        slot_fillers = {}
        for input_name, assigned_attr in assignment.items():
            # Add the access plan for this input
            base_plan_inputs[input_name] = {
                "access_plan": assigned_attr.access_plan
            }

            # Add the filters
            if self.base_plan_store.templates[base_plan_name]['input'][input_name]['filter']:
                # Get the filter and default joiner
                default_filter = self.base_plan_store.templates[base_plan_name]['input'][input_name]['filter']
                default_filter_joiner = "and"

                base_plan_inputs[input_name]["access_plan_filters"] = {
                    "filters": [default_filter],
                    "filter_joiner": default_filter_joiner
                }
            else:
                base_plan_inputs[input_name]["access_plan_filters"] = {
                    "filters": [],
                    "filter_joiner": None
                }

            # Add the RingAttribute that was assigned to this input
            base_plan_inputs[input_name]["ring_attribute"] = assigned_attr

            # Add attributes assigned to the inputs to the slots they will correspond to
            for associated_slot in self.base_plan_store.templates[base_plan_name]['input'][input_name]['associated_slots']:
                # Assign Identifier slots the name of the Identifier attribute
                associated_plan_slot = PlanSlot.from_string(associated_slot)
                if associated_plan_slot.s_type == 'Identifier' and ArgType.Identifier not in assigned_attr.type:
                    id_name = assigned_attr.parent_entity.id[0]
                    slot_fillers[associated_slot] = assigned_attr.parent_entity.attributes[id_name]
                elif associated_plan_slot.s_type == 'CompositeIdentifier':
                        # handle composite ids
                        id_names = assigned_attr.parent_entity.id
                        for i, id_name in enumerate(id_names):
                            slot_fillers["{CompositeIdentifier[" + str(i) + "]}"] = assigned_attr.parent_entity.attributes[id_name]
                else:
                    slot_fillers[associated_slot] = assigned_attr

        # Set up the plan_slot_fillers
        plan_slot_fillers = self.init_input_assignment_dict(self.base_plan_store.templates[base_plan_name]['input'])
        for slot, input_assignment in plan_slot_fillers.items():
            input_assignment.attr = assignment[next(iter(input_assignment.inputs))]

        # Create the specification object
        spec = CompositionSpecification(base_plan_name=base_plan_name,
                                        base_plan=self.base_plan_store.templates[base_plan_name],
                                        base_plan_inputs=base_plan_inputs,
                                        slot_fillers=slot_fillers,
                                        input_fillers=plan_slot_fillers)
        return spec

    def create_multi_access_plan(self, attrs):
        single_attr_plan = attrs[0].access_plan_without_id
        plan = {"|1|": single_attr_plan["|1|"], "|2|": single_attr_plan["|2|"]}
        step_id = 3
        for attr in attrs[1:]:
            plan[f"|{step_id}|"] = f"(retrieve_attribute |1| {attr.name})"
            step_id += 1
        plan[f"|{step_id}|"] = f"(collect {' '.join(['|' + str(i + 2)  + '|' for i in range(len(attrs))])})"
        plan[f"|{step_id + 1}|"] = f"(return |{step_id}|)"
        return plan


    def convert_new_assignment_to_composition_spec(self,
                                                   assignment: Dict,
                                                   base_plan_name: str,
                                                   base_plan_info: Dict,
                                                   include_id_in_access_plan=True) -> CompositionSpecification:
        """
        Transforms the base plan input assignments into a corresponding composition specification.
        :param assignment: The dictionary containing the mapping of base plan input name to the ring attribute that was assigned.
        :type assignment: Dict
        :param base_plan_name: The name of the base plan the assignment is for.
        :type base_plan_name: str
        :param base_plan_info: The name info dict of the base plan the assignment is for.
        :type base_plan_info: dict
        :param include_id_in_access_plan: Whether or not to include the id attribute in the access plans used
        :type include_id_in_access_plan: bool
        :return: The composition specification
        :rtype: CompositionSpecification
        """

        base_plan_inputs = {}
        slot_fillers = {}
        for input_name, assigned_attr in assignment.items():
            # Add the access plan for this input
            if isinstance(assigned_attr, list):
                base_plan_inputs[input_name] = {
                    "access_plan": self.create_multi_access_plan(assigned_attr)
                }
            else:
                base_plan_inputs[input_name] = {
                    "access_plan": assigned_attr.access_plan if include_id_in_access_plan else assigned_attr.access_plan_without_id
                    # "access_plan": assigned_attr.access_plan
                }

            # Add the filters
            # if self.base_plan_store.templates[base_plan_name]['input'][input_name]['filter']:
            if base_plan_info['input'][input_name]['filter']:
                # Get the filter and default joiner
                default_filter = base_plan_info['input'][input_name]['filter']
                default_filter_joiner = "and"

                base_plan_inputs[input_name]["access_plan_filters"] = {
                    "filters": [default_filter],
                    "filter_joiner": default_filter_joiner
                }
            else:
                base_plan_inputs[input_name]["access_plan_filters"] = {
                    "filters": [],
                    "filter_joiner": None
                }

            # Add the RingAttribute that was assigned to this input
            base_plan_inputs[input_name]["ring_attribute"] = assigned_attr

            # Add attributes assigned to the inputs to the slots they will correspond to
            for associated_slot in base_plan_info['input'][input_name]['associated_slots']:
                # Assign Identifier slots the name of the Identifier attribute
                associated_plan_slot = PlanSlot.from_string(associated_slot)
                if associated_plan_slot.s_type == 'Identifier' and ArgType.Identifier not in assigned_attr.type:
                    # ISSUE WITH LOWERCASE ID?
                    # TODO: fix this properly somewhere else
                    id_name = assigned_attr.parent_entity.id[0]
                    # print("ent_attrs:", assigned_attr.parent_entity.attributes.keys())
                    # id_case_insensitive_match = id_name
                    # for k in assigned_attr.parent_entity.attributes.keys():
                    #     if k.lower() == id_name:
                    #         print(id_name)
                    #         print(k)
                    #         id_name = k
                    #         break
                    slot_fillers[associated_slot] = assigned_attr.parent_entity.attributes[id_name]
                elif associated_plan_slot.s_type == 'CompositeIdentifier':
                        # handle composite ids
                        id_names = assigned_attr.parent_entity.id
                        # for id_idx in range(len(id_names)):
                        #     for k in assigned_attr.parent_entity.attributes.keys():
                        #         if k.lower() == id_names[id_idx]:
                        #             print(id_name)
                        #             print(k)
                        #             id_names[id_idx] = k
                        #             break
                        for i, id_name in enumerate(id_names):
                            slot_fillers["{CompositeIdentifier[" + str(i) + "]}"] = assigned_attr.parent_entity.attributes[id_name]
                else:
                    if isinstance(assigned_attr, list):
                        attr_idx = int(associated_slot.strip("{}").split("[")[-1].strip("]"))
                        slot_fillers[associated_slot] = assigned_attr[attr_idx]
                    else:
                        slot_fillers[associated_slot] = assigned_attr

        # Set up the plan_slot_fillers
        plan_slot_fillers = self.init_input_assignment_dict(base_plan_info['input'])
        for slot, input_assignment in plan_slot_fillers.items():
            input_assignment.attr = assignment[next(iter(input_assignment.inputs))]

        # Create the specification object
        spec = CompositionSpecification(base_plan_name=base_plan_name,
                                        base_plan=base_plan_info,
                                        base_plan_inputs=base_plan_inputs,
                                        slot_fillers=slot_fillers,
                                        input_fillers=plan_slot_fillers)
        return spec
