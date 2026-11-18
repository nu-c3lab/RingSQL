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
from satyrn.core.Document.InformationRequirement import InformationRequirement

class EntityClassWithMetrics(InformationRequirement):

    def __init__(self,
                 entity_name: str):
        super().__init__()
        self.entity_name = entity_name

    def get_plan_templates(self) -> List[Dict]:
        return [{
            "|1|": f"(retrieve_entity {self.entity_name})",
            "|2|": "(retrieve_attribute |1| {Metric})",
            "|3|": "({Analysis} |2|)",
            "|4|": "(collect |3|)",
            "|5|": "(return |4|)"
        },
        {
            "|1|": f"(retrieve_entity {self.entity_name})",
            "|2|": "(retrieve_attribute |1| {Metric})",
            "|3|": "(retrieve_attribute |1| {Categorical})",
            "|4|": "(groupby |3|)",
            "|5|": "({Analysis} |2| |4|)",
            "|6|": "(collect |3| |5|)",
            "|7|": "(return |6|)"
        }]
