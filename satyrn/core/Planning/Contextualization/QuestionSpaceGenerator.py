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

from typing import List, Dict

from satyrn.core.RingObjects.Ring import Ring
from satyrn.core.Analysis.OperationOntology import OperationOntology
from satyrn.core.Planning.PlanGeneration.PlanGenerator import PlanGenerator
from satyrn.core.Planning.QuestionGeneratorTemplateBased import QuestionGeneratorTemplateBased
from satyrn.core.Document.BasePlanStore import BasePlanStore
from satyrn.core.Planning.SQRComposer import SQRComposer
from satyrn.core.Planning.PlanGeneration.ExhaustiveBasePlanInputAssigner import ExhaustiveBasePlanInputAssigner
from satyrn.core.Planning.utils import extract_slots

class QuestionSpaceGenerator:
    def __init__(self,
                 ring: Ring,
                 operation_ontology: OperationOntology,
                 base_plan_store: BasePlanStore = None):
        self.ring = ring
        self.operation_ontology = operation_ontology
        self.base_plan_store = BasePlanStore() if not base_plan_store else base_plan_store
        self.sqr_composer = SQRComposer(self.ring, self.operation_ontology)
        self.plan_generator = PlanGenerator(self.ring, self.operation_ontology, self.sqr_composer, self.base_plan_store)
        self.question_generator = QuestionGeneratorTemplateBased(ring, operation_ontology, base_plan_store)
        self.base_plan_input_assigner = ExhaustiveBasePlanInputAssigner(self.ring, self.operation_ontology, self.base_plan_store)

    def generate_space(self,
                       desired_entities: List[str],
                       desired_base_plans: List[str]) -> List[str]:
        """
        Generate the space of general questions Satyrn can answer.
        :param desired_entities: The set of entities to generate the plans for. If this is empty, defaults to all entities in the ring.
        :type desired_entities: List[str]
        :param desired_base_plans: The set of base plans to use for generating plans. If this is empty, defaults to all base plans.
        :type desired_base_plans: List[str]
        :return: A list of general questions Satyrn can answer.
        :rtype: List[str]
        """

        all_specs = []

        # Generate specs and questions using the attributes and their access plans
        all_specs.extend(self.generate_with_access_plans(desired_entities))

        # Generate specs using the base plans
        all_specs.extend(self.generate_with_base_plans(desired_entities, desired_base_plans))

        # Grab all the questions from the generated specs, plans, and questions
        questions_lists = [spec["questions"] for spec in all_specs]
        questions = [q for s in questions_lists for q in s]     # Flatten the list of list of questions

        # Deduplicate the questions
        questions = list({q: None for q in questions}.keys())

        return questions

    def generate_with_base_plans(self,
                                 desired_entities: List[str],
                                 desired_base_plans: List[str]) -> List[Dict]:
        """
        Generate the space of general questions Satyrn can answer.
        :param desired_entities: The set of entities to generate the plans for. If this is empty, defaults to all entities in the ring.
        :type desired_entities: List[str]
        :param desired_base_plans: The set of base plans to use for generating plans. If this is empty, defaults to all base plans.
        :type desired_base_plans: List[Dict]
        :return: A list of dictionaries that look like: { "questions": [], "plan": {} }
        :rtype: List[str]
        """

        # TODO: Add a shortcut to the end for base plans that have no slots in their general_question_templates

        # Determine the set of entities and base plans to use based on the input
        entities = self.plan_generator.determine_entities_to_use(desired_entities)
        base_plans = self.plan_generator.determine_base_plans_to_use(desired_base_plans)

        specs = []
        base_plans_no_slots = []
        for base_plan_name, base_plan_info in base_plans.items():
            if any([len(extract_slots(qt)) > 0 for qt in base_plan_info["general_question_templates"]]):
                for ent in entities:
                    # Get the set of valid attribute assignments for the inputs of the current base plan
                    valid_input_assignments = self.base_plan_input_assigner.get_input_assignments_for_base_plan(base_plan_info, ent)

                    # Produce new CompositionSpecifications for each of the valid assignments
                    for assignment in valid_input_assignments:
                        specs.append(self.base_plan_input_assigner.convert_assignment_to_composition_spec(assignment, base_plan_name))
            else:
                # There were no slots in any of the general question templates, so just take them as is
                base_plans_no_slots.append({
                    "plan": base_plan_name,
                    "spec": None,
                    "questions": base_plan_info["general_question_templates"],
                })

        # Produce new composition specifications by filling in the EntityClass slots (e.g. {EntityClass:A}, {RelatedEntityClass:A})
        final_specs = self.plan_generator.generate_composition_specs_with_specific_slots_and_templates(specs,
                                                                                                       slot_types_to_consider=["EntityClass", "RelatedEntityClass", "Analysis"],
                                                                                                       use_plan_template=True,
                                                                                                       include_filled_slots=False)

        # Get the fillers for slots in the language templates (this is done in place at the moment)
        for spec in final_specs:
            self.plan_generator.get_template_expression_fillers(spec,
                                                                template_type="general_question_templates")

        # Compose the plans based on the composition specs
        final_outputs = []
        for spec in final_specs:
            final_outputs.append({
                "plan": self.sqr_composer.compose(spec)[0],
                "spec": spec
            })
            self.sqr_composer.alphabet_idx = 0

        # Generate the question for each of the plans
        for plan_and_spec in final_outputs:
            # Init the list for storing the filled questions
            plan_and_spec["questions"] = []
            for question_template in self.base_plan_store.templates[plan_and_spec['spec'].base_plan_name]['general_question_templates']:

                # Generate the question
                plan_and_spec["questions"].append(self.question_generator.generate_question(question_template,
                                                                                            plan_and_spec['spec'].slot_fillers,
                                                                                            plan_and_spec['plan'],
                                                                                            {},
                                                                                            plan_slot_fillers=plan_and_spec['spec'].input_fillers))

        # Add the questions for the base plans whose general_question_templates had no slots in them
        final_outputs.extend(base_plans_no_slots)

        # Return the plans, specs, and the questions associated with them
        return final_outputs

    def generate_with_access_plans(self,
                                   desired_entities: List[str]) -> List[Dict]:
        """
        Generates a set of SQR plans and associated questions using the ring attributes and their access plans.
        :param desired_entities: The set of entities to generate the plans for. If this is empty, defaults to all entities in the ring.
        :type desired_entities: List[str]
        :return: A list of dictionaries that look like: { "questions": [], "plan": {} }
        :rtype: List[Dict]
        """

        # Determine the set of entities and base plans to use based on the input
        entities = self.plan_generator.determine_entities_to_use(desired_entities)

        final_outputs = []  # Each output should look like: { "questions": [], "plan": {} }
        for ent in entities:
            for attr_name, attr in ent.attributes.items():

                # Get the access plan
                out = {
                    "plan": self.plan_generator.analysis_plan_parser.parse_plan_snippet(attr.access_plan),
                    "questions": attr.get_general_questions()
                }

                # Save this generation
                final_outputs.append(out)

        return final_outputs
