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

from typing import Tuple, Type, Dict, List, Optional
from contextlib import closing

from satyrn.core.RingObjects.Ring import Ring

from satyrn.core.Analysis.AnalysisEngine import AnalysisEngine
from satyrn.core.Analysis.AnalysisPlan import AnalysisPlan
from satyrn.core.Analysis.OperationOntology import OperationOntology
from satyrn.core.LanguageGeneration.GPT35Interface import GPT35Interface
from satyrn.core.LanguageGeneration.GPT4Interface import GPT4Interface

from satyrn.core.Planning.StatementGenerator import StatementGenerator, GenerationMode
from satyrn.core.Planning.StatementGeneratorTemplateBased import StatementGeneratorTemplateBased

from satyrn.core.QuestionAnalysis.FeatureExtractor import FeatureExtractor
from satyrn.core.QuestionAnalysis.UtteranceClassifier import UtteranceClassifier
from satyrn.core.Planning.InformationPlanner import InformationPlanner
from satyrn.core.Document.UtteranceType import UtteranceType
from satyrn.core.Document.DocumentType import DocumentType

class DocumentManager:

    feature_extractor_lm = GPT35Interface()

    def __init__(self,
                 ring: Ring,
                 operation_ontology: OperationOntology,
                 statement_generation_mode: GenerationMode = GenerationMode.OneStatementPerPlan,
                 qa_index_path: Optional[str] = None,
                 language_model = GPT35Interface(),
                 plan_statement_generator = StatementGenerator):
        self.ring = ring
        self.operation_ontology = operation_ontology
        self.analysis_engine = AnalysisEngine(self.ring)
        self.language_model = language_model
        self.feature_extractor = FeatureExtractor(self.ring, self.feature_extractor_lm)
        self.plan_statement_generator = plan_statement_generator(self.ring, self.operation_ontology, mode=statement_generation_mode)
        self.info_planner = InformationPlanner(self.ring, self.operation_ontology)

    def generate_output(self,
                        utterance: str) -> Dict:
        """
        Runs the main pipeline for generating an answer/report for a given utterance.
        :param utterance: An information seeking statement/question.
        :type utterance: str
        :return: A string that answers the given information seeking statement/question.
        :rtype: str
        """

        # Determine the type of utterance we were given
        utterance_type = self.determine_utterance_type(utterance)

        # Get the plans based on the utterance type
        if (utterance_type == UtteranceType.Question or utterance == UtteranceType.InfoRequest) and self.llm_index:
            # Query the index of generated factual statements for an answer
            result = self.llm_index.qa({"query": utterance})

            return {
                "report": result["result"],
                "factual_statements": [doc.page_content for doc in result["source_documents"]]
            }

        elif utterance_type == UtteranceType.ReportRequest:

            # Determine the report type
            report_type = self.determine_report_type(utterance)

            # Extract entity information
            entity, filter_attribute, filter_value = report_type.parse(utterance, self.feature_extractor)

            # Init the document type to generate
            report = report_type(entity.name, filter_attribute.name, filter_value)

            # Build plans from the information requirements
            info_requirements = report.get_information_requirements(entity.name, filter_attribute.name, filter_value)
            raw_plans = self.info_planner.get_raw_plans_from_requirements(info_requirements)
            plans = self.info_planner.generate_plans_from_raw_plans(raw_plans)
        else:
            raise NotImplementedError

        # Express these plans in natural language by generating a template where their results can be slotted in
        full_plans = [(p, self.plan_statement_generator.generate_statement_template_from_plan(p)) for p in plans]

        # Get the factual statements by executing each plan and slotting the result into the language template
        # factual_statements = [self.get_plan_execution_result(plan_with_template) for plan_with_template in full_plans]
        factual_statements = []
        for plan_with_template in full_plans:
            factual_statements.extend(self.get_plan_execution_result(plan_with_template))

        # Generate the prompt
        prompt = report.build_basic_prompt(factual_statements)

        # Make the call to the language model
        generated_report = self.language_model.generate(prompt)

        return {
            "report": generated_report,
            "factual_statements": factual_statements
        }

    @staticmethod
    def determine_utterance_type(utterance: str) -> UtteranceType:
        """
        Map the given utterance to a specific type of information seeking utterance.
        :param utterance: The utterance to determine the type for.
        :type utterance: str
        :return: The type of the utterance
        :rtype: UtteranceType
        """
        utterance_classifier = UtteranceClassifier()
        utterance_type = utterance_classifier.extract_utterance_type(utterance)
        if utterance_type == "report":
            return UtteranceType.ReportRequest
        else:
            return UtteranceType.Question

    @staticmethod
    def determine_report_type(report_request: str) -> Type[DocumentType]:
        """
        Map the given report request to a specific type of document to be generated.
        :param report_request: The statement that is requesting a report.
        :type report_request: str
        :return: The type of document to generate.
        :rtype: DocumentType
        """

        # TODO: Implement a robust version of this
        if "patient summary" in report_request.lower():
            return PatientSummary
        elif "subject report" in report_request.lower():
            return SubjectReport
        elif "stay report" in report_request.lower():
            return StayReport
        elif "performance review" in report_request.lower() or "performance report" in report_request.lower():
            return PerformanceReview
        elif "rent" in report_request.lower():
            if "national" in report_request.lower():
                return NationalRentTrendsReport
            else:
                return RegionRentReport
        else:
            return PerformanceReview

    def get_plan_execution_result(self,
                                  plan_with_template: Tuple[AnalysisPlan, str]) -> List[str]:
        """
        Executes the given analysis plan and slots the result into its language template.
        :param plan_with_template: The analysis plan to execute and it's language template.
        :type plan_with_template: Tuple of AnalysisPlan and str
        :return: The fact that results from executing the analysis statement.
        :rtype: str
        """

        # Pull values out of the tuple
        analysis_plan = plan_with_template[0]
        statement_template = plan_with_template[1]

        # Perform the analysis
        with closing(self.ring.db.session_maker()) as session:
            results = self.analysis_engine.sqr_single_ring_analysis(analysis_plan, self.ring, session)

        # Slot the results into the plan's result_statement
        factual_statements = self.plan_statement_generator.fill_result(results, statement_template)

        return factual_statements
