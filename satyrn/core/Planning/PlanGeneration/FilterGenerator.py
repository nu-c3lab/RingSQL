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
from typing import List, Dict, Union, Tuple
from contextlib import closing
from sqlalchemy.sql.expression import func

from satyrn.core.RingObjects.Ring import Ring
from satyrn.core.Operations.ArgType import ArgType
from satyrn.core.Planning.SQRComposer import SQRComposer
from satyrn.core.RingObjects.RingEntity import RingEntity
from satyrn.core.RingObjects.RingAttribute import RingAttribute
from satyrn.core.Analysis.OperationOntology import OperationOntology
from satyrn.core.Planning.CompositionSpecification import CompositionSpecification
from satyrn.core.Planning.PlanGeneration.PlanSlot import PlanSlot
from satyrn.core.Planning.PlanGeneration.SlotIdentifier import SlotIdentifier
from satyrn.core.Planning.utils import is_slot
from satyrn.core.Document.BasePlanStore import BasePlanStore
from satyrn.core.Planning.PlanGeneration.FillerIdentifier import FillerIdentifier
from satyrn.core.Planning.PlanGeneration.CacheManager import CacheManager
from satyrn.core.Planning.PlanGeneration.SlotExpressor import SlotExpressor
from satyrn.core.Planning.PlanGeneration.InputAssignment import InputAssignment
from satyrn.core.Planning.utils import extract_slots
from copy import deepcopy
import networkx as nx
import itertools

# TODO: refactor these into API call?
# USE_SUBQUERY_PROPORTION = 0.2
# FILTER_SUBQUERY_PROPORTION = 0.2
USE_SUBQUERY_PROPORTION = 0
FILTER_SUBQUERY_PROPORTION = 0

class FilterGenerator:
    """
    A class for generating useful and valid filters for a plan.
    """
    def __init__(self,
                 ring: Ring,
                 operation_ontology: OperationOntology,
                 cache_manager: CacheManager = None,
                 base_plan_store: BasePlanStore = None,
                 filler_identifier: FillerIdentifier = None,
                 slot_expressor: SlotExpressor = None):
        self.ring = ring
        self.operation_ontology = operation_ontology
        self.sqr_composer = SQRComposer(self.ring, self.operation_ontology)
        self.cache_manager = cache_manager if cache_manager else CacheManager(self.ring)
        self.identify_related_columns()
        # combine first and last name filters
        self.common_first_name_cols = ["fname", "firstname", "first_name", "f_name", "name_first"]
        self.common_last_name_cols = ["lname", "lastname", "last_name", "l_name", "name_last"]
        # self.base_plan_store.filter_templates contains bp style filter templates
        self.base_plan_store = base_plan_store if base_plan_store else BasePlanStore()
        self.filler_identifier = filler_identifier if filler_identifier else FillerIdentifier()
        self.slot_expressor = slot_expressor
        self.slot_identifier = SlotIdentifier()
        self.directly_related_attrs = self.get_directly_related_attrs(match_column_names=True)
        self.related_attr_graph = self.get_related_attr_graph()

    def get_directly_related_attrs(self, match_column_names):
        directly_related_attrs = []
        for join in self.ring.data_source.joins:
            fro_ent = [ent for ent in self.ring.entities if ent.primary_table == join.from_]
            to_ent = [ent for ent in self.ring.entities if ent.primary_table == join.to]
            if len(fro_ent) != 1 or len(to_ent) != 1:
                raise ValueError(f"Unable to find correct entity for join: {fro_ent}, {to_ent}")
            fro_ent = fro_ent[0]
            to_ent = to_ent[0]
            for path in join.path:
                # assumes unique names for attributes and unique attributes corrseponding to each column
                fro_attr = [attr for attr in fro_ent.attributes.values() if not attr.is_derived() and attr.source_table + "." + attr.source_columns[0] == path[0]]
                to_attr = [attr for attr in to_ent.attributes.values() if not attr.is_derived() and attr.source_table + "." + attr.source_columns[0] == path[1]]
                if len(fro_attr) != 1 or len(to_attr) != 1:
                    raise ValueError(f"Unable to find correct attribute for join: {fro_attr}, {to_attr}")
                fro_attr = fro_attr[0]
                to_attr = to_attr[0]
                directly_related_attrs.append([fro_attr, to_attr])
        if match_column_names:
            # consider attrs with same column names as directly related
            # assumes 1 column per attribute
            all_attrs = sum([[attr for attr in ent.attributes.values() if not attr.is_derived()] for ent in self.ring.entities], [])
            for attr1, attr2 in itertools.combinations(all_attrs, 2):
                if attr1.source_columns[0].lower() == attr2.source_columns[0].lower():
                    if [attr1, attr2] not in directly_related_attrs and [attr2, attr1] not in directly_related_attrs:
                        directly_related_attrs.append([attr1, attr2])
            
        return directly_related_attrs

    def get_related_attr_graph(self):
        graph = nx.Graph()
        for rel in self.directly_related_attrs:
            graph.add_edge(rel[0], rel[1])

        return graph

    def identify_related_columns(self):
        self.related_columns = {}
        for r in self.ring.data_source.joins:
            ons = r.path
            for cond in ons:
                c1 = cond[0]
                c2 = cond[1]
                if c1 in self.related_columns:
                    self.related_columns[c1].append(c2)
                else:
                    self.related_columns[c1] = [c2]
                if c2 in self.related_columns:
                    self.related_columns[c2].append(c1)
                else:
                    self.related_columns[c2] = [c1]

    def generate_spec_input_filters(self,
                                    spec: CompositionSpecification,
                                    sample_filter=True) -> List[Dict]:
        """
        Generates the SQR filters that can be added to the given composition specification.
        :param spec: The composition specification that contains an input that will be filtered.
        :type spec: CompositionSpecification
        :param sample_filter: Whether or not to generate a non-required filter
        :type sample_filter: bool
        :return: The filter steps that were produced.
        :rtype: List[Dict]
        """

        # TODO: This currently only generates a filter for ONE of the spec's inputs.
        
        required_options = [k for k, v in spec.base_plan["input"].items() if v.get("require_filter", False)]

        if spec.base_plan["input"] and sample_filter:
            sample_options = list(set(spec.base_plan["input"].keys()) - set(required_options))
            random.shuffle(sample_options)
        else:
            sample_options = []
        
        filters = []

        generated_filter = {}
        for input_to_filter in sample_options:
            try:
                filt, filter_expression = self.build_filter_for_base_plan_input(spec.base_plan, input_to_filter, spec)
                generated_filter = {
                    "input_to_filter": input_to_filter,
                    "filter": filt,
                    "expression": filter_expression,
                }
            except Exception as e:
                import traceback
                print(e)
                print(traceback.format_exc())
                continue

        # If it's not possible to generate a filter for any of the inputs, return the empty list
            # Store the filter that was generated for this input
            filters.append(generated_filter)

            # Add this filter to any inputs that are symmetric with the input that had a filter added to it
            for symmetric_input in spec.base_plan["input"][generated_filter["input_to_filter"]]["symmetric_filter_with"]:
                filters.append({
                    "input_to_filter": symmetric_input,
                    "filter": generated_filter["filter"],
                    "expression": generated_filter["expression"],
                })
            break

        # attempt to generate all required filters
        for input_to_filter in required_options:
            if input_to_filter in map(lambda f: f["input_to_filter"], filters):
                # skip duplicate filter creation
                continue
            try:
                filt, filter_expression = self.build_filter_for_base_plan_input(spec.base_plan, input_to_filter, spec)
                generated_filter = {
                    "input_to_filter": input_to_filter,
                    "filter": filt,
                    "expression": filter_expression,
                }
            except Exception as e:
                import traceback
                print(e)
                print(traceback.format_exc())
                raise ValueError("Could not generate a required filter")
                # continue

        # If it's not possible to generate a filter for any of the inputs, return the empty list
            if not generated_filter:
                continue

            # Store the filter that was generated for this input
            filters.append(generated_filter)

            # Add this filter to any inputs that are symmetric with the input that had a filter added to it
            for symmetric_input in spec.base_plan["input"][generated_filter["input_to_filter"]]["symmetric_filter_with"]:
                filters.append({
                    "input_to_filter": symmetric_input,
                    "filter": generated_filter["filter"],
                    "expression": generated_filter["expression"],
                })

        return filters

    def get_entity_associated_with_input(self,
                                         input_to_filter: str,
                                         spec: CompositionSpecification) -> RingEntity:
        """
        Determines which ring entity is associated with the given input of the base plan in the spec.
        :param input_to_filter: The name of the input in the base plan of the spec.
        :type input_to_filter: str
        :param spec: The composition specification whose input will be examined.
        :type spec: CompositionSpecification
        :return: The ring entity associated with a particular input slot assignment.
        :rtype: RingEntity
        """
        for slot, assignment_info in spec.input_fillers.items():
            if input_to_filter in assignment_info.inputs:
                if isinstance(assignment_info.attr, list):
                    return assignment_info.attr[0].parent_entity
                else:
                    return assignment_info.attr.parent_entity

        raise ValueError("No entity found for associated input.")

    def get_filter_template_assignments_for_attribute(self, attr):
        available_templates = []
        for filter_name, filter_template in self.base_plan_store.filter_templates.items():
            assignment = {}
            filter_attr_types = filter_template["filter_attr_types"]
            filter_attr_slots = filter_template["filter_attrs"]
            # assumes first slot is always for attr
            if ArgType.from_str(filter_template["filter_attr_types"][0]) in attr.type:
                assignment[filter_attr_slots[0]] = attr
            else:
                continue
            # TODO: handle other types of slots? aside from related attribute
            # may want to create a seperate key in dict for this? (to allow specifying types if needed?)
            # TODO: assumes single column attr and single column joins
            legal_assignment = True
            for attr_typ, attr_slot in zip(filter_attr_types[1:], filter_attr_slots[1:]):
                if attr_typ == "RelatedAttribute":
                    try:
                        related_attributes = list(self.related_attr_graph[attr])
                        if related_attributes:
                            related_attr = random.choice(related_attributes)
                            assignment[attr_slot] = related_attr
                            # also need to assign a slot for the corresponding related entity
                            parent_ent_slot = PlanSlot.from_string(attr_slot)
                            parent_ent_slot.s_type = "RelatedEntity"
                            assignment[str(parent_ent_slot)] = related_attr.parent_entity

                        else:
                            legal_assignment = False
                            break
                    except:
                        legal_assignment = False
                        break
                else:
                    plan_slot = PlanSlot.from_string(attr_slot)
                    slot_type = ArgType.from_str(plan_slot.s_type)
                    # ignore derived attributes
                    attributes = [a2 for a2 in attr.parent_entity.get_attributes_with_type(slot_type) if not a2.is_derived()]
                    if not attributes:
                        legal_assignment = False
                        break
                    else:
                        assignment[attr_slot] = random.choice(attributes)
                    
            if legal_assignment:
                available_templates.append((filter_name, filter_template, assignment))
        return available_templates
            

    def build_filter_from_template(self, 
                                   attr: RingAttribute,
                                   subquery_filter_prop: float=FILTER_SUBQUERY_PROPORTION,
                                   )-> Tuple[Dict, str]:
        # fills in filter template for a given attribute
        # TODO: for in filters, need to id related cols? (same name or joinable?)
        # filter template should have 2 things:
        #   - the subqeury for the filter (optionally with an additional filter?)
        #   - template for the attribute??
        #   - how to handle the order by?

        available_templates_with_assignments = self.get_filter_template_assignments_for_attribute(attr)
        if not available_templates_with_assignments:
            return {}, None, None
        template_sample_weights = [template_info[1]["sample_proportion"] for template_info in available_templates_with_assignments]
        total_weights = sum(template_sample_weights)
        template_sample_weights = [w / total_weights for w in template_sample_weights]
        filter_template_name, filter_template, slots_to_vals = deepcopy(random.choices(available_templates_with_assignments, weights=template_sample_weights, k=1)[0])
        subquery = filter_template["subquery"]

        slots_to_vals["{parent_ent}"] = attr.parent_entity

        sq_slots = self.slot_identifier.identify_slots_in_sqr_dict(subquery)
        
        for slot in sq_slots:
            if slot not in slots_to_vals.keys():
                slots_to_vals[slot] = random.choice(self.filler_identifier.identify_filler(slot, None))

        spec_input_fillers = {slot: InputAssignment(val) for slot, val in slots_to_vals.items()}

        subquery = self.sqr_composer.plan_parser.create_analysis_steps(subquery)
        subquery = self.sqr_composer.plan_filler.fill_plan(subquery, slots_to_vals)
        filled_subquery = subquery
        if random.random() < subquery_filter_prop:
            # TODO: may want to disallow use of attr in this filter?
            if "{RelatedEntity[0]}" in slots_to_vals:
                subquery_filter, subquery_filter_expression = self.build_filter_with_entity(slots_to_vals["{RelatedEntity[0]}"], filter_by_subquery_val_prop=0, subquery_filter_prop=0)
            else:
                subquery_filter, subquery_filter_expression = self.build_filter_with_entity(slots_to_vals["{parent_ent}"], filter_by_subquery_val_prop=0, subquery_filter_prop=0)
            subquery_filter = self.sqr_composer.plan_parser.create_analysis_steps(subquery_filter)
            subquery = self.sqr_composer.compose_filter_and_access_plan(subquery, subquery_filter)
        else:
            subquery_filter = {}
            subquery_filter_expression = ""
        
        analysis_template = filter_template["analysis_template"]
        analysis_slots = self.slot_identifier.identify_slots_in_sqr_dict(analysis_template)

        for slot in analysis_slots:
            if slot not in slots_to_vals.keys():
                slots_to_vals[slot] = random.choice(self.filler_identifier.identify_filler(slot, None))

        analysis = self.sqr_composer.plan_parser.create_analysis_steps(analysis_template)
        analysis = self.sqr_composer.plan_filler.fill_plan(analysis, slots_to_vals)

        # join the subqeury and analysis while filling in the first step of analysis plan
        final_plan, _ = self.sqr_composer.compose_access_plans_and_base_plan(analysis, {"|subquery|": subquery})

        leaves = self.sqr_composer.plan_parser.get_leaves(self.sqr_composer.plan_parser.create_plan_graph(final_plan))
        if len(leaves) != 1:
            raise ValueError(f"Subqeury plan has mutliple leaves: {leaves}\nPlan: {final_plan}")

        # use filter language template
        language_templates = filter_template["question_templates"]
        # TODO: randomly sample for more variation
        language_template = language_templates[0]

        # replace subquery filter ref?
        if subquery_filter_expression:
            # add for before the raw subquery filter expression
            language_template = language_template.replace("{Filter[subquery].Expression}", "for " + subquery_filter_expression)


        # special handling for CategoryOrderedByAggregatedMetric plan sort order
        # TODO: find a more general fix for this?
        if filter_template_name == "CategoryOrderedByAggregatedMetric":
            language_template = language_template.replace("{Direction[0].Expression}", "highest" if slots_to_vals["{Direction[0]}"] == "desc" else "lowest")
        elif filter_template_name == "CategoryOrderedByCountAll":
            language_template = language_template.replace("{Direction[0].Expression}", "most common" if slots_to_vals["{Direction[0]}"] == "desc" else "least common")

        language_template_slots = {}
        for slot in extract_slots(language_template):
                    language_template_slots[slot] = []

        tmp_spec = CompositionSpecification(filter_template_name,
                                            {},
                                            base_plan_inputs={"|subquery|": {"access_plan": filled_subquery, "access_plan_filters": {"filters": [subquery_filter] if subquery_filter else [], "filter_joiner": None}}},
                                            slot_fillers=slots_to_vals,
                                            input_fillers=spec_input_fillers,
                                            )

        language_fillers = {}
        for slot in language_template_slots:
            plan_slot = PlanSlot.from_string(slot)
            language_fillers[str(plan_slot)] = self.slot_expressor.get_slot_expression(plan_slot, tmp_spec)

        filled_language_template = language_template
        for slot, val in language_fillers.items():
            filled_language_template = filled_language_template.replace(slot, val)
        

        return {step_num: str(step) for step_num, step in final_plan.items()}, leaves[0], filled_language_template
        

    def build_simple_filter_for_attribute(self,
                                          attr: RingAttribute,
                                          filter_by_subquery_val_prop: float = USE_SUBQUERY_PROPORTION,
                                          subquery_filter_prop: float = FILTER_SUBQUERY_PROPORTION) -> Tuple[Dict, str]:
        """
        Builds a simple filter consisting of a single filter without any boolean connectors.
        :param attr: The entity whose attributes will be filtered on.
        :type attr: RingAttribute
        :param filter_by_subquery_val_prop: The probability of using a filter subquery template
        :type filter_by_subqeury_val_prop: float
        :param subquery_filter_prop: The probability of using an additional filter inside the filter subquery
        :type subquery_filter_prop: float
        :return: The steps of a simple SQR filter.
        :rtype: Dict
        """
        
        # randomly sample if a filter template should be used
        if random.random() < filter_by_subquery_val_prop:
            try:
                filter_sqr, return_ref, expression = self.build_filter_from_template(attr, subquery_filter_prop)
                if return_ref:
                    return filter_sqr, return_ref, expression
                else:
                    print(f"UNABLE TO FILL A FILTER TEMPLATE FOR ATTR: {attr}")
            except Exception as e:
                print("ERROR BUILDING FILTER FROM TEMPLATE")
                import traceback
                print(traceback.format_exc())
                print(e)

        # Get a random valid filter operation
        filter_operation = self.get_filter_operation(attr)
        
        if filter_operation == "exact" and attr.base_isa == "string" and len(attr.source_columns) == 1:
                # only do for attrs with a single source col?
                is_first_name = any(cn in attr.source_columns[0].lower() for cn in self.common_first_name_cols)
                is_last_name = not is_first_name and any(cn in attr.source_columns[0].lower() for cn in self.common_last_name_cols)
                if is_first_name or is_last_name:
                    other_attrs = [attr2 for attr_name, attr2 in attr.parent_entity.attributes.items() if attr2.base_isa == "string" and len(attr2.source_columns) == 1]
                    first_name_attr = None
                    last_name_attr = None
                    if is_first_name:
                        # find corresponding last name column
                        last_name_attrs = [attr2 for attr2 in other_attrs if any(cn in attr2.source_columns[0].lower() for cn in self.common_last_name_cols)]
                        # skip ambigous last name col
                        if len(last_name_attrs) == 1:
                            first_name_attr = attr
                            last_name_attr = last_name_attrs[0]
                    elif is_last_name:
                        first_name_attrs = [attr2 for attr2 in other_attrs if any(cn in attr2.source_columns[0].lower() for cn in self.common_first_name_cols)]
                        # skip ambigous first name col
                        if len(first_name_attrs) == 1:
                            first_name_attr = first_name_attrs[0]
                            last_name_attr = attr
                    if first_name_attr and last_name_attr:
                        vals = random.choice(self.cache_manager.get_distinct_attribute_values((first_name_attr, last_name_attr)))
                        if ' ' in vals[0] or "'" in vals[0]:
                            vals[0] = f"\"{vals[0]}\""
                        if ' ' in vals[1] or "'" in vals[1]:
                            vals[1] = f"\"{vals[1]}\""
                        filter_steps = {
                            "|1|": f"(retrieve_entity {first_name_attr.parent_entity.name})",
                            "|2|": f"(retrieve_attribute |1| {first_name_attr.name})",
                            "|3|": f"(retrieve_attribute |1| {last_name_attr.name})",
                            "|4|": f"(exact |2| {vals[0]})",
                            "|5|": f"(exact |3| {vals[1]})",
                            "|6|": "(and |4| |5|)",
                        }
                        # TODO: sample this language??
                        return filter_steps, "|6|", f"named {vals[0]} {vals[1]}"

        # Get a random valid value for this attribute
        filter_value = self.get_filter_value(attr, filter_operation)

        # Generate the filter steps
        filter_steps, terminal_ref = self.get_steps(filter_operation, attr, filter_value)

        return filter_steps, terminal_ref, self.slot_expressor.step_expressor.express_filter_step(terminal_ref, self.sqr_composer.plan_parser.create_analysis_steps(filter_steps))

    def get_steps(self,
                  filter_operation: str,
                  filter_attribute: RingAttribute,
                  filter_value) -> Tuple[Dict[str, str], str]:

        # Handle cases where there are spaces or apostrophes in the filter value
        if isinstance(filter_value, dict):
            filter_steps = filter_value
            step_3 = f"({filter_operation} |{len(filter_steps.keys()) + 2}| |{len(filter_steps.keys())}|)"
        else:
            if not isinstance(filter_value, tuple):
                filter_value = tuple([filter_value])
            step_3 = f"({filter_operation} |2|"
            for val in filter_value:
                filter_value_str = str(val)
                if ' ' in filter_value_str or "'" in filter_value_str:
                    step_3 += f" \"{val}\""
                else:
                    step_3 += f" {val}"
            step_3 += ")"
            filter_steps = {}

        filter_steps[f"|{len(filter_steps.keys()) + 1}|"] = f"(retrieve_entity {filter_attribute.parent_entity.name})"
        filter_steps[f"|{len(filter_steps.keys()) + 1}|"] = f"(retrieve_attribute |{len(filter_steps.keys())}| {filter_attribute.name})"
        filter_steps[f"|{len(filter_steps.keys()) + 1}|"] = step_3
        terminal_ref = f"|{len(filter_steps.keys())}|"

        return filter_steps, terminal_ref

    def get_filter_operation(self,
                             attr: RingAttribute) -> str:
        if attr.base_isa == "string":
            possible_operations = ["contains", "startswith", "endswith", "exact"]
        elif ArgType.Categorical in attr.type:
            possible_operations = ["exact"]
        else:
            possible_operations = ["exact", "greaterthan", "greaterthan_eq", "lessthan", "lessthan_eq", "between"]

        return random.choice(possible_operations)

    def get_filter_value(self,
                         attr: RingAttribute,
                         filter_operation: str) -> Union[str, float, int, Tuple[str], Tuple[float], Tuple[int]]:
        # handle choosing a substring if op is like
        value = random.choice(self.cache_manager.get_distinct_attribute_values(attr))
        if filter_operation == "between":
            value2 = random.choice(self.cache_manager.get_distinct_attribute_values(attr))
            return (value, value2) if value2 > value else (value2, value)
        # handle string vals - can't select only a space or sequence of spaces
        # will use 'a' a col only has empty strings or strings of spaces
        elif filter_operation in ["like", "contains", "startswith", "endswith", "exact"]:
            val = ''
            tries = 0
            # need to strip "() " since AnalysisPlanParser strips "()" and AnalysisStep strips " "
            while(not str(val).strip("() ") and tries < 5):
                if filter_operation == "exact":
                    val = value
                elif filter_operation in ["like", "contains"]:
                    start_idx = random.randint(0, len(value) - 1)
                    end_idx = random.randint(start_idx + 1, len(value))
                    val = value[start_idx: end_idx]
                elif filter_operation == "startswith":
                    end_idx = random.randint(1, len(value))
                    val = value[:end_idx]
                elif filter_operation == "endswith":
                    start_idx = random.randint(0, len(value) - 1)
                    val = value[start_idx:]
                value = random.choice(self.cache_manager.get_distinct_attribute_values(attr))
                tries += 1
            
            if not str(val).strip("() "):
                print(f"WARNING: A valid substring could not be sampled from attribute {attr.name}. Using the default 'a'")
                val = 'a'
            return val
        else:
            return value

    def contains_instance_filter(self,
                                 steps: Dict[str, str]) -> bool:
        """
        Check if the given series of templated SQR steps contains an instance filter.
        An instance filter is any filter that contains an "exact" filter on the Identifier attribute of an entity.
        :param steps: The templated steps to check.
        :type steps: Dict[str, str]
        :return: True or False depending on if the given steps contains an instance filter of not.
        :rtype: bool
        """
        analysis_steps = self.sqr_composer.plan_parser.create_analysis_steps(steps)

        for step_ref, step in analysis_steps.items():
            if step.operation in "exact" and is_slot(step.args[1]):
                # Parse the slot and check if the exact operation is looking at an Identifier[].Value[] slot
                # This indicates that these steps contains an instance filter
                slot = PlanSlot.from_string(step.args[1])
                if slot.s_type == "Identifier" and slot.value_dec:
                    return True
        return False

    def build_filter_for_base_plan_input(self,
                                         base_plan: Dict,
                                         input_to_filter: str,
                                         spec: CompositionSpecification,
                                         min_atomic_filters: int = 1,
                                         max_atomic_filters: int = 1, # set to 1 to avoid multiple subquery filters
                                         ) -> Dict:
        """
        Generate a random SQR filter for the chosen input of the base plan.
        :param base_plan: The full base plan entry from the json file.
        :type base_plan: Dict
        :param input_to_filter: The reference to the input to add the generated filter to.
        :type input_to_filter: basestring
        :param spec: The composition specification that contains an input that will be filtered.
        :type spec: CompositionSpecification
        :param min_atomic_filters: The minimum number of atomic filters to include in the generated filter.
        :type min_atomic_filters: int
        :param max_atomic_filters: The maximum number of atomic filters to include in the generated filter.
        :type max_atomic_filters: int
        :return: A dictionary containing the raw filter steps.
        :rtype: Dict
        """

        # TODO: Consider not allowing filters to be added onto attributes that have already been filtered on in the input of the base plan
        if min_atomic_filters > max_atomic_filters:
            raise ValueError("The minimum number of atomic filters is smaller than the maximum number of atomic filters.")

        # Determine which attributes can be used when building a new filter
        available_attributes = []
        if self.contains_instance_filter(base_plan["input"][input_to_filter]['filter']):
            # For instance filters, it may make make sense to filter on the attributes of the entity that was aggregated
            if spec.base_plan_inputs[input_to_filter]['ring_attribute'].is_derived():
                # If the attribute assigned to this base plan input is a derived attribute, then get the non-derived, non-Identifier attributes of the related entity and make these available for filtering
                related_ent = spec.base_plan_inputs[input_to_filter]['ring_attribute'].aggregated_entity
                available_attributes = self.get_attributes_of_related_ent_for_filtering(related_ent)
        else:
            ent_slot_for_filter = spec.base_plan["input"][input_to_filter].get("filter_ents", [])
            if ent_slot_for_filter:
                # TODO: allow creating multiple filters on multiple different ents?
                entity_to_filter = spec.slot_fillers[ent_slot_for_filter[0]]
            else:
                entity_to_filter = self.get_entity_associated_with_input(input_to_filter, spec)
            available_attributes = self.get_available_attributes_for_filtering(entity_to_filter)

            # Add attributes of the related entity, if it makes sense to
            if isinstance(spec.base_plan_inputs[input_to_filter]['ring_attribute'], list):
                if spec.base_plan_inputs[input_to_filter]['ring_attribute'][0].is_derived():
                    related_ent = spec.base_plan_inputs[input_to_filter]['ring_attribute'][0].aggregated_entity
                    available_attributes += self.get_attributes_of_related_ent_for_filtering(related_ent)
            else:
                if spec.base_plan_inputs[input_to_filter]['ring_attribute'].is_derived():
                    related_ent = spec.base_plan_inputs[input_to_filter]['ring_attribute'].aggregated_entity
                    available_attributes += self.get_attributes_of_related_ent_for_filtering(related_ent)

        if len(available_attributes) < 1:
            raise ValueError("No attributes available to filter on.")

        # TODO: Remove any attributes that are already being used as filters in the input
        
        # filters out all atts with filled values in the plan - may filter out too many things
        # available_attributes = list(filter(lambda x: x not in set(spec.slot_fillers.values()), available_attributes))

        # removes all atts with values already assigned - seems to work correctly
        # still allows filtering on other values that may cause certain plans 
        # like InstanceMetricValue to have empty results depending on sampled vals
        # now also prevents filtering with different value on join related cols
        atts_with_sampled_vals = []
        filled_slot_cols = []
        for slot, val in spec.slot_fillers.items():
            if "Value" in slot:
                att_slot = slot.split(".Value")[0] + "}"
                atts_with_sampled_vals.append(spec.slot_fillers[att_slot])
                att = spec.slot_fillers[att_slot]
                filled_slot_cols.extend([".".join([att.source_table, source_col]) for source_col in att.source_columns])

        revised_available_attributes = []
        for att in available_attributes:
            if att in atts_with_sampled_vals:
                continue
            att_filled = False
            att_cols = [".".join([att.source_table, source_col]) for source_col in att.source_columns]
            for col in att_cols:
                for related_col in self.related_columns.get(col, []):
                    if related_col in filled_slot_cols:
                        att_filled = True
                        break
            if not att_filled:
                revised_available_attributes.append(att)

        available_attributes = revised_available_attributes

        if len(available_attributes) < 1:
            raise ValueError("No attributes available to filter on.")


        # Pick the number of atomic filters to add to the final filter
        min_atomic_filters = max(min_atomic_filters, 1)                      # Make sure the min number of atomic filters is at least 1
        max_atomic_filters = max(max_atomic_filters, min_atomic_filters)     # Make sure the max number of atomic filters is at least the min

        num_atomic_filters = random.randint(min_atomic_filters, max_atomic_filters)

        # Randomly pick the number of conjuncts between 1 and the number of atomic filters, and make sure its less than or equal to the total number of available attributes
        num_conjuncts = random.randint(min_atomic_filters, num_atomic_filters)
        num_conjuncts = min(num_conjuncts, len(available_attributes))

        # Build each of the conjuncts as a set of disjunctive filters (i.e. atomic filters joined with an OR operation)
        conjuncts_with_terminal_refs = []
        conjunct_size_assignments = self.determine_atomic_filters_per_conjunct(num_atomic_filters, num_conjuncts)
        random.shuffle(available_attributes)
        for num_atomic_filters_in_conjunct in conjunct_size_assignments:
            # Pick an attribute without replacement from the list of available_attributes
            filtering_attr = available_attributes.pop(0)

            # Build the conjunct (i.e. the disjunction)
            conjuncts_with_terminal_refs.append(self.build_disjunction(filtering_attr, num_atomic_filters_in_conjunct))

        # Join the conjuncts together with an "AND" statement to construct the final set of filter steps
        filter_steps, terminal_ref, filter_expression = self.join_filters(conjuncts_with_terminal_refs, "and")

        return filter_steps, filter_expression

    def build_filter_with_entity(self,
                                 ent: RingEntity,
                                 min_atomic_filters: int = 1,
                                 max_atomic_filters: int = 2,
                                 allow_ids: bool = True,
                                 filter_by_subquery_val_prop: float = USE_SUBQUERY_PROPORTION,
                                 subquery_filter_prop: float = FILTER_SUBQUERY_PROPORTION) -> Dict:
        """
        Creates a random SQR filter for an entity.
        :param attr: The ring entity that will be used to determine which attributes can be used as part of the filter.
        :type attr: RingEntity
        :param min_atomic_filters: The minimum number of atomic filters to include in the generated filter.
        :type min_atomic_filters: int
        :param max_atomic_filters: The maximum number of atomic filters to include in the generated filter.
        :type max_atomic_filters: int
        :param allow_ids: Whether or not to allow generating filters on id attributes
        :type allow_ids: bool
        :param filter_by_subquery_val_prop: The probability of using a filter subquery template
        :type filter_by_subquery_val_prop: float
        :param subquery_filter_prop: The probability of using an additional filter inside the filter subquery
        :type subquery_filter_prop: float
        :return: A dictionary containing the raw filter steps.
        :rtype: Dict
        """

        if min_atomic_filters > max_atomic_filters:
            raise ValueError("The minimum number of atomic filters is smaller than the maximum number of atomic filters.")

        # Get the attributes that are available for filtering based on the current attribute
        available_attributes = self.get_available_attributes_for_filtering(ent, allow_ids=allow_ids)          # TODO: Don't allow filters to be added onto attributes that have already been filtered on in the input of the base plan (this will require either a new function or for the composition spec to be added as input to this function)

        # Pick the number of atomic filters to add to the final filter
        min_atomic_filters = max(min_atomic_filters, 1)                      # Make sure the min number of atomic filters is at least 1
        max_atomic_filters = max(max_atomic_filters, min_atomic_filters)     # Make sure the max number of atomic filters is at least the min

        num_atomic_filters = random.randint(min_atomic_filters, max_atomic_filters)

        # Randomly pick the number of conjuncts between 1 and the number of atomic filters, and make sure its less than or equal to the total number of available attributes
        num_conjuncts = random.randint(min_atomic_filters, num_atomic_filters)
        num_conjuncts = min(num_conjuncts, len(available_attributes))

        # Build each of the conjuncts as a set of disjunctive filters (i.e. atomic filters joined with an OR operation)
        conjuncts_with_terminal_refs = []
        conjunct_size_assignments = self.determine_atomic_filters_per_conjunct(num_atomic_filters, num_conjuncts)
        random.shuffle(available_attributes)
        for num_atomic_filters_in_conjunct in conjunct_size_assignments:
            # Pick an attribute without replacement from the list of available_attributes
            filtering_attr = available_attributes.pop(0)

            # Build the conjunct (i.e. the disjunction)
            conjuncts_with_terminal_refs.append(self.build_disjunction(filtering_attr, num_atomic_filters_in_conjunct, filter_by_subquery_val_prop=filter_by_subquery_val_prop, subquery_filter_prop=subquery_filter_prop))

        # Join the conjuncts together with an "AND" statement to construct the final set of filter steps
        filter_steps, terminal_ref, filter_expression = self.join_filters(conjuncts_with_terminal_refs, "and")

        return filter_steps, filter_expression

    def determine_atomic_filters_per_conjunct(self,
                                              n_atomic_filters: int,
                                              n_conjuncts: int) -> List[int]:
        """
        Creates a list containing the number of atomic filters that should be included in each conjunct.
        :param n_atomic_filters: The total number of atomic filters to allocate.
        :type n_atomic_filters: int
        :param n_conjuncts: The total number of conjuncts.
        :type n_conjuncts: int
        :return: A list whose elements are the number of atomic filters to include in the conjunct at that index of the list.
        :rtype: List of int
        """

        if n_atomic_filters < n_conjuncts:
            raise ValueError("Not enough atomic filters to assign at least one to each conjunct.")

        # Assign one atomic filter to each conjunct
        conjunct_size_assignments = [1] * n_conjuncts
        n_atomic_filters -= n_conjuncts

        # Assign the remaining number of atomic filters to a random index until there are none left
        while n_atomic_filters > 0:
            idx = random.randrange(0, n_conjuncts)
            conjunct_size_assignments[idx] += 1
            n_atomic_filters -= 1

        return conjunct_size_assignments

    def get_available_attributes_for_filtering(self,
                                               ent: RingEntity, allow_ids: bool=True) -> List[RingAttribute]:
        """
        Determines the RingAttributes that can be used as part of a filter.
        :param attr: The entity whose attributes will be examined.
        :type attr: RingEntity
        :return: The list of ring attributes.
        :rtype: List[RingAttribute]
        """

        # TODO: look at the aggregated_entity if attr.is_aggregated
        if allow_ids:
            available_attributes = [a for a in ent.attributes.values() if not a.is_derived() and ArgType.Document not in a.type]
        else:
            available_attributes = [a for a in ent.attributes.values() if not a.is_derived() and ArgType.Document not in a.type and a.name not in ent.id]

        return available_attributes

    def get_attributes_of_related_ent_for_filtering(self,
                                                    related_ent: RingEntity) -> List[RingAttribute]:
        """
        Determines the RingAttributes that can be used as part of a filter for an entity related to another entity.
        :param related_ent: The related entity of the other entity in consideration.
        :type related_ent: RingEntity
        :return: The list of ring attributes.
        :rtype: List[RingAttribute]
        """
        available_attributes = [a for a in related_ent.attributes.values() if not a.is_derived()
                                 and ArgType.Identifier not in a.type
                                 and ArgType.RelatedIdentifier not in a.type]
        return available_attributes

    def build_disjunction(self,
                          attr: RingAttribute,
                          num_atomic_filters: int,
                          negation_prob:float=0.0,
                          filter_by_subquery_val_prop: float = USE_SUBQUERY_PROPORTION,
                          subquery_filter_prop: float = FILTER_SUBQUERY_PROPORTION) -> Tuple[Dict, str]:
        """
        Creates a set of filtering steps joined with an OR operation.
        :param attr: The ring attributes whose parent entity will be used to determine what other attributes can be filtered on.
        :type attr: RingAttribute
        :param num_atomic_filters: The total number of atomic filters to include in the disjunction.
        :type num_atomic_filters: int
        :param negation_prob: The probability of negating the disjunction
        :type negation_prob: float
        :param filter_by_subquery_val_prop: The probability of using a filter subquery template
        :type filter_by_subquery_val_prop: float
        :param subquery_filter_prop: The probability of using an additional filter inside the filter subquery
        :type subquery_filter_prop: float
        :return: Tuple containing the raw steps for the disjunction and the reference of the final step (i.e. the OR step)
        :rtype: Tuple[Dict, str]
        """

        filters_with_terminal_refs = []
        for i in range(num_atomic_filters):
            # Build a simple filter on this attribute
            filter_steps, terminal_ref, expression = self.build_simple_filter_for_attribute(attr, filter_by_subquery_val_prop=filter_by_subquery_val_prop, subquery_filter_prop=subquery_filter_prop)
            
            # Parse each of these into a dictionary of AnalysisStep objects
            filter_plan_steps = self.sqr_composer.plan_parser.create_analysis_steps(filter_steps)
            
            # Use the SQRComposer to append letters to these steps and the terminal ref
            ref_letter = self.sqr_composer.get_next_ref_letter()
            filter_plan_steps = self.sqr_composer.append_to_plan_refs(filter_plan_steps, ref_letter)
            terminal_ref = terminal_ref[0:-1] + ref_letter + terminal_ref[-1]

            # Save the generated filter
            filters_with_terminal_refs.append((filter_plan_steps, terminal_ref, expression))

        disjunction, terminal_step_ref, filter_expression = self.join_filters(filters_with_terminal_refs, "or")
        
        # not currently used
        negate = random.choices([0, 1], weights=[1 - negation_prob, negation_prob], k=1)[0]
        
        if negate:
            negate_ref_letter = terminal_step_ref.strip("|").strip("0123456789")
            negate_step = int(terminal_step_ref.strip("|").replace(negate_ref_letter, "")) + 1
            negate_step_ref = f"|{negate_step}{negate_ref_letter}|"
            disjunction[negate_step_ref] = f"(not {terminal_step_ref})"
            terminal_step_ref = negate_step_ref

        # Convert the steps back to strings
        disjunction = {k: str(v) for k, v in disjunction.items()}

        return disjunction, terminal_step_ref, filter_expression

    def join_filters(self,
                     filters_with_terminal_refs: List[Tuple[Dict, str]],
                     joiner_type: str) -> Tuple[Dict, str]:
        """
        Creates a filter that is a combination of the given filters joined together with an AND or OR operation.
        :param filters_with_terminal_refs: The list of filters and their terminal step references that will be joined together.
        :type filters_with_terminal_refs: List[Tuple[Dict, str]]
        :param joiner_type: Either "and" or "or"
        :type joiner_type: str
        :return: A tuple containing the filter steps and the reference of the terminal step
        :rtype: Tuple[Dict, str]
        """

        # Handle the base case where there is only one filter to join
        if len(filters_with_terminal_refs) == 1:
            return filters_with_terminal_refs[0]

        final_filter = {}
        for f in filters_with_terminal_refs:
            # Add the filter steps to the disjunction
            final_filter.update(f[0])

        # Create an AND or OR operation with args that are all the references for these terminal steps
        joiner_step_ref = "|" + str(len(final_filter) + 1) + self.sqr_composer.get_next_ref_letter() + "|"
        final_filter[joiner_step_ref] = f"({joiner_type} " + " ".join([f[1] for f in filters_with_terminal_refs]) + ")"

        # TODO: use language template for filter op, not just its name (although should be the same for and/or)
        final_expression = f" {joiner_type} ".join([filter_info[2] for filter_info in filters_with_terminal_refs])

        return final_filter, joiner_step_ref, final_expression
