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

from typing import Tuple
import ast

from satyrn.core.RingObjects.Ring import Ring
from satyrn.core.RingObjects.RingEntity import RingEntity
from satyrn.core.RingObjects.RingAttribute import RingAttribute

from satyrn.core.LanguageGeneration.GPT35Interface import GPT35Interface

class FeatureExtractor:
    def __init__(self,
                 ring: Ring,
                 chatGPT: GPT35Interface()):
        self.ring = ring
        self.chatGPT = chatGPT

    def extract_entity_instance(self,
                                utterance: str) -> Tuple[RingEntity, RingAttribute, str]:
        # TODO: Implement this for real
        entity_list = [ent.name for ent in self.ring.entities]
        attribute_dict = {}
        for ent in self.ring.entities:
            attribute_dict[ent.name] = [attr for attr in ent.attributes.keys()]

        # TODO: change these static examples to dynamic ones from the plan manager.
        example_1 = \
            " input: Give me a summary for the contributions with contribution recipient Daneil Hynes. \
             Entity: contributions\
             attribute: contributionRecipient, \
             value = Daneil Hynes  \
             "
        example_2 = \
            " input: Give me a summary for the contributions made to Daneil Hynes. \
             Entity: contributions\
             attribute: contributionRecipient, \
             value = Daneil Hynes  \
             "
        example_3 = \
            " input: Tell me how contributor with parent organization NATIONAL AFL-CIO is doing. \
             Entity: contributor \
             attribute: parent_org, \
             value = NATIONAL AFL-CIO "

        example_4 = \
            " input: Tell me how John Doe is doing. \
             Entity: User \
             attribute: username, \
             value = John Doe\
            "

        prompt = "Given the example below: " + example_1 + example_2 + example_3 + example_4 + \
                "What are the entities, filters, and attributes of the following prompt, given the available attributes and entities? " + \
                " prompt: " + utterance, " entities: " + ' ,'.join(entity_list) + " attribute dictionary for each entity: "+ str(attribute_dict) \
                + "give the results as a python list in the form of: [[entity, attribute, value]]. You might see many possible choices, but do not return mutiple results nor return results in the wrong format. In other words, return only one result. Do NOT add any explanation and make sure to return it in the correct format of [[entity, attribute, value]]."
        response_from_gpt = self.chatGPT.generate(str(prompt))
        # Sometimes returns multiple elements so select the first element from the array of arrays
        response = ast.literal_eval(response_from_gpt)[0]
        entity = [ent for ent in self.ring.entities if ent.name == response[0]][0]
        attributes = [attr for attr_name, attr in entity.attributes.items() if attr.name == response[1]]
        filter_attribute = attributes[0] if len(attributes) > 0 else None
        filter_value = response[2]
        print("result is: ", entity, filter_attribute, filter_value)

        return entity, filter_attribute, filter_value
