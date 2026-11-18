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

class BasePlan:
    def __init__(self,
                 name: str,
                 input: Dict,
                 analysis_template: Dict,
                 description: str,
                 statement_templates: List[str],
                 question_templates: List[str],
                 general_question_templates: List[str]):
        self.name = name
        self.input = input
        self.analysis_template = analysis_template
        self.description = description
        self.statement_templates = statement_templates
        self.question_templates = question_templates
        self.general_question_templates = general_question_templates
