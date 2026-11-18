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

from typing import List, Dict

from satyrn.core.Planning.CompositionSpecification import CompositionSpecification
from satyrn.core.Planning.PlanGeneration.PlanSlot import PlanSlot

from satyrn.core.Planning.utils import extract_slots

class SlotIdentifier:
    def __init__(self):
        pass

    def identify_slots_to_fill(self,
                               spec: CompositionSpecification,
                               include_filled_slots: bool = False,
                               slot_types_to_consider: List[str] = None,
                               ignore_value_slots: bool = False,
                               use_plan_template: bool = False,
                               use_question_templates: bool = False,
                               use_general_question_templates: bool = False,
                               use_statement_templates: bool = False,
                               use_filter_ents: bool = False) -> Dict[str, List]:
        """
        Determine which slots need to be filled in the base plan of the given composition specification.
        :param spec: The composition specification to check.
        :type spec: CompositionSpecification
        :param include_filled_slots: Should slots that already have filler values in the spec be included in the output.
        :type include_filled_slots: bool
        :param slot_types_to_consider: Used to constrain the identification of slots to fill to a pre-specified list.
        :type slot_types_to_consider: List[str]
        :param ignore_value_slots: A flag specifying whether or not slots which require a value for an attribute to be used as filler.
        :type ignore_value_slots: bool
        :param use_plan_template: A flag specifying whether slots should also be extracted from the plan templates (analytics_template, filters) of the base plan associated with the composition specification.
        :type use_plan_template: bool
        :param use_question_templates: A flag specifying whether slots should also be extracted from the question templates of the base plan associated with the composition specification.
        :type use_question_templates: bool
        :param use_general_question_templates: A flag specifying whether slots should also be extracted from the general question templates of the base plan associated with the composition specification.
        :type use_general_question_templates: bool
        :param use_statement_templates: A flag specifying whether slots should also be extracted from the statement templates of the base plan associated with the composition specification.
        :type use_statement_templates: bool
        :return:  A dictionary mapping slots to be filled to an empty list.
        :rtype: Dict[str, List]
        """

        slots_to_values = {}

        # Get slots in the analysis template
        if use_plan_template:
            for slot in self.identify_slots_in_sqr_dict(spec.base_plan['analysis_template']):
                slots_to_values[slot] = []

            # Get slots in the input filters
            for input_label, input_info in spec.base_plan['input'].items():
                for slot in self.identify_slots_in_sqr_dict(input_info['filter']):
                    slots_to_values[slot] = []
                
                # Get slots in "filter_ent"
                if use_filter_ents:
                    for slot in input_info.get("filter_ents", []):    
                        slots_to_values[slot] = []

        # Get slots in the question template
        if use_question_templates:
            for template in spec.base_plan['question_templates']:
                for slot in extract_slots(template):
                    slots_to_values[slot] = []

        # Get slots in the general question template
        if use_general_question_templates:
            for template in spec.base_plan['general_question_templates']:
                for slot in extract_slots(template):
                    slots_to_values[slot] = []

        # Get slots in the statement template
        if use_statement_templates:
            for template in spec.base_plan['statement_templates']:
                for slot in extract_slots(template):
                    slots_to_values[slot] = []

        # Remove slots that already have filler values in the spec
        if not include_filled_slots:
            for filled_slot in spec.input_fillers.keys():
                if filled_slot in slots_to_values:
                    del slots_to_values[filled_slot]
            for filled_slot in spec.slot_fillers.keys():
                if filled_slot in slots_to_values:
                    del slots_to_values[filled_slot]

        # Remove slots that are not ones that have been flagged for consideration
        if slot_types_to_consider:
            keys = list(slots_to_values.keys())
            for slot in keys:
                plan_slot = PlanSlot.from_string(slot)
                if plan_slot.s_type not in slot_types_to_consider:
                    del slots_to_values[slot]

        # Remove slots that contain "Value" from consideration
        if ignore_value_slots:
            keys = list(slots_to_values.keys())
            for slot in keys:
                plan_slot = PlanSlot.from_string(slot)
                if plan_slot.value_dec:
                    del slots_to_values[slot]

        return slots_to_values

    def identify_slots_in_sqr_dict(self,
                                   sqr_dict: Dict[str, str]) -> List[str]:
        """
        Extracts all slots in a given SQR plan dictionary.
        :param sqr_dict: The SQR plan dictionary to find slots in.
        :type sqr_dict: Dict[str, str]
        :return: A list of slots in the plan (e.g. ["{Metric[0]}", "{Identifier[0]}"])
        :rtype:
        """

        slots = []
        for step_ref, step in sqr_dict.items():
            slots.extend(extract_slots(step))
        return slots
