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

class RankingBlueprint(DocumentBlueprint):
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
                 metric_sort_direction):
        super().__init__(entity_name, entity_instance_identifier_attribute_name, entity_instance_identifier_value, entity_reference, metric_entity_name, metric_attribute_name, metric_aggregation, set_filter, metric_preference_direction, ring)
        self.metric_sort_direction = metric_sort_direction

        self.limit = 3
        self.entity_group = self.ring.get_entity_by_name(self.entity_name).nicename[1]

    def get_plan_composition_specs(self) -> List[CompositionSpecification]:
        """

        :return: A list of CompositionSpecification, each of which contains keys for "base_plan", "access_plan", "access_plan_filters", and "slot_fillers".
        :rtype: List of CompositionSpecification
        """

        composition_specs = []

        # Get the metric value for the entity instance
        composition_specs.append(self.get_metric_value_for_entity_instance())

        # Get the total number of entities being ranked
        composition_specs.append(self.get_num_items_to_rank_plan())

        # Get the rank for the target entity instance according to the specified metric
        composition_specs.append(self.get_rank_of_entity_instance_plan())

        # Get the top three entity instances in the ranking according to the specified metric
        composition_specs.append(self.get_top_three_instances())

        # Compute how far away from the top of the ranking the target entity instance is according to the specified metric
        composition_specs.append(self.get_distance_from_max())

        # Compute the average value of the specified metric for all entities being ranked
        composition_specs.append(self.get_aggregated_value_of_metric('average'))

        # Compute min and max of the metric for all entities
        composition_specs.append(self.get_aggregated_value_of_metric('min'))
        composition_specs.append(self.get_aggregated_value_of_metric('max'))

        # Figure out if the target entity instance's comparative metric value is greater than the average for all entities of the same type
        composition_specs.append(self.get_is_instance_metric_greater_than_average_for_all())

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
                } if self.set_filter else {"filters": [], "filter_joiner": None}
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

    def get_num_items_to_rank_plan(self) -> CompositionSpecification:
        """

        :return: The composition specifications.
        :rtype: Dict
        """
        base_plan_inputs = {
            "|A|": {
                "access_plan": self.entity_access_plan,
                "access_plan_filters": {
                    "filters": [self.set_filter],
                    "filter_joiner": None
                } if self.set_filter else {"filters": [], "filter_joiner": None},
            }
        }
        slot_fillers = { }
        return CompositionSpecification("EntityCount",
                                        self.base_plan_templates["EntityCount"],
                                        base_plan_inputs,
                                        slot_fillers)

    def get_rank_of_entity_instance_plan(self) -> CompositionSpecification:
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
                } if self.set_filter else {"filters": [], "filter_joiner": None}
            }
        }
        slot_fillers = {
            "Identifier[0].Value[0]": self.entity_instance_identifier_value,
            "Identifier[0].Value[0].Expression": self.entity_reference,
            "Direction[0]": self.metric_sort_direction,  # TODO: Generalize this beyond binary directionality
            "Metric[0].Expression": self.metric_nicename
        }
        return CompositionSpecification("InstanceRank",
                                        self.base_plan_templates["InstanceRank"],
                                        base_plan_inputs,
                                        slot_fillers)

    def get_top_three_instances(self) -> CompositionSpecification:
        """

        :return:
        :rtype:
        """
        plan = "TopThreeForMetric" if self.metric_sort_direction == 'desc' else "BottomThreeForMetric"
        base_plan_inputs = {
            "|A|": {
                "access_plan": self.metric_access_plan,
                "access_plan_filters": {
                    "filters": [self.set_filter],
                    "filter_joiner": None
                } if self.set_filter else {"filters": [], "filter_joiner": None}
            }
        }
        slot_fillers = {
            "Quantity[0]": self.limit
        }

        return CompositionSpecification(plan,
                                        self.base_plan_templates[plan],
                                        base_plan_inputs,
                                        slot_fillers)

    def get_distance_from_max(self) -> CompositionSpecification:
        """

        :return:
        :rtype:
        """
        plan = "InstanceDistanceFromMax" if self.metric_sort_direction == 'desc' else "InstanceDistanceFromMin"
        base_plan_inputs = {
            "|A|": {
                "access_plan": self.metric_access_plan,
                "access_plan_filters": {
                    "filters": [self.set_filter],
                    "filter_joiner": None
                } if self.set_filter else {"filters": [], "filter_joiner": None}
            },
            "|B|": {
                "access_plan": self.metric_access_plan,
                "access_plan_filters": {
                    "filters": [self.set_filter],
                    "filter_joiner": None
                } if self.set_filter else {"filters": [], "filter_joiner": None}
            }
        }
        slot_fillers = {
            "Identifier[0].Value[0]": self.entity_instance_identifier_value,
            "Identifier[0].Value[0].Expression": self.entity_reference,
            "EntityClass[A].Expression": self.entity_group,
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
                    "filters": [self.set_filter],
                    "filter_joiner": None
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

    def get_is_instance_metric_greater_than_average_for_all(self) -> CompositionSpecification:
        """

        :return:
        :rtype:
        """
        plan = "InstanceGreaterThanAggregatedMetric" if self.get_target_range() == '+inf' else "InstanceLessThanAggregatedMetric"
        base_plan_inputs = {
            "|A|": {
                "access_plan": self.metric_access_plan,
                "access_plan_filters": {
                    "filters": [self.set_filter],
                    "filter_joiner": None
                }
            },
            "|B|": {
                "access_plan": self.metric_access_plan,
                "access_plan_filters": {
                    "filters": [self.set_filter],
                    "filter_joiner": None
                } if self.set_filter else {"filters": [], "filter_joiner": None}
            }
        }
        slot_fillers = {
            "Analysis[0]": "average",
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
        return f"Generate a report for {entity_reference} ranking it according to {self.metric_nicename}{' ' + filter_statement if filter_statement else ''}. " \
        f"{'Higher' if self.metric_preference_direction == '+inf' else 'Lower'} values are considered better."

    def build_baseline_prompt_with_info_reqs(self,
                                             entity_reference: str,
                                             filter_statement: str) -> str:
        prompt = self.build_baseline_prompt(entity_reference, filter_statement)
        prompt += f" The metric is {self.metric_nicename}. " \
                  f"In the report, include information about the value of the metric for {entity_reference}, " \
                  f"the total number of entities being ranked, " \
                  f"the rank of {entity_reference} according to the metric, " \
                  f"the top three {self.entity_name} according to the metric, " \
                  f"how far away from the top of the ranking {entity_reference} is according to the metric, " \
                  f"the average value of the metric for all {self.entity_name}, " \
                  f"the minimum value of the metric for all {self.entity_name}, "\
                  f"the maximum value of the metric for all {self.entity_name}, " \
                  f"and whether or not the metric value for {entity_reference} is greater than the average value of the metric for all {self.entity_name}."
        prompt += "\n\n" + self.build_prompting_instructions()
        return prompt
