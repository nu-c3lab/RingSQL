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

from satyrn.core.Operations.ArgType import ArgType

class BasePlanInput:
    """
    A simple data structure that mirrors a single input to a base plan.
    e.g.
    "|A|": {
        "attribute_type": ["Metric"],
        "associated_slots": ["{Metric[0]}"],
        "filter": {
            "|0|": "(retrieve_entity {EntityClass[A]})",
            "|1|": "(retrieve_entity {RelatedEntityClass[A]})",
            "|2|": "(retrieve_attribute |1| {Datetime[0]})",
            "|3|": "(exact |2| \"{Datetime[0].Value[0]}\")",
            "|4|": "(retrieve_attribute |0| {Identifier[0]})",
            "|5|": "(exact |4| \"{Identifier[0].Value[0]}\")",
            "|6|": "(and |5| |3|)"
        }
    }
    """
    def __init__(self,
                 name: str,
                 attribute_type: List[ArgType],
                 associated_slots: List[str],
                 filter: Dict):
        self.name = name
        self.attribute_type = attribute_type
        self.associated_slots = associated_slots
        self.filter = filter

    @staticmethod
    def from_dict(base_plan_input_name: str,
                  base_plan_input_dict: Dict) -> 'BasePlanInput':
        return BasePlanInput(
            name=base_plan_input_name,
            attribute_type=[ArgType.from_str(s) for s in base_plan_input_dict["attribute_type"]],
            associated_slots=base_plan_input_dict["associated_slots"],
            filter=base_plan_input_dict["filter"]
        )
