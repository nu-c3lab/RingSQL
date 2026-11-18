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

class ComparativeBenchmarkBlueprint(DocumentBlueprint):
    """
    Produces a set of information requirements for a single entity instance.
    """
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
                 benchmark_target):
        super().__init__(entity_name, entity_instance_identifier_attribute_name, entity_instance_identifier_value, entity_reference, metric_entity_name, metric_attribute_name, metric_aggregation, set_filter, metric_preference_direction, ring)

        self.benchmark_target = benchmark_target
        self.not_instance_filter = self.get_not_instance_filter()

    def get_plan_composition_specs(self) -> List[CompositionSpecification]:
        """

        :return: A list of dictionaries, each of which contains keys for "base_plan", "access_plan", "access_plan_filters", and "slot_fillers".
        :rtype: List of dictionaries
        """

        composition_specs = []

        # Get the metric value for the entity instance
        composition_specs.append(self.get_metric_value_for_entity_instance())

        # Figure out if the entity instance's value is greater than the target benchmark value
        composition_specs.append(self.is_instance_metric_greater_than_benchmark_target())

        # Compute the min, max, average, median, and standard deviation the specified metric for all entities being compared
        composition_specs.append(self.get_aggregated_value_of_metric('min'))
        composition_specs.append(self.get_aggregated_value_of_metric('max'))

        composition_specs.append(self.get_aggregated_value_of_metric('median'))
        composition_specs.append(self.get_is_instance_metric_greater_than_aggregated_metric_for_others('median'))

        composition_specs.append(self.get_aggregated_value_of_metric('average'))
        composition_specs.append(self.get_is_instance_metric_greater_than_aggregated_metric_for_others('average'))

        composition_specs.append(self.get_aggregated_value_of_metric('stddev'))

        return composition_specs

    def get_metric_value_for_entity_instance(self) -> CompositionSpecification:
        """

        :return:
        :rtype:
        """
        base_plan_inputs = {
            "|A|": {
                "access_plan": self.metric_access_plan,
                "access_plan_filters": {
                    "filters": [self.set_filter],
                    "filter_joiner": None
                }
            }
        }
        slot_fillers = {
            "Identifier[0].Value[0]": self.entity_instance_identifier_value,
            "Identifier[0].Value[0].Expression": self.entity_reference,
            "Filter[A].Expression": "",
            "Metric[0].Expression": self.metric_nicename
        }
        return CompositionSpecification("InstanceMetricValue",
                                        self.base_plan_templates["InstanceMetricValue"],
                                        base_plan_inputs,
                                        slot_fillers)

    def is_instance_metric_greater_than_benchmark_target(self) -> CompositionSpecification:
        """

        :return:
        :rtype:
        """
        plan = "InstanceGreaterThanQuantity" if self.get_target_range() == '+inf' else "InstanceLessThanQuantity"
        base_plan_inputs = {
            "|A|": {
                "access_plan": self.metric_access_plan,
                "access_plan_filters": {
                    "filters": [self.set_filter],
                    "filter_joiner": None
                }
            }
        }
        slot_fillers = {
            "Identifier[0].Value[0]": self.entity_instance_identifier_value,
            "Identifier[0].Value[0].Expression": self.entity_reference,
            "Quantity[0]": self.benchmark_target,
            "Metric[0].Expression": self.metric_nicename
        }
        return CompositionSpecification(plan,
                                        self.base_plan_templates[plan],
                                        base_plan_inputs,
                                        slot_fillers)

    def get_aggregated_value_of_metric(self,
                                       aggregation: str) -> CompositionSpecification:
        """

        :return:
        :rtype:
        """
        base_plan_inputs = {
            "|A|": {
                "access_plan": self.metric_access_plan,
                "access_plan_filters": {
                    "filters": [self.set_filter, self.not_instance_filter],
                    "filter_joiner": "and"
                }
            }
        }
        slot_fillers = {
            "Analysis[0]": aggregation,
            "Filter[A].Expression": ""
        }
        return CompositionSpecification("AggregateMetric",
                                        self.base_plan_templates["AggregateMetric"],
                                        base_plan_inputs,
                                        slot_fillers)

    def get_is_instance_metric_greater_than_aggregated_metric_for_others(self,
                                                                         aggregation: str) -> CompositionSpecification:
        """

        :return:
        :rtype:
        """
        plan = "InstanceGreaterThanAggregatedMetric" if self.get_target_range() == '+inf' else "InstanceLessThanAggregatedMetric"
        base_plan_inputs = {
            "|A|": {
                "access_plan": self.metric_access_plan,
                "access_plan_filters": {
                    "filters": [self.set_filter, self.not_instance_filter],
                    "filter_joiner": "and"
                }
            },
            "|B|": {
                "access_plan": self.metric_access_plan,
                "access_plan_filters": {
                    "filters": [self.set_filter],
                    "filter_joiner": "and"
                }
            }
        }
        slot_fillers = {
            "Analysis[0]": aggregation,
            "Identifier[0].Value[0]": self.entity_instance_identifier_value,
            "Identifier[0].Value[0].Expression": self.entity_reference,
            "Metric[0].Expression": self.metric_nicename
        }
        return CompositionSpecification(plan,
                                        self.base_plan_templates[plan],
                                        base_plan_inputs,
                                        slot_fillers)

    def build_baseline_prompt(self,
                              entity_reference: str,
                              filter_statement: str) -> str:
        prompt = f"Generate a report for {entity_reference} comparing it to the target benchmark for {self.metric_nicename}{' ' + filter_statement if filter_statement else ''}. " \
                 f"The target benchmark value is {self.benchmark_target}. " \
                 f"It is better to be {'higher' if self.metric_preference_direction == '+inf' else 'lower'} than the target benchmark value."
        return prompt

    def build_baseline_prompt_with_info_reqs(self,
                                             entity_reference: str,
                                             filter_statement: str) -> str:
        prompt = self.build_baseline_prompt(entity_reference, filter_statement)
        prompt += f" The metric is {self.metric_nicename}. " \
                  f"In the report, include information about the value of the metric for {entity_reference}, " \
                  f"whether or not the metric value for {entity_reference} is greater than the target benchmark value, " \
                  f"what the minimum value of the metric is, "\
                  f"what the maximum value of the metric is, " \
                  f"what the median value of the metric is, " \
                  f"whether or not the metric value for {entity_reference} is greater than the median value of the metric, " \
                  f"what the average value of the metric is, " \
                  f"whether or not the metric value for {entity_reference} is greater than the average value of the metric, " \
                  f"and what the standard deviation is for the metric."
        prompt += "\n\n" + self.build_prompting_instructions()
        return prompt
