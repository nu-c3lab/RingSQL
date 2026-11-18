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

import json
from pathlib import Path

class BasePlanStore:
    def __init__(self):
        # # Read in the JSON file of base_plan_templates.json
        # p = Path(__file__).with_name('base_plan_templates.json')
        # p = Path(__file__).with_name('improved_base_plans.json')
        
        p = Path(__file__).with_name('improved_base_plans_new_semantics.json')
        with p.open('r') as f:
            self.templates = json.load(f)


        # updated bps for spider style questions and filter templates
        # p = Path(__file__).with_name('spider_style_base_plans.json')
        # with p.open('r') as f:
        #     self.all_templates = json.load(f)
        #     self.templates = self.all_templates["BasePlans"]
        #     self.filter_templates = self.all_templates["FilterSubPlans"]