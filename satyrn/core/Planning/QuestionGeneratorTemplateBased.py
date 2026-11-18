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

from satyrn.core.RingObjects.Ring import Ring
from satyrn.core.Analysis.AnalysisPlan import AnalysisPlan
from satyrn.core.Document.BasePlanStore import BasePlanStore
from satyrn.core.Analysis.OperationOntology import OperationOntology
from satyrn.core.Planning.StatementGeneratorTemplateBased import StatementGeneratorTemplateBased

class QuestionGeneratorTemplateBased:
    def __init__(self,
                 ring: Ring,
                 operation_ontology: OperationOntology,
                 base_plan_store = None):
        self.ring = ring
        self.operation_ontology = operation_ontology
        self.base_plan_store = BasePlanStore() if not base_plan_store else base_plan_store
        self.statement_generator = StatementGeneratorTemplateBased(self.ring, self.operation_ontology)
    def generate_question(self,
                          sentence_template: str,
                          slot_fillers: Dict,
                          analysis_plan: AnalysisPlan,
                          filter_steps_for_postfix: Dict[str, AnalysisPlan],
                          plan_slot_fillers = None) -> str:
        return self.statement_generator.generate_statement(sentence_template,
                                                           {},
                                                           slot_fillers,
                                                           analysis_plan,
                                                           filter_steps_for_postfix,
                                                           is_question=True,
                                                           plan_slot_fillers=plan_slot_fillers)
    
    def combine_filter_expression_with_question(self, question, filter_expression):
        return f"""{question.strip("?")} with {filter_expression}?"""
