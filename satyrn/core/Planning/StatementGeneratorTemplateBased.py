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
import copy
from enum import Enum
from typing import Dict, List

from satyrn.core.api import utils
from satyrn.core.RingObjects.Ring import Ring
from satyrn.core.Planning.utils import capitalize_first_only, oxfordcomma
from satyrn.core.Analysis.AnalysisPlan import AnalysisPlan
from satyrn.core.Planning.StepExpressor import StepExpressor
from satyrn.core.Analysis.OperationOntology import OperationOntology
from satyrn.core.Planning.AnalysisPlanParser import AnalysisPlanParser
from satyrn.core.Planning.QuestionGenerator import QuestionGenerator
from satyrn.core.Planning.StatementGenerator import StatementGenerator
from satyrn.core.Planning.SQRComposer import SQRComposer
from satyrn.core.Operations.ArgType import ArgType
from satyrn.core.Planning.utils import extract_slots, remove_extra_whitespace
from satyrn.core.Planning.PlanGeneration.PlanSlot import PlanSlot

class GenerationMode(Enum):
    OneStatementPerRow = 1
    OneStatementPerPlan = 2

class StatementGeneratorTemplateBased:
    def __init__(self,
                 ring: Ring,
                 operation_ontology: OperationOntology,
                 mode: GenerationMode = GenerationMode.OneStatementPerPlan):
        self.ring = ring
        self.operation_ontology = operation_ontology
        self.plan_parser = AnalysisPlanParser(self.operation_ontology)
        self.sqr_composer = SQRComposer(ring, operation_ontology)
        self.mode = mode
        self.step_expressor = StepExpressor(self.ring, self.operation_ontology, StatementGenerator(self.ring, self.operation_ontology))
        self.question_generator = QuestionGenerator(self.ring, self.operation_ontology)

    def generate_statement(self,
                           statement_template: str,
                           result: Dict,
                           slot_fillers: Dict,
                           analysis_plan: AnalysisPlan,
                           filter_steps_for_postfix: Dict[str, AnalysisPlan],
                           is_question: bool = False,
                           plan_slot_fillers = None) -> str:
        # Make a copy of the template to fill
        factual_statement = copy.deepcopy(statement_template)

        slots_to_fill = extract_slots(factual_statement)
        for slot in slots_to_fill:
            plan_slot = PlanSlot.from_string(slot)
            if plan_slot.s_type == "Reference" and plan_slot.expression_dec and not plan_slot.value_dec:
                # reference_number = get_slot_reference(slot)
                reference_number = plan_slot.s_type_id
                expressed_step = self.step_expressor.express_step("|" + str(reference_number) + "|", analysis_plan)
                factual_statement = factual_statement.replace(str(plan_slot), str(expressed_step))

            elif plan_slot.s_type == "Metric" and not plan_slot.expression_dec and not plan_slot.value_dec:
                # metric_ref = slots_to_ref[slot]
                # express_ref = self.step_expressor.express_step(metric_ref[0], analysis_plan)
                # factual_statement = factual_statement.replace(slot, str(express_ref))
                factual_statement = factual_statement.replace(str(plan_slot), plan_slot_fillers[str(plan_slot)]['attr'].nicename[0])

            elif plan_slot.s_type != 'Result':
                # Fill any remaining slots that aren't Result or Filter slots
                slot_key = extract_slots(str(plan_slot))[0]
                factual_statement = factual_statement.replace(str(plan_slot), str(slot_fillers[slot_key]))

        # Fill in result and unit slots
        result_slots_to_fill = [slot for slot in slots_to_fill if PlanSlot.from_string(slot).s_type == 'Result']

        # More than one result (fill in the slots in the <repeat> tags, comma separate the values)
        if is_question:
            pass
        elif result['length'] > 1:

            # Get the string between the <repeat> tags
            statement_segment_to_repeat = re.findall(r'<repeat>(.+?)</repeat>', factual_statement)[0]

            # For each row of results
            all_statement_segments = []
            for result_value_list in result['results']:

                # Make a copy of the string between the <repeat> tags
                statement_segment = copy.deepcopy(statement_segment_to_repeat)

                # Fill in the slots for the current copy
                for slot in result_slots_to_fill:
                    plan_slot = PlanSlot.from_string(slot)
                    slot_number = int(plan_slot.s_type_id)
                    if plan_slot.s_type == "Result" and not plan_slot.unit_dec:
                        filler = self.get_result_filler(slot_number, result_value_list, result['fieldNames'], analysis_plan)
                        statement_segment = statement_segment.replace(str(plan_slot), filler)

                    elif plan_slot.s_type == "Result" and plan_slot.unit_dec:
                        filler = self.get_unit_filler(slot_number, result_value_list, result['fieldNames'], analysis_plan, result['units']['results'])
                        statement_segment = statement_segment.replace(str(plan_slot), filler)

                # Save this segment
                all_statement_segments.append(statement_segment)

            # Replace the original string (including <repeat> tags) in the factual statement with the collection of statements
            factual_statement = factual_statement.replace("<repeat>" + statement_segment_to_repeat + "</repeat>", oxfordcomma(all_statement_segments))

        elif result['length'] == 1:
            # Only one result
            result_value_list = result['results'][0]
            for slot in result_slots_to_fill:
                plan_slot = PlanSlot.from_string(slot)
                slot_number = int(plan_slot.s_type_id)
                if plan_slot.s_type == "Result" and not plan_slot.unit_dec:
                    filler = self.get_result_filler(slot_number, result_value_list, result['fieldNames'], analysis_plan)
                    factual_statement = factual_statement.replace(str(plan_slot), filler)


                elif plan_slot.s_type == "Result" and plan_slot.unit_dec:
                    filler = self.get_unit_filler(slot_number, result_value_list, result['fieldNames'], analysis_plan, result['units']['results'])
                    factual_statement = factual_statement.replace(str(plan_slot), filler)

        ## Add filters to the factual statements
        # return_step = list(analysis_plan.plan_steps.keys())[-1]
        # step = analysis_plan.plan_steps[return_step]
        # filter_steps_to_add = [ret_arg for ret_arg in step.args if self.operation_ontology.is_boolean_operation(analysis_plan.plan_steps[ret_arg].operation)]
        if filter_steps_for_postfix:
            filter_plan = self.plan_parser.parse_plan_snippet(filter_steps_for_postfix)

            # Get the reference of the final filter step
            final_step_ref = filter_plan.get_leaves()[0]

            # Call the step_expressor to express the filter step in natural language
            filter_statement = "with " + self.step_expressor.express_filter_step(final_step_ref, filter_plan)

            # Add the filter to the factual statement
            if filter_statement:
                if factual_statement.endswith((".", "?", "!")):
                    factual_statement  = factual_statement[0:-1] + " " + filter_statement + factual_statement[-1:]
                else:
                    factual_statement = factual_statement + " " + filter_statement + "."

        # Make sure the first letter of each statement is capitalized
        factual_statement = capitalize_first_only(factual_statement)

        # Remove any unnecessary whitespace
        factual_statement = remove_extra_whitespace(factual_statement)

        return factual_statement

    def get_result_filler(self,
                          slot_number: int,
                          result: List,
                          field_names: List,
                          analysis_plan: AnalysisPlan) -> str:
        # Pull out the raw value of the desired result from the result dictionary
        answer = str(result[slot_number])
        if len(result) == 1 and answer in ['True', 'False']:
            return 'is' if answer == 'True' else 'is not'

        # Convert any results that are for an Identifier attribute into the EntityReference for the corresponding ID
        field_dict = utils.entity_from_subquery_name(field_names[slot_number], list(analysis_plan.subplans.keys()))
        if field_dict:
            entity = self.ring.get_entity_by_name(field_dict['entity'])
        if field_dict and entity.reference and ArgType.Identifier in entity.attributes[field_dict['field']].type:
            # If the result to populate is an identifier attribute and the entity has a reference to stick in there
            answer = self.step_expressor.fill_reference_template(field_dict['entity'], field_dict['field'], answer, entity.reference)

        return answer

    def get_unit_filler(self,
                        slot_number: int,
                        result: List,
                        field_names: List,
                        analysis_plan: AnalysisPlan,
                        units: List) -> str:
        # Convert any results that are for an Identifier attribute into the EntityReference for the corresponding ID
        field_dict = utils.entity_from_subquery_name(field_names[slot_number], list(analysis_plan.subplans.keys()))
        if field_dict:
            entity = self.ring.get_entity_by_name(field_dict['entity'])
        if field_dict and entity.reference and ArgType.Identifier in entity.attributes[field_dict['field']].type:
            # If the result to populate is an identifier attribute and the entity has a reference to stick in there
            return ""
        elif len(units[slot_number][1]) > 0:
            # Otherwise, if there are units, add the units
            return units[slot_number][1]
        return ""
