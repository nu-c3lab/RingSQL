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

import copy
import re

from satyrn.core.RingObjects.Ring import Ring
from satyrn.core.Planning.SQRComposer import SQRComposer
from satyrn.core.Document.BasePlanStore import BasePlanStore
from satyrn.core.Analysis.OperationOntology import OperationOntology
from satyrn.core.Planning.CompositionSpecification import CompositionSpecification
from satyrn.core.Operations.ArgType import ArgType
from satyrn.core.Planning.StepExpressor import StepExpressor
from satyrn.core.Planning.AnalysisPlanParser import AnalysisPlanParser
from satyrn.core.Planning.utils import get_reference_attributes
from satyrn.core.Planning.PlanGeneration.FillerIdentifier import FillerIdentifier
from satyrn.core.Analysis.AnalysisStep import AnalysisStep
from satyrn.core.Planning.PlanGeneration.PlanSlot import PlanSlot
from satyrn.core.Planning.StatementGenerator import StatementGenerator

class SlotExpressor:
    def __init__(self,
                 ring: Ring,
                 operation_ontology: OperationOntology,
                 sqr_composer: SQRComposer,
                 base_plan_store: BasePlanStore):
        self.ring = ring
        self.operation_ontology = operation_ontology
        self.sqr_composer = sqr_composer
        self.base_plan_store = base_plan_store
        self.statement_generator = StatementGenerator(self.ring, self.operation_ontology)
        self.step_expressor = StepExpressor(self.ring, self.operation_ontology, self.statement_generator)
        self.analysis_plan_parser = AnalysisPlanParser(self.operation_ontology)
        self.filler_identifier = FillerIdentifier(self.ring, self.operation_ontology)
        self.identifier_value_cache = {}

    def get_slot_expression(self,
                            plan_slot: PlanSlot,
                            spec: CompositionSpecification) -> str:
        """
        Wrapper function for getting expression for a given slot.
        :param slot: The slot to express in natural language.
        :type slot: PlanSlot
        :param spec: The composition spec the slot belongs to.
        :type spec: CompositionSpecification
        :return: A string expressing the slot
        :rtype: str
        """

        if plan_slot.s_type in ["Categorical", "Arithmetic", "Metric", "Datetime", "Attribute"] and plan_slot.expression_dec and not plan_slot.value_dec:
            return self.get_input_attribute_expression(plan_slot, spec)
        
        elif plan_slot.s_type in ["RelatedAttribute", "RelatedEntity"] and plan_slot.expression_dec and not plan_slot.value_dec:
            return self.get_input_attribute_expression(plan_slot, spec)

        elif plan_slot.s_type == "Metric" and plan_slot.value_dec and not plan_slot.unit_dec:
            return self.get_metric_value_expression(plan_slot, spec)

        elif plan_slot.s_type == "Metric" and plan_slot.value_dec and plan_slot.unit_dec:
            return self.get_metric_value_unit(plan_slot, spec)

        elif plan_slot.s_type == "Identifier" and plan_slot.value_dec and plan_slot.expression_dec:
            return self.get_identifier_value_expression(plan_slot, spec)

        elif plan_slot.s_type == "CompositeIdentifier" and plan_slot.value_dec and plan_slot.expression_dec:
            return self.get_identifier_value_expression(plan_slot, spec)

        elif plan_slot.s_type == "Datetime" and plan_slot.value_dec and plan_slot.expression_dec:
            return self.get_datetime_value_expression(plan_slot, spec)

        elif plan_slot.s_type == "EntityClass" and plan_slot.expression_dec:
            return self.get_entity_class_expression(plan_slot, spec)

        elif plan_slot.s_type == "Direction" and plan_slot.expression_dec:
            return self.get_direction_expression(plan_slot, spec)

        elif plan_slot.s_type == "Filter" and plan_slot.expression_dec:
            return self.get_filter_expression(plan_slot, spec)

        elif plan_slot.s_type == "Analysis" and plan_slot.expression_dec:
            # TODO: may want to handle this and the one below like comparisons? resolve operation and use format string?
            return self.get_analysis_expression(plan_slot, spec)
        
        elif plan_slot.s_type == "SetOp" and plan_slot.expression_dec:
            return self.get_analysis_expression(plan_slot, spec)
        
        elif plan_slot.s_type == "NumericComparison" and plan_slot.expression_dec:
            return self.get_comparison_expression(plan_slot, spec)

        elif plan_slot.s_type == "Reference" and plan_slot.expression_dec:
            return self.get_reference_expression(plan_slot, spec)

        elif plan_slot.s_type == "Quantity":
            return self.get_quantity_expression(plan_slot, spec)

        raise ValueError(f"Unhandled expression slot: {str(plan_slot)}")

    def get_filter_expression(self,
                              slot: PlanSlot,
                              spec: CompositionSpecification) -> str:
        # Get the corresponding attribute passed into the input slot of the base plan
        ref_letter = slot.s_type_id

        # Get the filter steps that are associated with this base plan input
        input_filter_info = spec.base_plan_inputs["|" + ref_letter + "|"]["access_plan_filters"]

        # Compose this input_filter_info into a single set of steps
        if input_filter_info["filters"]:

            # Make sure the filters plans are parsed in the form required for composition (i.e. Dict[str, AnalysisStep])
            parsed_filter_plans = []
            for p in input_filter_info["filters"]:
                if isinstance(p[list(p.keys())[0]], AnalysisStep):
                    parsed_filter_plans.append(p)
                else:
                    parsed_filter_plans.append(self.analysis_plan_parser.create_analysis_steps(p))

            # Compose the filter plans
            filter_steps_on_input = self.sqr_composer.compose_filter_plans(parsed_filter_plans,
                                                                           input_filter_info["filter_joiner"],
                                                                           spec.slot_fillers)

            # Parse the plan into the necessary object (i.e. AnalysisPlan)
            filter_plan = self.analysis_plan_parser.parse_plan_snippet_from_analysis_steps(filter_steps_on_input)

            # Get the reference of the final filter step
            final_step_ref = filter_plan.get_leaves()[0]

            # Call the step_expressor to express the filter step in natural language
            return "for " + self.step_expressor.express_filter_step(final_step_ref, filter_plan)
        else:
            return ""

    def get_input_attribute_expression(self,
                                       slot: PlanSlot,
                                       spec: CompositionSpecification) -> str:
        # Get the corresponding non-expression version of the slot
        non_expression_slot = copy.deepcopy(slot)
        non_expression_slot.expression_dec = False
        if slot.s_type_sub_id:
            ring_attribute = spec.input_fillers[str(non_expression_slot)].attr[int(slot.s_type_sub_id)]
        else:
            ring_attribute = spec.input_fillers[str(non_expression_slot)].attr

        return ring_attribute.nicename[0]

    def get_metric_value_expression(self,
                                    slot: PlanSlot,
                                    spec: CompositionSpecification) -> str:
        # Get the corresponding Metric.Value slot
        metric_value_slot = copy.deepcopy(slot)
        metric_value_slot.expression_dec = False

        metric_value = spec.slot_fillers[str(metric_value_slot)]

        return str(metric_value)

    def get_metric_value_unit(self,
                              slot: PlanSlot,
                              spec: CompositionSpecification) -> str:
        # Get the corresponding Metric slot
        metric_value_slot = copy.deepcopy(slot)
        metric_value_slot.expression_dec = False
        metric_value_slot.unit_dec = False

        # Get the corresponding attribute
        metric_value_attr = self.filler_identifier.get_attribute_for_value_slot(str(metric_value_slot), spec)

        return metric_value_attr.units[1] if metric_value_attr.units else ""

    def get_identifier_value_expression(self,
                                        slot: PlanSlot,
                                        spec: CompositionSpecification) -> str:
        # Get the corresponding IdentifierValue slot to be expressed
        identifier_value_slot = copy.deepcopy(slot)
        identifier_value_slot.expression_dec = False

        # Get the attribute associated with that IdentifierValue
        identifier_ring_attribute = self.filler_identifier.get_attribute_for_value_slot(str(identifier_value_slot), spec)

        # Get the corresponding Identifier attribute (i.e. the one with the same reference number)
        # ref_number = get_slot_reference(slot)
        # identifier_slot = f"{{Identifier:{ref_number}}}"  # TODO: This is wrong. The IdentifierValueExpression doesn't necessarily correspond to the Identifer with the same reference number (i.e. IdentifierValueExpression:13 != Identifier:13)
        # identifier_ring_attribute = spec.plan_slot_fillers[identifier_slot].attr
        # identifier_value_slot = f"{{IdentifierValue:{ref_number}}}"

        # Express the identifier using the raw value of the identifier (the commented out code below this is how it should really be done)
        # spec.slot_fillers[slot] = spec.slot_fillers[identifier_value_slot]

        # Express the identifier using the reference of the RingEntity
        entity = identifier_ring_attribute.parent_entity
        entity_instance_identifier_attribute_name = entity.id[0]  # TODO: In the future: could look this up directly in the access plan
        entity_instance_identifier_value = spec.slot_fillers[str(identifier_value_slot)]

        return self.look_up_identifier_value_expression(entity.name,
                                                        entity_instance_identifier_attribute_name,
                                                        entity_instance_identifier_value)

    def look_up_identifier_value_expression(self,
                                            entity_name: str,
                                            entity_instance_identifier_attribute_name: str,
                                            entity_instance_identifier_value: str) -> str:
        entity = self.ring.get_entity_by_name(entity_name)
        if entity.reference and ArgType.Identifier in entity.attributes[entity_instance_identifier_attribute_name].type:
            # Retrieve all the values needed for filling the reference from the database
            instance_results_dict = self.step_expressor.get_reference_values_for_one(entity_name, entity_instance_identifier_attribute_name, entity_instance_identifier_value, entity.reference)
            instance_results = instance_results_dict['results'][0]

            # Fill the reference template
            reference_attributes = get_reference_attributes(entity.reference)
            # reference_attributes.insert(0, entity_instance_identifier_attribute_name)
            out = entity.reference.format(**{attribute_name: result for attribute_name, result in zip(reference_attributes, instance_results)})
            return out

        else:
            return entity_instance_identifier_value

    def get_entity_class_expression(self,
                                    slot: PlanSlot,
                                    spec: CompositionSpecification) -> str:
        # Get the corresponding attribute passed into the input slot of the base plan
        ref_letter = slot.s_type_id
        corresponding_input_attr = [slot_filler.attr for slot_filler in spec.input_fillers.values() if "|" + ref_letter + "|" in slot_filler.inputs][0]

        # Get the parent entity of this attribute and its nicename
        if isinstance(corresponding_input_attr, list):
            return corresponding_input_attr[0].parent_entity.nicename[0]
        else:
            return corresponding_input_attr.parent_entity.nicename[0]

    def get_direction_expression(self,
                                 slot: PlanSlot,
                                 spec: CompositionSpecification) -> str:
        direction_slot = copy.deepcopy(slot)
        direction_slot.expression_dec = False

        direction_slot_value = spec.slot_fillers[str(direction_slot)]

        # Express the direction and store the value as the filler
        if direction_slot_value == "asc":
            return "ascending"
        elif direction_slot_value == "desc":
            return "descending"
        else:
            raise ValueError(f"Unknown Direction filler: {direction_slot_value}")

    def get_datetime_value_expression(self,
                                      slot: PlanSlot,
                                      spec: CompositionSpecification) -> str:
        # Get the corresponding DatetimeValue slot that should be expressed
        datetime_value_slot = copy.deepcopy(slot)
        datetime_value_slot.expression_dec = False

        # Look it up in the spec's slot fillers and return the value
        value = spec.slot_fillers[str(datetime_value_slot)]

        return str(value)

    def get_analysis_expression(self,
                                slot: PlanSlot,
                                spec: CompositionSpecification) -> str:
        # Get the corresponding Analysis slot that should be expressed
        analysis_slot = copy.deepcopy(slot)
        analysis_slot.expression_dec = False

        return spec.slot_fillers[str(analysis_slot)]
    
    def get_comparison_expression(self,
                                slot: PlanSlot,
                                spec: CompositionSpecification) -> str:
        # Get the corresponding Analysis slot that should be expressed
        analysis_slot = copy.deepcopy(slot)
        analysis_slot.expression_dec = False

        # TODO: strip formatting placeholders?
        return re.sub(r"\{[^}]*\}", "", self.operation_ontology.resolve_operation(spec.slot_fillers[str(analysis_slot)]).template).strip()

    def get_reference_expression(self,
                                 slot: PlanSlot,
                                 spec: CompositionSpecification) -> str:
        # Only need to return a placeholder since this will be generated and filled by the statement generator
        return "REFERENCE_PLACEHOLDER"

    def get_quantity_expression(self,
                                slot: PlanSlot,
                                spec: CompositionSpecification) -> str:
        # Only need to return a placeholder since this will be generated and filled by the statement generator
        # Get the corresponding Analysis slot that should be expressed
        quantity_slot = copy.deepcopy(slot)
        quantity_slot.expression_dec = False

        return spec.slot_fillers[str(quantity_slot)]
