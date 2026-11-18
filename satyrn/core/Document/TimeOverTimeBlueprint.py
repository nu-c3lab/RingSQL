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

from satyrn.core.RingObjects.Ring import Ring
from satyrn.core.Document.DocumentBlueprint import DocumentBlueprint
from satyrn.core.Planning.CompositionSpecification import CompositionSpecification

class TimeOverTimeBlueprint(DocumentBlueprint):
    def __init__(self,
                 entity_name: str,
                 entity_instance_identifier_attribute_name: str,
                 entity_instance_identifier_value: str,
                 entity_reference: str,
                 metric_entity_name: str,
                 metric_attribute_name: str,
                 metric_aggregation: str,
                 set_filter: Dict[str, str],
                 metric_preference_direction: str,
                 ring: Ring,
                 time_attribute_name,
                 time_zero,
                 time_one):
        super().__init__(entity_name, entity_instance_identifier_attribute_name, entity_instance_identifier_value, entity_reference, metric_entity_name, metric_attribute_name, metric_aggregation, set_filter, metric_preference_direction, ring)


        self.time_attribute_name = time_attribute_name
        self.time_zero = time_zero
        self.time_one = time_one

        self.entity_group = self.ring.get_entity_by_name(self.entity_name).nicename[1]

        self.time_zero_filter = self.get_time_filter(self.time_zero)
        self.time_one_filter = self.get_time_filter(self.time_one)

    def get_time_filter(self,
                        time_value: str) -> Dict[str, str]:
        return {
            "|1|": f"(retrieve_entity {self.metric_entity_name})",
            "|2|": f"(retrieve_attribute |1| {self.time_attribute_name})",
            "|3|": f"(exact |2| \"{time_value}\")",
        }

    def get_plan_composition_specs(self) -> List[CompositionSpecification]:
        """

        :return: A list of dictionaries, each of which contains keys for "base_plan", "access_plan", "access_plan_filters", and "slot_fillers".
        :rtype: List of dictionaries
        """
        composition_specs = []

        # Get the metric value at time t0 for the target entity
        composition_specs.append(self.get_instance_metric_value_at_time(self.time_zero_filter, self.time_zero))

        # Get the metric value at time t1 for the target entity
        composition_specs.append(self.get_instance_metric_value_at_time(self.time_one_filter, self.time_one))

        # Get the percent change between t1 and t0 for the target entity
        composition_specs.append(self.get_instance_percent_change_over_time())

        # Get the average metric value at time t0 for all entities
        composition_specs.append(self.get_aggregated_metric_value_at_time('average', self.time_zero_filter, self.time_zero))

        # Get the min and max of the aggregated attribute at time t0 for all entities
        composition_specs.append(self.get_aggregated_metric_value_at_time('min', self.time_zero_filter, self.time_zero))
        composition_specs.append(self.get_aggregated_metric_value_at_time('max', self.time_zero_filter, self.time_zero))

        # Get the average metric value at time t1 for all entities
        composition_specs.append(self.get_aggregated_metric_value_at_time('average', self.time_one_filter, self.time_one))

        # Get the min and max of the aggregated attribute at time t1 for all entities
        composition_specs.append(self.get_aggregated_metric_value_at_time('min', self.time_one_filter, self.time_one))
        composition_specs.append(self.get_aggregated_metric_value_at_time('max', self.time_one_filter, self.time_one))

        # Get the percent change between t1 and 0 for all entities
        composition_specs.append(self.get_average_percent_change_over_time())

        # Check if the percent change for target entity is greater than the percent change for all entities
        composition_specs.append(self.get_is_instance_cot_greater_than_average_cot())

        return composition_specs

    def get_instance_metric_value_at_time(self,
                                          time_filter: Dict[str, str],
                                          time_value: str) -> CompositionSpecification:
        base_plan_inputs = {
            "|A|": {
                "access_plan": self.metric_access_plan,
                "access_plan_filters": {
                    "filters": [time_filter, self.instance_filter, self.set_filter if self.set_filter else None],
                    "filter_joiner": "and"
                }
            }
        }
        slot_fillers = {
            "Identifier[0].Value[0]": self.entity_instance_identifier_value,
            "Identifier[0].Value[0].Expression": self.entity_reference,
            "Filter[A].Expression": "for " + str(time_value),
            "Metric[0].Expression": self.metric_nicename
        }
        return CompositionSpecification("InstanceMetricValue",
                                        self.base_plan_templates["InstanceMetricValue"],
                                        base_plan_inputs,
                                        slot_fillers)

    def get_aggregated_metric_value_at_time(self,
                                            aggregation: str,
                                            time_filter: Dict[str, str],
                                            time_value: str) -> CompositionSpecification:
        base_plan_inputs = {
            "|A|": {
                "access_plan": self.metric_access_plan,
                "access_plan_filters": {
                    "filters": [time_filter, self.set_filter if self.set_filter else None],
                    "filter_joiner": "and"
                }
            }
        }
        slot_fillers = {
            "Analysis[0]": aggregation,
            "Filter[A].Expression": "for " + str(time_value)
        }
        return CompositionSpecification("AggregateMetric",
                                        self.base_plan_templates["AggregateMetric"],
                                        base_plan_inputs,
                                        slot_fillers)

    def get_instance_percent_change_over_time(self) -> CompositionSpecification:
        base_plan_inputs = {
            "|A|": {
                "access_plan": self.metric_access_plan,
                "access_plan_filters": {
                    "filters": [self.time_zero_filter, self.instance_filter, self.set_filter if self.set_filter else None],
                    "filter_joiner": "and"
                }
            },
            "|B|": {
                "access_plan": self.metric_access_plan,
                "access_plan_filters": {
                    "filters": [self.time_one_filter, self.instance_filter, self.set_filter if self.set_filter else None],
                    "filter_joiner": "and"
                }
            }
        }
        slot_fillers = {
            "Identifier[0].Value[0].Expression": self.entity_reference,
            "Datetime[0].Value[0].Expression": str(self.time_zero),
            "Datetime[0].Value[1].Expression": str(self.time_one),
            "Metric[0].Expression": self.metric_nicename,

            # Note: The following slots are not used because the filter associated with the plan template is not used.
            "Identifier[0]": self.entity_instance_identifier_attribute_name,
            "Identifier[0].Value[0]": self.entity_instance_identifier_value,
            "EntityClass[A]": self.entity_name,
            "RelatedEntityClass[A]": self.metric_entity_name,
            "Datetime[0]": self.time_attribute_name,
            "Datetime[0].Value[0]": self.time_zero,
            "Datetime[0].Value[1]": self.time_one
        }
        return CompositionSpecification("InstancePercentChangeOverTime",
                                        self.base_plan_templates["InstancePercentChangeOverTime"],
                                        base_plan_inputs,
                                        slot_fillers)

    def get_average_percent_change_over_time(self) -> CompositionSpecification:
        base_plan_inputs = {
            "|A|": {
                "access_plan": self.metric_access_plan,
                "access_plan_filters": {
                    "filters": [self.time_zero_filter, self.set_filter if self.set_filter else None],
                    "filter_joiner": "and"
                }
            },
            "|B|": {
                "access_plan": self.metric_access_plan,
                "access_plan_filters": {
                    "filters": [self.time_one_filter, self.set_filter if self.set_filter else None],
                    "filter_joiner": "and"
                }
            }
        }
        slot_fillers = {
            "Analysis[0]": "average",
            "Metric[0].Expression": self.metric_nicename,
            "EntityClass[A].Expression": self.entity_group,
            "Datetime[0].Value[0].Expression": str(self.time_zero),
            "Datetime[0].Value[1].Expression": str(self.time_one),

            # Note: The following slots are not used because the filter associated with the plan template is not used.
            "RelatedEntityClass[A]": self.metric_entity_name,
            "Datetime[0]": self.time_attribute_name,
            "Datetime[0].Value[0]": self.time_zero,
            "Datetime[0].Value[1]": self.time_one,
        }
        return CompositionSpecification("AggregatePercentChangeOverTime",
                                        self.base_plan_templates["AggregatePercentChangeOverTime"],
                                        base_plan_inputs,
                                        slot_fillers)

    def get_is_instance_cot_greater_than_average_cot(self) -> CompositionSpecification:
        base_plan_inputs = {
            "|A|": {
                "access_plan": self.metric_access_plan,
                "access_plan_filters": {
                    "filters": [self.time_zero_filter,
                                self.instance_filter,
                                self.set_filter if self.set_filter else None],
                    "filter_joiner": "and"
                }
            },
            "|B|": {
                "access_plan": self.metric_access_plan,
                "access_plan_filters": {
                    "filters": [self.time_one_filter,
                                self.instance_filter,
                                self.set_filter if self.set_filter else None],
                    "filter_joiner": "and"
                }
            },
            "|C|": {
                "access_plan": self.metric_access_plan,
                "access_plan_filters": {
                    "filters": [self.time_zero_filter,
                                self.set_filter if self.set_filter else None],
                    "filter_joiner": "and"
                }
            },
            "|D|": {
                "access_plan": self.metric_access_plan,
                "access_plan_filters": {
                    "filters": [self.time_one_filter,
                                self.set_filter if self.set_filter else None],
                    "filter_joiner": "and"
                }
            }
        }
        slot_fillers = {
            "Analysis[0]": "average",
            "EntityClass[A].Expression": self.entity_group,
            "Metric[0].Expression": self.metric_nicename,
            "Datetime[0].Value[0].Expression": str(self.time_zero),
            "Datetime[0].Value[1].Expression": str(self.time_one),
            "Identifier[0].Value[0].Expression": self.entity_reference,

            # Note: The following slots are not used because the filter associated with the plan template is not used.
            "Identifier[0]": self.entity_instance_identifier_attribute_name,
            "Identifier[0].Value[0]": self.entity_instance_identifier_value,
            "EntityClass[A]": self.entity_name,
            "RelatedEntityClass[A]": self.metric_entity_name,
            "Datetime[0]": self.time_attribute_name,
            "Datetime[0].Value[0]": self.time_zero,
            "Datetime[0].Value[1]": self.time_one
        }
        return CompositionSpecification("InstancePercentChangeOverTimeGreaterThanAggregatePercentChangeOverTime",
                                        self.base_plan_templates["InstancePercentChangeOverTimeGreaterThanAggregatePercentChangeOverTime"],
                                        base_plan_inputs,
                                        slot_fillers)

    def build_baseline_prompt(self,
                              entity_reference: str,
                              filter_statement: str) -> str:
        prompt = f"Generate a report for {entity_reference} describing how {self.metric_nicename} has changed over time between {self.time_zero} and {self.time_one}{' ' + filter_statement if filter_statement else ''}. " \
                 f"{'Higher' if self.metric_preference_direction == '+inf' else 'Lower'} values are considered better."
        return prompt

    def build_baseline_prompt_with_info_reqs(self,
                                             entity_reference: str,
                                             filter_statement: str) -> str:
        prompt = self.build_baseline_prompt(entity_reference, filter_statement)
        prompt += f" The metric is {self.metric_nicename}. " \
                  f"In the report, include information about the value of the metric for {entity_reference} at {self.time_zero}, " \
                  f"the value of the metric for {entity_reference} at {self.time_one}, " \
                  f"the percent change between {self.time_zero} and {self.time_one} for {entity_reference}, " \
                  f"the average value of the metric at {self.time_zero} for all {self.entity_name}, " \
                  f"the minimum value of the metric at {self.time_zero} for all {self.entity_name}, " \
                  f"the maximum value of the metric at {self.time_zero} for all {self.entity_name}, " \
                  f"the average value of the metric at {self.time_one} for all {self.entity_name}, " \
                  f"the minimum value of the metric at {self.time_one} for all {self.entity_name}, " \
                  f"the maximum value of the metric at {self.time_one} for all {self.entity_name}, " \
                  f"the percent change between {self.time_zero} and {self.time_one} for all {self.entity_name}, " \
                  f"and whether or not the percent change was greater for {entity_reference} than the percent change for all {self.entity_group}."
        prompt += "\n\n" + self.build_prompting_instructions()
        return prompt
