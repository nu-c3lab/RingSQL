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

from typing import Dict, List

from satyrn.core.RingObjects.RingEntity import RingEntity
from satyrn.core.RingObjects.RingAttribute import RingAttribute
from satyrn.core.Document.InformationRequirement import InformationRequirement

class EntityInstanceCategories(InformationRequirement):

    def __init__(self,
                 entity_name: str,
                 filter_attribute_name: str,
                 filter_value: str):
        super().__init__()
        self.entity_name = entity_name
        self.filter_attribute_name = filter_attribute_name
        self.filter_value = filter_value

    def get_plan_templates(self) -> List[Dict]:
        return [{
            "|1|": f"(retrieve_entity {self.entity_name})",
            "|2|": f"(retrieve_attribute |1| {self.filter_attribute_name})",
            "|3|": f"(exact |2| \"{self.filter_value}\")",
            "|4|": "(retrieve_attribute |1| {Categorical})",
            "|5|": "(collect |2| |4|)",
            "|6|": "(return |5| |3|)"
        }]
