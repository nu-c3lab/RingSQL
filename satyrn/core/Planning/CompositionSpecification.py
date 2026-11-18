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

from typing import Dict

class CompositionSpecification:
    def __init__(self,
                 base_plan_name: str,
                 base_plan: Dict,
                 base_plan_inputs: Dict,
                 slot_fillers: Dict,
                 input_fillers: Dict = None):
        self.base_plan_name = base_plan_name
        self.base_plan = base_plan
        self.base_plan_inputs = base_plan_inputs
        self.slot_fillers = slot_fillers
        self.input_fillers = input_fillers

    def clean(self) -> None:
        """
        Cleans the composition specs in place.
        :return: None
        :rtype: None
        """
        # Remove any empty access plan filters from the composition specs
        for access_plan_ref, access_plan_spec in self.base_plan_inputs.items():
            access_plan_spec['access_plan_filters']['filters'] = list(filter(None, access_plan_spec['access_plan_filters']['filters']))

        return None
