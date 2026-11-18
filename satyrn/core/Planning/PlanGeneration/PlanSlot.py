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

from typing import Tuple

class PlanSlot:
    def __init__(self,
                 s_type: str,
                 s_type_id: str,
                 value_dec: bool = False,
                 value_dec_id: str = None,
                 expression_dec: bool = False,
                 unit_dec: bool = False,
                 s_type_sub_id=None):
        self.s_type = s_type
        self.s_type_id = s_type_id
        self.value_dec = value_dec
        self.value_dec_id = value_dec_id
        self.expression_dec = expression_dec
        self.unit_dec = unit_dec
        self.s_type_sub_id = s_type_sub_id

    def __eq__(self, other):
        return self.__str__() == other.__str__()

    def __str__(self):
        # Start with the slot type and id
        s = f"{self.s_type}[{self.s_type_id}]"
        if self.s_type_sub_id:
            s += f"[{self.s_type_sub_id}]"

        # Add any decorators
        if self.value_dec:
            s += f".Value[{self.value_dec_id}]"
        if self.expression_dec:
            s += ".Expression"
        if self.unit_dec:
            s += ".Unit"

        # Add the brackets around the slot
        return f"{{{s}}}"

    @staticmethod
    def from_string(slot_string: str) -> 'PlanSlot':

        def get_info_for_slot_component_with_brackets(slot_component: str) -> Tuple[str, str]:
            slot_type_info = re.findall(r'([a-zA-Z]+)\[([a-zA-Z0-9]+)](?:\[([a-zA-Z0-9]+)])?', slot_component)    # outputs values like [('Metric', '0')] or ('Attribute', '0', '1')
            return slot_type_info[0]

        slot_component_strings = slot_string.strip("{}").split(".")

        # The first component should always be the slot type
        slot_type_info = get_info_for_slot_component_with_brackets(slot_component_strings.pop(0))
        s_type = slot_type_info[0]  # e.g. 'Metric'
        s_type_id = slot_type_info[1]
        # print(slot_type_info)
        s_type_sub_id = slot_type_info[2] if len(slot_type_info) > 2 else None

        # Create the PlanSlot object to be updated as required
        plan_slot = PlanSlot(s_type, s_type_id, s_type_sub_id=s_type_sub_id)

        for component_string in slot_component_strings:
            if "Value[" in component_string:
                slot_type_info = get_info_for_slot_component_with_brackets(component_string)
                plan_slot.value_dec = True
                plan_slot.value_dec_id = slot_type_info[1]

            elif "Expression" in component_string:
                plan_slot.expression_dec = True

            elif "Unit" in component_string:
                plan_slot.unit_dec = True

        return plan_slot
