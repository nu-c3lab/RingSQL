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

import random
import numpy as np
from typing import List, Dict, Any, Union, Tuple
from collections import defaultdict
from contextlib import closing
from sqlalchemy.sql.expression import func

from satyrn.core.Operations.ArgType import ArgType
from satyrn.core.RingObjects.Ring import Ring
from satyrn.core.RingObjects.RingEntity import RingEntity
from satyrn.core.Analysis.AnalysisStep import AnalysisStep
from satyrn.core.RingObjects.RingAttribute import RingAttribute
from satyrn.core.Analysis.OperationOntology import OperationOntology
from satyrn.core.Planning.AnalysisPlanParser import AnalysisPlanParser
from satyrn.core.Planning.CompositionSpecification import CompositionSpecification
from satyrn.core.Planning.PlanGeneration.PlanSlot import PlanSlot
from satyrn.core.Analysis.AnalysisEngine import AnalysisEngine
from satyrn.core.Planning.PlanGeneration.CacheManager import CacheManager

from satyrn.core.api.utils import is_arg_reference
from satyrn.core.Planning.utils import extract_slots, is_slot

class FillerIdentifier:
    """
    A class for determining values that can fill a given slot.
    """
    def __init__(self,
                 ring: Ring,
                 operation_ontology: OperationOntology,
                 cache_manager: CacheManager = None):
        self.ring = ring
        self.operation_ontology = operation_ontology
        self.analysis_plan_parser = AnalysisPlanParser(self.operation_ontology)
        self.cache_manager = cache_manager if cache_manager else CacheManager(self.ring)

    def simplify_rel_type(self, rel_types):
        # cases:
        #   -   o2o o2o -> o2o
        #   -   o2o o2m -> o2m
        #   -   o2o m2o -> m2o
        #   -   o2o m2m -> m2m

        #   -   o2m o2o -> o2m
        #   -   o2m o2m -> o2m
        #   -   o2m m2o -> m2m
        #   -   o2m m2m -> m2m

        #   -   m2m o2o -> m2m
        #   -   m2m o2m -> m2m
        #   -   m2m m2o -> m2m
        #   -   m2m m2m -> m2m

        #   -   m2o o2o -> m2o
        #   -   m2o o2m -> m2m
        #   -   m2o m2o -> m2o
        #   -   m2o m2m -> m2m

        if len(rel_types) == 1:
            return rel_types[0]
        
        if "m2m" in rel_types:
            return "m2m"
        
        collapsed_rel_types = [t for t in rel_types if t != "o2o"]
        if len(collapsed_rel_types) == 0:
            return "o2o"
        
        for rel_type in collapsed_rel_types[1:]:
            if rel_type != collapsed_rel_types[0]:
                return "m2m"
        
        return collapsed_rel_types[0]

    def get_related_ents(self,
                         ent: RingEntity,
                         remove_ambiguous_joins: bool=True) -> List[RingEntity]:
        """
        Returns a list of entities directly related to the given entity on the many side of a relationship.
        :param ent: The entity to find related entities for.
        :type ent: RingEntity
        :param remove_ambiguos_joins: Whether to include related entities with multiple direct join paths to the given entity.
        :type remove_ambiguos_joins: bool
        :return: A list of entites directly related to ent.
        :rtype: List[RingEntity]
        """
        related_ents = []
        # want outer query to be on this entity, where one col is in a subquery on another entity
        for e in self.ring.entities:
            if e == ent:
                continue
            try:
                paths = self.ring.relationship_graph.get_all_direct_paths(e.name, ent.name, cutoff=None)
            except:
                continue
        
            # ignore entities related through multiple direct paths (length 1) if needed
            if remove_ambiguous_joins and len(paths) != 1:
                continue
            else:
                if paths[0]:
                    prev_ent_name = ent.name
                    rel_types = []
                    for rel_name in reversed(paths[0]):
                        rel = None
                        for temp_rel in self.ring.relationships:
                            if temp_rel.name == rel_name:
                                rel = temp_rel
                        if rel:            
                            if rel.fro == prev_ent_name:
                                rel_type = rel.type
                                prev_ent_name = rel.to
                            elif rel.to == prev_ent_name:
                                rel_type = rel.type[::-1]
                                prev_ent_name = rel.fro
                            else:
                                raise ValueError("Unsupported relationship used")
                            rel_types.append(rel_type)
                    related_ents.append((e, rel_types))
        return related_ents

    def sample_value_for_slot(self,
                              slot: str,
                              spec: CompositionSpecification) -> Any:
        """
        Get a single value for the specified slot.
        :param slot: The slot for which to determine the filler values.
        :type slot: str
        :param spec: The composition specification this slot is from.
        :type spec: CompositionSpecification
        :return: A value that can fill the given slot.
        :rtype: Any
        """
        filler_values = self.identify_filler(slot, spec)

        if len(filler_values) < 1:
            raise ValueError(f"No filler value found for slot '{slot}'.")
        random.shuffle(filler_values)
        # handle composite ids
        plan_slot = PlanSlot.from_string(slot)
        if plan_slot.s_type == "CompositeIdentifier":
            if plan_slot.value_dec:
                return filler_values[0][int(plan_slot.s_type_id)]
            else:
                return filler_values[int(plan_slot.s_type_id)]
        else:
            return filler_values[0]
        

    def identify_filler(self,
                        slot: str,
                        spec: CompositionSpecification,
                        n_id_attr_filler: int = 1,
                        n_quantity_filler: int = 1) -> List[Any]:
        """
        Determines a set of viable filler values for a given slot.
        :param slot: The slot for which to determine the filler values.
        :type slot: str
        :param spec: The composition specification this slot is from.
        :type spec: CompositionSpecification
        :param n_id_attr_filler: The number of values to return from the database for RingAttributes that have type Identifier.
        :type n_id_attr_filler: int
        :return: A list of values
        :rtype: List
        """

        plan_slot = PlanSlot.from_string(slot)

        if plan_slot.s_type == "Quantity":
            return self.get_quantity_fillers(n_quantity_filler)       # TODO: This needs to be A LOT better

        elif plan_slot.s_type == "Analysis":
            # TODO: handle sql dialects and remove median for sqlite
            # return ["average", "max", "min", "count_unique", "sum", "median"]
            # re for search: 
            #   \(average |\(max |\(min |\(count_unique |\(count |\(sum 
            return ["average", "max", "min", "count_unique", "count", "sum"]

        elif plan_slot.s_type == "Direction":
            return ["desc", "asc"]
        
        elif plan_slot.s_type == "SetOp":
            return ["except", "intersect", "union"]
        
        elif plan_slot.s_type == "NumericComparison":
            return ["greaterthan", "lessthan", "greaterthan_eq", "lessthan_eq", "exact"]

        elif plan_slot.s_type in ["Metric", "Identifier", "CompositeIdentifier", "Datetime", "Categorical", "Arithmetic", "Attribute"] and not plan_slot.value_dec and not plan_slot.expression_dec:
            # Get all the steps associated with this slot in the base plan, and filters
            steps_dict = self.get_steps_associated_with_slot(slot, spec)

            if len(steps_dict['analysis_template']) > 0:
                analysis_template_steps = self.analysis_plan_parser.create_analysis_steps(spec.base_plan['analysis_template'])

                for step_ref in steps_dict['analysis_template']:
                    if analysis_template_steps[step_ref].operation == "retrieve_attribute":
                        # Get the entity associated with the slot in this step
                        entity = self.find_entity_for_retrieve_attribute_step(step_ref, analysis_template_steps, spec)

                        # Get attributes with the slot type from the entity
                        slot_type = ArgType.from_str(plan_slot.s_type)
                        attributes = entity.get_attributes_with_type(slot_type)
                        if len(attributes) < 1:
                            raise ValueError(f"No attributes of {slot_type} type found for entity {entity.name}.")
                        return [attr for attr in attributes]

            elif len(steps_dict['input_filters']) > 0:
                for input_label, step_list in steps_dict['input_filters'].items():
                    filter_steps = self.analysis_plan_parser.create_analysis_steps(spec.base_plan['input'][input_label]['filter'])

                    for step_ref in step_list:
                        if filter_steps[step_ref].operation == 'retrieve_attribute':
                            # Get the entity associated with the slot in this step
                            entity = self.find_entity_for_retrieve_attribute_step(step_ref, filter_steps, spec)
                            # Get attributes with the slot type from the entity
                            arg_type = ArgType.from_str(plan_slot.s_type)
                            attributes = entity.get_attributes_with_type(arg_type)
                            return [attr for attr in attributes]
            else:
                raise ValueError("Slot not found in analysis template or input filters.")

        elif plan_slot.expression_dec:
            return []

        elif plan_slot.value_dec:
            # Get the corresponding slot that the values should correspond to (e.g. {Identifier[0]} for {Identifier[0].Value[5]})
            # TODO: Update this so that we better get values using the new semantic
            if plan_slot.s_type == "Identifier":
                parent_slot_filler_attr = self.get_attribute_for_value_slot(slot, spec)
                # handle composite ids
                if len(parent_slot_filler_attr.parent_entity.id) == 1:
                    filler_attr_name = parent_slot_filler_attr.parent_entity.id[0]
                    parent_entity = self.ring.get_entity_by_name(parent_slot_filler_attr.parent_entity.name)
                    filler_attr = parent_entity.attributes[filler_attr_name]
                else:
                    filler_attr_names = parent_slot_filler_attr.parent_entity.id
                    parent_entity = self.ring.get_entity_by_name(parent_slot_filler_attr.parent_entity.name)
                    filler_attr = tuple([parent_entity.attributes[filler_attr_name] for filler_attr_name in filler_attr_names])
            elif plan_slot.s_type == "CompositeIdentifier":
                parent_slot_filler_attr = self.get_attribute_for_value_slot(slot, spec)
                filler_attr_names = parent_slot_filler_attr.parent_entity.id
                parent_entity = self.ring.get_entity_by_name(parent_slot_filler_attr.parent_entity.name)
                filler_attr = tuple([parent_entity.attributes[filler_attr_name] for filler_attr_name in filler_attr_names])
            else:
                filler_attr = self.get_attribute_for_value_slot(slot, spec)

            # Sample values for that attribute
            return self.get_values_from_db(filler_attr, num_samples=n_id_attr_filler)

        elif plan_slot.s_type == "RelatedEntityClass":
            #  Get the input associated with this related entity {RelatedEntity[A]}
            input_ref = plan_slot.s_type_id

            # Get the attribute assigned to that input
            input_attr = spec.base_plan_inputs['|'+input_ref+'|']['ring_attribute']

            # Get the related entity
            if isinstance(input_attr, list):
                
                if input_attr[0].is_aggregated:
                    return [input_attr[0].aggregated_entity]
                else:
                    ent = input_attr[0].parent_entity
                    related_ents = self.get_related_ents(ent)
                    
                    constraints = spec.base_plan.get("related_ent_constraints", {})

                    if slot in constraints.keys():    
                        choices = [ent_info[0] for ent_info in related_ents if self.simplify_rel_type(ent_info[1]) in constraints[slot].split("|")]
                        # print([c[0].name for c in choices])
                        if not choices:
                            raise ValueError(f"No related entities found for entity {ent} satisfying the given constraints")
                        return [random.choice(choices)]
                    else:
                        if related_ents:
                            return [random.choice(related_ents)[0]]
                        else:
                            return [input_attr[0].parent_entity]
            else:
                if input_attr.is_aggregated:
                    return [input_attr.aggregated_entity]
                else:
                    ent = input_attr.parent_entity
                    related_ents = self.get_related_ents(ent)
                    
                    constraints = spec.base_plan.get("related_ent_constraints", {})

                    if slot in constraints.keys():
                        choices = [ent_info[0] for ent_info in related_ents if self.simplify_rel_type(ent_info[1]) in constraints[slot].split("|")]
                        if not choices:
                            raise ValueError(f"No related entities found for entity {ent} satisfying the given constraints")
                        return [random.choice(choices)]
                    else:
                        if related_ents:
                            return [random.choice(related_ents)[0]]
                        else:
                            return [input_attr.parent_entity]

        elif plan_slot.s_type == "EntityClass":
            #  Get the input associated with this entity class {EntityClass[A]}
            input_ref = plan_slot.s_type_id

            # Get the attribute assigned to that input
            input_attr = spec.base_plan_inputs['|'+input_ref+'|']['ring_attribute']

            # Get the parent entity
            return [input_attr.parent_entity]
        else:
            raise ValueError(f"Unhandled slot type: {slot}")

    def get_quantity_fillers(self,
                             n_quantity_filler: int = 1) -> List:
        """
        Produces values from an arbitrary list of values.
        :param n_quantity_filler: The total number of filler values to get.
        :type n_quantity_filler: int
        :return: A list of quantity filler values.
        :rtype: List
        """
        quantity_values = [1, 3, 5, 10, 100]
        return list(np.random.choice(quantity_values, size=n_quantity_filler, replace=True))

    def get_values_from_db(self,
                           attr: Union[RingAttribute, Tuple[RingAttribute]],
                           num_samples: int) -> List:
        """
        Retrieves distinct values of this attribute from the database.
        :param attr: The attribute to sample values for.
        :type attr: RingAttribute
        :return: A list of valid values for the given attribute.
        :rtype: List
        """

        distinct_attribute_values = self.cache_manager.get_distinct_attribute_values(attr)
        # Randomly sample the desired number of values
        # handle retrieving multiple vals to support composite ids
        sample_idxs = list(np.random.choice(len(distinct_attribute_values), size=num_samples, replace=True))
        return np.array(distinct_attribute_values)[sample_idxs].tolist()

    def get_attribute_for_value_slot(self,
                                     value_slot: str,
                                     spec: CompositionSpecification) -> RingAttribute:
        """
        Finds the attribute this value slot should derive its values from.
        :param value_slot: The value slot to find the parent for.
        :type value_slot: str
        :param spec: The composition spec this value slot is from.
        :type spec: CompositionSpecification
        :return: The RingAttribute corresponding to this value slot.
        :rtype: RingAttribute
        """

        # Get the non-value version of this slot
        non_value_slot = PlanSlot.from_string(value_slot)
        non_value_slot.value_dec = False
        non_value_slot.value_dec_id = None

        # Look up the attribute that was used to fill the non-value version of this slot
        if str(non_value_slot) in spec.input_fillers:
            return spec.input_fillers[str(non_value_slot)].attr
        elif str(non_value_slot) in spec.slot_fillers:
            return spec.slot_fillers[str(non_value_slot)]
        else:
            raise ValueError("Unhandled case for getting attribute associated with value slot.")

    def get_steps_associated_with_slot(self,
                                       target_slot: str,
                                       spec: CompositionSpecification) -> Dict:
        """
        Find the set of steps that contain the target slot.
        :param target_slot: The slot to find in the spec.
        :type target_slot: str
        :param spec: The specification to check.
        :type spec: CompositionSpecification
        :return: A dictionary mapping components of the spec (e.g. 'analysis_template', 'input_filters') to a list of step references (e.g. ['|1|', '|4|'] containing that target_slot.
        :rtype: Dict[str, List[str]]
        """

        # Find any steps with the target slot in the analysis template of the base plan in the spec
        analysis_template_steps_with_slot = []
        for step_ref, step in spec.base_plan['analysis_template'].items():
            slots_in_step = extract_slots(step)
            if slots_in_step and any([step_slot for step_slot in slots_in_step if step_slot == target_slot]):
                analysis_template_steps_with_slot.append(step_ref)

        # Find any steps with the target slot in the filters of the base plan in the spec
        input_filters_steps_with_slot = defaultdict(list)
        for input_label, input_info in spec.base_plan['input'].items():
            for step_ref, step in input_info['filter'].items():
                slots_in_step = extract_slots(step)
                if slots_in_step and any([step_slot for step_slot in slots_in_step if step_slot == target_slot]):
                    input_filters_steps_with_slot[input_label].append(step_ref)

        return {
            "analysis_template": analysis_template_steps_with_slot,
            "input_filters": input_filters_steps_with_slot
        }

    def find_entity_for_retrieve_attribute_step(self,
                                                step_ref: str,
                                                plan: Dict[str, AnalysisStep],
                                                spec: CompositionSpecification) -> RingEntity:

        if plan[step_ref].operation == 'retrieve_attribute':
            entity_arg = plan[step_ref].args[0]
            if is_arg_reference(entity_arg):
                # Recurse on this step ref
                return self.find_entity_for_retrieve_attribute_step(entity_arg, plan, spec)
            else:
                # We know we're retrieving the attribute from an entity, so get that entity from the ring, look up that attribute, and return it
                entity = self.ring.get_entity_by_name(plan[step_ref].args[0])
                return self.ring.get_entity_by_name(entity.name)
        elif plan[step_ref].operation == 'retrieve_entity':
            entity_arg = plan[step_ref].args[0]
            if is_slot(entity_arg):
                # Look it up in the slot fillers
                entity = spec.slot_fillers[entity_arg]
                return self.ring.get_entity_by_name(entity.name)
            else:
                raise ValueError("Unhandled case!")
        else:
            raise ValueError(f"Unhandled operation type when finding parent identifier attribute: {plan[step_ref].operation}")
