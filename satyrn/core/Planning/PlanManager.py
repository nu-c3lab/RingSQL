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

"""
Plan Manager

November 22, 2022
Authors: C3 Lab
"""

import re
import copy
from typing import List, Tuple

from satyrn.core.RingObjects.Ring import Ring
from satyrn.core.RingObjects.RingAttribute import RingAttribute
from satyrn.core.Analysis.OperationOntology import OperationOntology
from satyrn.core.Document.Requirements import *
from satyrn.core.Planning.InformationPlanner import InformationPlanner

class PlanManager:
    def __init__(self,
                 ring: Ring,
                 ontology: OperationOntology):
        self.ring = ring
        self.ontology = ontology
        self.info_planner = InformationPlanner(self.ring, self.ontology)

        ### UPDATE THIS CLASS FOR NEW BLUEPRINT STYLE REPORTS ###

        # Class Requirements
        self.entity_info_requirement_classes = [
            EntityClassWithMetrics,
            EntityClassWithRelatedEntityMetrics
        ]

        # Instance Requirements (commented out for now until implemented)
        self.instance_info_requirement_classes = [
            EntityInstanceCategories,
            EntityInstanceWithMetrics,
            EntityInstanceWithRelatedEntityMetrics
        ]
        self.info_requirements = [cls(entity.name) for cls in self.entity_info_requirement_classes for entity in self.ring.entities]
        self.info_requirements.extend(cls(entity.name, '{Categorical}', '{Value}') for cls in self.instance_info_requirement_classes for entity in self.ring.entities)

    # def generate(self,
    #              filters: List = None) -> Tuple[List[dict], List[dict]]:
    #     """
    #     Generate plans using the space of analysis operations from the ontology and attributes from the ring.
    #     :return: A list of possible plans.
    #     :return type: list of dict
    #     Note: The basic algorithm is to generate an initial set of basic plans for each operation that can be performed against an attribute.
    #           Then, using this set of plans, generate any possible plans with time series.
    #           Then, using this set of plans, generate any possible plans with group bys.
    #           And repeat this process for each of the attributes of the target entity in the ring.
    #     """
    #
    #     plans = []
    #
    #     # Get/build the analysis space
    #     for operation in self.ontology.analysis_operations:
    #         for arithmetic_attribute in self.ring.get_all_attributes('Arithmetic'):
    #             # generate base (single-attribute, no group by) plan
    #             base_plan = self.get_base_plan(operation, arithmetic_attribute)
    #             plans.append(base_plan)
    #             # add group bys to each plan
    #             for categorical_attribute in self.ring.get_all_attributes('Categorical'):
    #                 plans.append(self.get_group_by_plan(base_plan, categorical_attribute))
    #
    #     filter_plans = self.generate_plans_with_filters(plans, filters)
    #
    #     return plans, filter_plans

    def generate(self,
                 filters: List = None) -> Tuple[List[dict], List[dict]]:
        """
        Generate plans using the space of analysis operations from the ontology and attributes from the ring.
        :return: A list of possible plans.
        :return type: list of dict
        Note: The basic algorithm is to generate an initial set of basic plans for each operation that can be performed against an attribute.
              Then, using this set of plans, generate any possible plans with time series.
              Then, using this set of plans, generate any possible plans with group bys.
              And repeat this process for each of the attributes of the target entity in the ring.
        """

        raw_plans = self.info_planner.get_raw_plans_from_requirements(self.info_requirements)
        plans = self.info_planner.generate_plans_from_raw_plans(raw_plans)
        return raw_plans, plans

    def generate_plans_with_filters(self,
                                    plans: List[dict],
                                    filters: List[List]) -> List[dict]:
        """
        Creates a new list of plans with the given filters.
        For each of the given plans, a new plan will be created with each of the given filters (one for each filter for each plan).
        :param plans: The plans upon which the newly generated plans will be based.
        :type plans: list of dicts
        :param filters: The Satyrn filters to add to the plan (each filter is a list consisting of three entries).
        :type filters: list of lists
        :return: A list of all the new plans.
        :rtype: list of dicts
        """

        if filters:
            new_plans = []
            # Add the filters to the plans
            for p in plans:
                for f in filters:
                    # Not sure whether/how we want to do this, given the exceptionally large space of possibilities
                    pass

            return new_plans
        else:
            return []

    def get_base_plan(self,
                      operation: str,
                      attribute: RingAttribute):
        return {
            '|1|': f'(retrieve_entity {attribute.parent_entity["name"]})',
            '|2|': f'(retrieve_attribute |1| {attribute.name})',
            '|3|': f'({operation} |2|)',
            '|4|': f'(collect |3|)',
            '|5|': f'(return |4|)'
        }

    def get_group_by_plan(self,
                          base_plan: dict,
                          attribute: RingAttribute):
        group_by_plan = copy.deepcopy(base_plan)
        group_by_plan['|6|'] = f'(retrieve_attribute |1| {attribute.name})'
        group_by_plan['|7|'] = f'(groupby |6|)'
        group_by_plan['|3|'] = group_by_plan['|3|'][:-1] + ' |7|)' # TODO: Change this to use regular expressions
        group_by_plan['|4|'] = group_by_plan['|4|'][:-1] + ' |2|)' # TODO: Change this to use regular expressions
        return group_by_plan
