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

import json
from pathlib import Path
from typing import Dict, List, Tuple

from satyrn.core.RingObjects.Ring import Ring
from satyrn.core.Document.utils import build_metric_name
from satyrn.core.Planning.CompositionSpecification import CompositionSpecification
from satyrn.core.Document.BasePlanStore import BasePlanStore

class DocumentBlueprint():
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
                 **kwargs):
        super().__init__()
        self.entity_name = entity_name
        self.entity_instance_identifier_attribute_name = entity_instance_identifier_attribute_name
        self.entity_instance_identifier_value = entity_instance_identifier_value
        self.entity_reference = entity_reference
        self.metric_entity_name = metric_entity_name
        self.metric_attribute_name = metric_attribute_name
        self.metric_aggregation = metric_aggregation

        self.set_filter = set_filter

        self.metric_preference_direction = metric_preference_direction

        self.ring = ring

        # TODO: In the future, this should not be read as part of the analysis class
        self.base_plan_store = BasePlanStore()
        self.base_plan_templates = self.base_plan_store.templates
        # # Read in the JSON file of info_requirements.json
        # p = Path(__file__).with_name('base_plan_templates.json')
        # with p.open('r') as f:
        #     self.base_plan_templates = json.load(f)

        # Generate / retrieve some useful information about the entity and metric
        self.metric_name = build_metric_name(self.metric_aggregation, self.metric_entity_name, self.metric_attribute_name)
        self.metric_access_plan, self.metric_nicename = self.get_metric_access_plan_and_nicename(self.metric_name)
        self.entity_access_plan = self.get_entity_access_plan()
        self.instance_filter = self.get_instance_filter()

        self.requirements = {}

    def get_plan_composition_specs(self) -> List[CompositionSpecification]:
        """
        To be overridden by inheriting classes
        :return: A list of dictionaries, each of which contains keys for "base_plan", "access_plan", "access_plan_filters", and "slot_fillers".
        :rtype: List of dictionaries
        """
        pass

    def get_entity_access_plan(self) -> Dict:
        # Get the ring entity
        ring_entity = [ent for ent in self.ring.entities if ent.name == self.entity_name][0]

        # Get the attribute from the ring
        ring_attribute = ring_entity.attributes[self.metric_name]

        # Return the access plan for that attribute
        return ring_attribute.access_plan

    def get_metric_access_plan_and_nicename(self,
                                            metric_name: str) -> Tuple[Dict, str]:
        # Get the ring entity
        ring_entity = [ent for ent in self.ring.entities if ent.name == self.entity_name][0]

        # Get the attribute from the ring
        ring_attribute = ring_entity.attributes[metric_name]

        # Get the nicename for the metric
        metric_nicename = ring_attribute.nicename[0]

        # Return the access plan for that attribute
        return ring_attribute.access_plan, metric_nicename

    def get_instance_filter(self) -> Dict:
        return {
            "|1|": f"(retrieve_entity {self.entity_name})",
            "|2|": f"(retrieve_attribute |1| {self.entity_instance_identifier_attribute_name})",
            "|3|": f"(exact |2| \"{self.entity_instance_identifier_value}\")",
        }

    def get_not_instance_filter(self) -> Dict:
        return {
            "|1|": f"(retrieve_entity {self.entity_name})",
            "|2|": f"(retrieve_attribute |1| {self.entity_instance_identifier_attribute_name})",
            "|3|": f"(exact |2| \"{self.entity_instance_identifier_value}\")",
            "|4|": f"(not |3|)"
        }

    @staticmethod
    def parse(utterance, feature_extractor):
        return feature_extractor.extract_entity_instance(utterance)

    def get_target_range(self):
        return self.metric_preference_direction or self.ring.get_entity_by_name(self.metric_entity_name).metrics[self.metric_attribute_name][0]

    def build_baseline_prompt(self,
                              entity_reference: str,
                              filter_statement: str) -> str:
        pass

    def build_prompting_instructions(self) -> str:
        return f"The audience is educated, but may not understand technical terms. " \
               f"Please use natural sounding language and try to find more natural terms for the groups that are mentioned."

    def build_baseline_prompt_with_facts(self,
                                         entity_reference: str,
                                         filter_statement: str,
                                         factual_statements: List[str]) -> str:
        prompt = "Context:\n{}".format('\n'.join(factual_statements))
        prompt += "\n\n" + self.build_baseline_prompt(entity_reference, filter_statement)
        prompt += " Use only the facts provided in the context. "
        prompt += self.build_prompting_instructions()
        return prompt

    def build_baseline_prompt_with_info_reqs(self,
                                             entity_reference: str,
                                             filter_statement: str) -> str:
        pass
