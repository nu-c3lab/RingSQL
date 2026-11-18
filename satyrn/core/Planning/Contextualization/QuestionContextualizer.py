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
from typing import List, Dict
from satyrn.core.RingObjects.Ring import Ring
from satyrn.core.Analysis.OperationOntology import OperationOntology
from satyrn.core.Document.BasePlanStore import BasePlanStore
from satyrn.core.Planning.Contextualization.QuestionSpaceGenerator import QuestionSpaceGenerator
from satyrn.core.LanguageGeneration.GPT4TurboInterface import GPT4TurboInterface

class QuestionContextualizer:
    def __init__(self,
                 ring: Ring,
                 operation_ontology: OperationOntology,
                 base_plan_store: BasePlanStore = None):
        self.ring = ring
        self.operation_ontology = operation_ontology
        self.base_plan_store = BasePlanStore() if not base_plan_store else base_plan_store
        self.question_space_generator = QuestionSpaceGenerator(self.ring, self.operation_ontology, self.base_plan_store)
        self.llm = GPT4TurboInterface()

    def contextualize(self,
                      question: str,
                      desired_entities: List[str],
                      desired_base_plans: List[str],
                      mode: str) -> List[str]:
        """
        Produces a set of questions whose answer would help contextualize the given question.
        :param question: The question to contextualize.
        :type question: str
        :param mode: The mode that specifies the way contextualizing questions should be derived.
        :type mode: str
        :return: A list of questions.
        :rtype: List[str]
        """

        LIMIT = 5
        if mode == 'question_space':
            # Generate the space of questions that can likely be answered by the question
            question_space = self.question_space_generator.generate_space(desired_entities, desired_base_plans)

            # Pick the top 5 that are most relevant to the given question
            most_relevant_questions = self.get_relevant_questions(question, question_space, limit=LIMIT)

            # Adapt those questions to the specifics of the given question
            adapted_questions = self.adapt_questions(question, most_relevant_questions)

            return adapted_questions

        elif mode == 'generate_from_entities':
            questions = self.generate_relevant_questions_with_entities_and_attributes(question,
                                                                                      limit=LIMIT)
            return questions

        else:
            raise ValueError(f"Unknown contextualization mode: {mode}")

    def get_relevant_questions(self,
                               target_question: str,
                               question_space: List[str],
                               limit: int) -> List[str]:
        """
        Select the most relevant questions from the given set of questions.
        :param target_question:
        :type target_question: str
        :param question_space:
        :type question_space: List[str]
        :param limit:
        :type limit: int
        :return: A list of questions.
        :rtype: List[str]
        """

        nl = '\n'
        prompt = f"Target Question: {target_question}\n\n" \
                 f"The following are a list of Generic Questions related to the Target Question:\n\n" \
                 f"{nl.join(question_space)}" \
                 f"\n\nThe Generic Questions may or may not be related to the Target Question. " \
                 f"The following are the set of entities and a list of their attributes:\n\n" \
                 f"{self.ring.get_entities_and_attributes_string()}\n\n" \
                 f"Please pick up to {limit} of the most relevant questions from the list of Generic Question based on how well they would provide context for the Target Question. " \
                 f"Please ensure the chosen set of questions is diverse and does not include too many of the same kind of question.\n\n" \
                 f"Please return the results as a JSON object with a single key 'relevant_questions' where the value is an array of strings."

        raw_output = self.llm.generate(prompt, response_format_type="json_object")

        # Load the LLM's output to a JSON object
        relevant_questions_json = json.loads(raw_output)

        if 'relevant_questions' in relevant_questions_json:
            return relevant_questions_json['relevant_questions']
        else:
            return []

    def generate_relevant_questions_with_entities_and_attributes(self,
                                                                 target_question: str,
                                                                 limit: int) -> List[str]:
        """
        Generates contextualizing questions based on the set of available entities and attributes in the ring.
        :param target_question:
        :type target_question: str
        :param limit:
        :type limit: int
        :return:
        :rtype:
        """

        prompt = f"Target Question: {target_question}\n\n" \
                 f"The following are the set of the available Entities and a list of their Attributes:\n\n" \
                 f"{self.ring.get_entities_and_attributes_string()}\n\n" \
                 f"Please generate up to {limit} relevant questions that would provide context for the Target Question and improve a person's understanding of the answer to the Target Question.\n" \
                 f"When generating the list of questions, use only Entities and Attributes that are available.\n\n" \
                 f"Please return the results as a JSON object with a single key 'relevant_questions' where the value is an array of strings."
        print(prompt)
        raw_output = self.llm.generate(prompt, response_format_type="json_object")

        # Load the LLM's output to a JSON object
        relevant_questions_json = json.loads(raw_output)

        if 'relevant_questions' in relevant_questions_json:
            return relevant_questions_json['relevant_questions']
        else:
            return []

    def adapt_questions(self,
                        target_question: str,
                        relevant_questions: List[str]) -> List[str]:
        """
        Adapts the given relevant_questions to be better relate to the target_question.
        :param question:
        :type question: str
        :param relevant_questions:
        :type relevant_questions: List[str]
        :return:
        :rtype: List[str]
        """
        nl = '\n'
        prompt = f"Target Question: {target_question}\n\n" \
                 f"The following are a list of Generic Questions related to the Target Question:\n\n" \
                 f"{nl.join(relevant_questions)}" \
                 f"\n\nCan you adapt the generic questions to be related to the Target Question in terms of entities and filters? " \
                 f"If a question references a generic amount, please replace this with a reasonable value.\n\n" \
                 f"Please return the results as a JSON object with a single key 'adapted_questions' where the value is an array of strings."

        raw_output = self.llm.generate(prompt, response_format_type="json_object")

        # Load the LLM's output to a JSON object
        adapted_questions_json = json.loads(raw_output)

        if 'adapted_questions' in adapted_questions_json:
            return adapted_questions_json['adapted_questions']
        else:
            return []
