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
from contextlib import closing

from flask import Blueprint, current_app, jsonify, request
from flask_cors import cross_origin

from .viewHelpers import api_key_check, get_or_create_ring
from satyrn.core.Analysis.AnalysisEngine import AnalysisEngine
from satyrn.core.Analysis.OperationOntology import OperationOntology
from satyrn.core.QuestionAnalysis.FeatureExtractor import FeatureExtractor
from satyrn.core.LanguageGeneration.GPT35Interface import GPT35Interface
from satyrn.core.LanguageGeneration.GPT4Interface import GPT4Interface
from satyrn.core.LanguageGeneration.GPT4TurboInterface import GPT4TurboInterface
from satyrn.core.LanguageGeneration.GPT4oMiniInterface import GPT4oMiniInterface
from satyrn.core.LanguageGeneration.Mixtral8x7BInterface import Mixtral8x7BInterface
from satyrn.core.LanguageGeneration.Llama8BInterface import LlamaInterface
from satyrn.core.LanguageGeneration.CodeInterpreterInterface import CodeInterpreterInterface
from satyrn.core.LanguageGeneration.StableBelugaInterface import StableBelugaInterface
from satyrn.core.Planning.StatementGenerator import StatementGenerator, GenerationMode
from satyrn.core.Planning.StatementGeneratorTemplateBased import StatementGeneratorTemplateBased
from satyrn.core.Planning.AnalysisPlanParser import AnalysisPlanParser
from satyrn.core.Planning.SQRCompiler import SQRCompiler
from satyrn.core.api.DocumentManager import DocumentManager
from satyrn.core.Planning.PlanManager import PlanManager
from satyrn.core.Planning.SQRComposer import SQRComposer
from satyrn.core.Planning.QuestionGenerator import QuestionGenerator
from satyrn.core.Document import *
from satyrn.core.Document.SQRPlanFiller import SQRPlanFiller
from satyrn.core.Analysis.AnalysisPlan import AnalysisPlan
from satyrn.core.Document.RankingBlueprint import RankingBlueprint
from satyrn.core.Document.ComparativeBenchmarkBlueprint import ComparativeBenchmarkBlueprint
from satyrn.core.Document.TimeOverTimeBlueprint import TimeOverTimeBlueprint
from satyrn.core.Operations.ArgType import ArgType
from prettytable import PrettyTable
from satyrn.core.Document.BasePlanStore import BasePlanStore
from satyrn.core.Planning.QuestionGeneratorTemplateBased import QuestionGeneratorTemplateBased
from satyrn.core.Planning.PlanGeneration.PlanGenerator import PlanGenerator
from satyrn.core.Planning.Contextualization.QuestionContextualizer import QuestionContextualizer
from satyrn.core.Planning.PlanGeneration.CacheManager import CacheManager

from functools import reduce
import multiprocessing
from typing import Dict, List, Tuple
# import concurrent.futures
# import functools
# from flask import jsonify, copy_current_request_context
# EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=16)

# def timeout(seconds):
#     """Decorator to time-limit a function (like a Flask route)."""
#     def decorator(func):
#         @functools.wraps(func)
#         def wrapper(*args, **kwargs):
#             with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
#                 future = executor.submit(func, *args, **kwargs)
#                 try:
#                     return future.result(timeout=seconds)
#                 except concurrent.futures.TimeoutError:
#                     return jsonify({"error": f"Request timed out after {seconds}s"}), 504
#         return wrapper
#     return decorator

# def timeout(seconds):
#     """Time-limit a Flask view by running it in a worker thread with the current request context copied."""
#     def decorator(func):
#         @functools.wraps(func)
#         def wrapper(*args, **kwargs):
#             # Copy Flask's request/app context into the worker
#             wrapped = copy_current_request_context(func)
#             fut = EXECUTOR.submit(wrapped, *args, **kwargs)
#             try:
#                 return fut.result(timeout=seconds)
#             except concurrent.futures.TimeoutError:
#                 fut.cancel()  # best-effort; thread won't be forcibly killed
#                 return jsonify({"error": f"Request timed out after {seconds}s"}), 504
#         return wrapper
#     return decorator

# # some "local globals"
app = current_app # this is now the same app instance as defined in appBundler.py
api = Blueprint("api", __name__)
cache = app.cache

def _generate_plans_internal(plan_generator: PlanGenerator, request_dict: Dict) -> List[Dict]:
    plans_and_questions = []
    if request_dict["num_access_plans_per_attribute"] > 0:
        plans_and_questions.extend(plan_generator.generate_with_access_plans(request_dict["desired_entities"],
                                                                             request_dict["num_access_plans_per_attribute"],
                                                                             request_dict["filter_proportion"]))
    if request_dict["num_plans_per_base_plan_per_entity"] > 0:
        plans_and_questions.extend(plan_generator.generate_with_base_plans(request_dict["desired_entities"],
                                                                           [request_dict["target_base_plan"]],
                                                                           request_dict["num_plans_per_base_plan_per_entity"],
                                                                           request_dict["filter_proportion"],
                                                                           timeout_seconds=request_dict.get("timeout_seconds")))
    if request_dict["num_retrieval_plans_per_entity"] > 0:
        plans_and_questions.extend(plan_generator.generate_retrieval_plans(request_dict["desired_entities"],
                                                                           request_dict["num_retrieval_plans_per_entity"],
                                                                           request_dict["filter_proportion"],
                                                                           request_dict.get("retrieval_distinct_proportion", 0)))

    if request_dict["num_grouping_plans_per_entity"] > 0:
        plans_and_questions.extend(plan_generator.generate_grouping_plans(request_dict["desired_entities"],
                                                                          request_dict["num_grouping_plans_per_entity"],
                                                                          request_dict["filter_proportion"],
                                                                          request_dict.get("grouping_having_proportion", 0)))

    if request_dict["num_set_operation_plans_per_entity"] > 0:
        plans_and_questions.extend(plan_generator.generate_set_operation_plans(request_dict["desired_entities"],
                                                                          request_dict["num_set_operation_plans_per_entity"],
                                                                          request_dict["filter_proportion"]))
    if request_dict["num_in_operation_plans_per_entity"] > 0:
        plans_and_questions.extend(plan_generator.generate_in_operation_plans(request_dict["desired_entities"],
                                                                          request_dict["num_in_operation_plans_per_entity"],
                                                                          request_dict["filter_proportion"],
                                                                          request_dict["in_op_negate_proportion"]))
    if request_dict["num_multi_join_plans_per_entity"] > 0:
        plans_and_questions.extend(plan_generator.generate_multi_join_plans(request_dict["desired_entities"],
                                                                          request_dict["num_multi_join_plans_per_entity"],
                                                                          request_dict["filter_proportion"]))
    
    if request_dict["num_simple_aggregation_plans_per_entity"] > 0:
        plans_and_questions.extend(plan_generator.generate_simple_aggregation_plans(request_dict["desired_entities"],
                                                                          request_dict["num_simple_aggregation_plans_per_entity"],
                                                                          request_dict["filter_proportion"]))

    if request_dict["num_simple_join_plans_per_entity"] > 0:
        plans_and_questions.extend(plan_generator.generate_simple_join_plans(request_dict["desired_entities"],
                                                                          request_dict["num_simple_join_plans_per_entity"],
                                                                          request_dict["filter_proportion"]))
    
    if request_dict["augment_with_order_by_proportion"] > 0:
        plans_and_questions = plan_generator.augment_plans_with_order_by(plans_and_questions,
                                                                         request_dict["augment_with_order_by_proportion"])


    if request_dict.get("num_simple_sql_plans_per_entity", 0) > 0:
        plans_and_questions.extend(plan_generator.generate_simple_sql_plans(request_dict["desired_entities"],
                                                                          request_dict["num_simple_sql_plans_per_entity"],
                                                                          request_dict["filter_proportion"]))
    return plans_and_questions

def _generate_plans_payload_process(ring_id: str,
                                    version: str,
                                    request_dict: Dict,
                                    output_queue: multiprocessing.Queue) -> None:
    try:
        if not app.plan_generator or app.plan_generator.ring.id != ring_id:
            ring = get_or_create_ring(ring_id, version)
            operation_ontology = OperationOntology()
            sqr_composer = SQRComposer(ring, operation_ontology)
            base_plan_store = BasePlanStore()
            cache_manager = CacheManager(ring, max_items=200, max_values_per_item=500)
            app.plan_generator = PlanGenerator(ring, operation_ontology, sqr_composer, base_plan_store, cache_manager)

        plans_and_questions = _generate_plans_internal(app.plan_generator, request_dict)
        final_output = {
            "plans_and_questions": [{
                "plan": pq["plan"].to_json() if pq["plan"] else None,
                "questions": pq["questions"],
                "ring_id": ring_id,
                "base_plan": pq["base_plan"],
                "source": pq["source"],
                "access_plans": pq["access_plans"] if "access_plans" in pq else {},
                "sql": pq["sql"] if "sql" in pq else None,
            } for pq in plans_and_questions]
        }
        output_queue.put(final_output)
    except Exception:
        output_queue.put({"plans_and_questions": []})

# THE ROUTES
# base route as a pseudo health check
# no login necessary to check this
@api.route("/")
@api_key_check
def base():
    return json.dumps({
        "status": "API is up and running"
    })

@api.route("/rings/", methods=["GET"]) #, "POST"])
@api_key_check
def get_api_info():
    return json.dumps({
        # "success": success,
        # "message": msg,
        "rings": [{
            "id": rid,
            "versions": {
                version: {
                    "name": ringInfo.name,
                    "description": ringInfo.description
                }
                for version, ringInfo in app.rings.get(rid).items()
            }
        }
        for rid in app.rings.keys()]
    })


@api.route("/rings/<ring_id>/", methods=["GET"])
@api_key_check
def get_ring_info(ring_id):
    # THIS IS GOING TO ASSUME THE REQUESTING PROXY
    # IS MANAGING WHETHER THE USER HAS THE RIGHT TO DO THIS OR NOT
    # Also, if no version set, "latest" is implied (see next endpoint for explicitly set version)
    ring = get_or_create_ring(ring_id)
    if tuple(ring) is tuple:
        # ring will now be an error message
        return json.dumps(ring)
    ringInfo = ring.generate_info()
    return json.dumps(ringInfo)

@api.route("/rings/<ring_id>/<version>/", methods=["GET"])
@api_key_check
def get_ring_info_with_version(ring_id,
                               version):
    # THIS IS GOING TO ASSUME THE REQUESTING PROXY
    # IS MANAGING WHETHER THE USER HAS THE RIGHT TO DO THIS OR NOT
    ring = get_or_create_ring(ring_id, version=version)
    if tuple(ring )is tuple:
        # ring will now be an error message
        return json.dumps(ring)
    ringInfo = ring.generate_info()
    return json.dumps(ringInfo)

@api.route("/sqr_plan/<ring_id>/<version>/", methods=["GET"])
@api_key_check
def get_sqr_plans(ring_id,
                  version):
    """
    Generates the set of all SQR plans for a given ring.
    This is primarily used for testing.
    :param ring_id:
    :type ring_id:
    :param version:
    :type version:
    :return:
    :rtype:
    """
    # Init the ring
    ring = get_or_create_ring(ring_id, version)

    # Init the operation ontology
    ontology = OperationOntology()

    # Init the plan manager
    plan_manager = PlanManager(ring, ontology)

    # Generate the plans
    raw_plans, plans = plan_manager.generate()

    question_generator = QuestionGenerator(ring, ontology)
    questions = [question_generator.generate_question_from_plan(plan) for plan in plans]

    # Format and return the results
    return json.dumps({
        "plan_templates": raw_plans,
        "plans": plans,
        "questions": questions
    }, default=str, indent=4)

@api.route("/sqr_analysis/<ring_id>/<version>/", methods=["GET", "POST"])
@cross_origin(supports_credentials=True)
@api_key_check
def analysis(ring_id: str,
             version: str) -> Dict:
    """
    Runs the analysis specified by the SQR plan in the JSON of the request.
    :param ring_id: The ID of the ring.
    :type ring_id: str
    :param version: The ring version.
    :type version: str
    :return: A dictionary of the analysis results.
    :rtype: dict
    """

    # Get our ring and extractor
    ring = get_or_create_ring(ring_id, version)
    if type(ring) is tuple:
        # ring will now be an error message
        return json.dumps(ring)

    # Init the analysis engine
    analysis_engine = AnalysisEngine(ring)

    # The analysis plan come in via a JSON body
    raw_analysis_plan = request.json

    compiler = SQRCompiler(analysis_engine.plan_parser)

    # Parse the analysis plan
    analysis_plan = analysis_engine.plan_parser.parse(raw_analysis_plan)
    analysis_plan = compiler.compile(analysis_plan)

    # Run the analysis
    with closing(ring.db.session_maker()) as session:
        results = analysis_engine.sqr_single_ring_analysis(analysis_plan, ring, session)

    if "score" in results:
        results["score"] = results["score"]
    # this next line is a bit of a hack to deal with un-jsonable things by coercing them
    # to strings without having to write quick managers for every possible type (date, datetime, int64, etc)
    results = json.loads(json.dumps(results, default=str))
    # doing jsonify here manages the mimetype
    return jsonify(results)

@api.route("/extractor/<ring_id>/<version>/", methods=["GET", "POST"])
@api_key_check
def get_extracted_features(ring_id, version):
    """
    Extracts the features (entity, attributes, etc.) from a given utterance.
    This is mainly used for testing.
    :param ring_id:
    :type ring_id:
    :param version:
    :type version:
    :param utterance:
    :type utterance:
    :return:
    :rtype:
    """

    question_dict = request.json if request.content_type == "application/json" else {}

    if not question_dict:
        return "No question provided."

    # Init the ring
    ring = get_or_create_ring(ring_id, version)

    utterance = question_dict['question']

    # Determine the type of utterance we were given
    utterance_type = DocumentManager.determine_utterance_type(utterance)

    # Get the plans based on the utterance type
    if utterance_type == UtteranceType.Question or utterance == UtteranceType.InfoRequest:
        # need to flesh out this single-question branch
        return {"request_type": "question"}

    report_type = DocumentManager.determine_report_type(utterance)
    feature_extractor = FeatureExtractor(ring, DocumentManager.feature_extractor_lm)
    entity, filter_attribute, filter_value = report_type.parse(utterance, feature_extractor)

    return {"request_type": "report",
            "report_type": report_type.__name__,
            "entity": entity.name,
            "filter_attribute": filter_attribute.name if filter_attribute else "",
            "filter_value": str(filter_value)}

@api.route("/text_to_sqr/<ring_id>/<version>/", methods=["GET", "POST"])
@api_key_check
def get_sqr_from_questions(ring_id, version):
    """
    Generates the SQR corresponding to the given natural language question.
    :param ring_id:
    :type ring_id:
    :param version:
    :type version:
    :return:
    :rtype:
    """

    # Get the question out of the JSON body
    question_dict = request.json if request.content_type == "application/json" else {}

    if not question_dict:
        return "No plan provided."

    text_to_sqr_model = LlamaInterface("https://c3lablocalllm.work/v1/completions")

    if question_dict.get('compile', True):
        operation_ontology = OperationOntology()
        plan_parser = AnalysisPlanParser(operation_ontology)
        sqr_compiler = SQRCompiler(plan_parser)

        results = [sqr_compiler.compile(plan_parser.parse(plan)).to_json() for plan in text_to_sqr_model.question_to_sqr(question_dict['questions'])]
    else:
        results = text_to_sqr_model.question_to_sqr(question_dict['questions'])

    # doing jsonify here manages the mimetype
    return jsonify(results)

@api.route("/lang_gen/<ring_id>/<version>/", methods=["GET", "POST"])
@api_key_check
def generate_factual_statements(ring_id, version):
    """
    Generates a factual statement for the SQR plan provided in the JSON body.
    This is mainly used for testing.
    :param ring_id:
    :type ring_id:
    :param version:
    :type version:
    :return:
    :rtype:
    """

    # Get the question out of the JSON body
    plan_dict = request.json if request.content_type == "application/json" else {}

    if not plan_dict:
        return "No plans provided."
    ring = get_or_create_ring(ring_id, version)
    operation_ontology = OperationOntology()
    statement_generation_mode = GenerationMode.OneStatementPerRow
    # statement_generator = StatementGenerator(ring, operation_ontology, mode=statement_generation_mode)
    plan_parser = AnalysisPlanParser(operation_ontology)
    # plan = plan_parser.parse(plan_dict)
    # factual_statement_template = statement_generator.generate_statement_template_from_plan(plan)

    doc_manager = DocumentManager(ring, operation_ontology, statement_generation_mode=statement_generation_mode)

    # Perform the analysis
    plans_and_results = []
    for plan in plan_dict['plans']:
        try:
            plan = plan_parser.parse(plan)
            with closing(doc_manager.ring.db.session_maker()) as session:
                plans_and_results.append({'plan': plan, 'result': doc_manager.analysis_engine.sqr_single_ring_analysis(plan, doc_manager.ring, session)})
        except Exception as e:
            plans_and_results.append({'plan': None, 'result': None})

    for plan_and_result in plans_and_results:
        if plan_and_result['plan']:
            plan_and_result['plan'].result = plan_and_result['result']

    # Generate statement_templates and fill with results
    # Express these plans in natural language by generating a template where the results can be slotted in
    statement_templates = []
    for p in plans_and_results:
        try:
            statement_templates.append(doc_manager.plan_statement_generator.generate_statement_template_from_plan(p['plan']) if p['result'] else None)
        except:
            statement_templates.append(None)
    # statement_templates = [doc_manager.plan_statement_generator.generate_statement_template_from_plan(p['plan']) if p['result'] else None for p in plans_and_results]
    factual_statements = reduce(
        lambda a, plans_and_template: a + doc_manager.plan_statement_generator.fill_result(*plans_and_template),
        zip([p['plan'] for p in plans_and_results], statement_templates), [])

    # Clean the factual_statements by removing extra spaces
    text_factual_statements = [" ".join(f.split()) if f else 'Plan could not be executed.' for f in factual_statements]
    prompt_factual_statements = [" ".join(f.split()) for f in factual_statements if f]

    prompt = "Context:\n{}".format('\n'.join(prompt_factual_statements))
    prompt += "\n\nGenerate a report using only the facts provided in the context. "
    prompt += "The audience is educated, but may not understand technical terms. " \
              "Please use natural sounding language and try to find more natural terms for the groups that are mentioned. " \
              f"If the answer to \"{plan_dict['question']}\" is in the context, begin the report by answering this question in a separate paragraph."

    return {
        'facts': text_factual_statements,
        'prompt': prompt
    }

@api.route("/fact_gen/<ring_id>/<version>/", methods=["GET", "POST"])
@api_key_check
def get_factual_statements(ring_id, version):
    """
    Generates the set of factual statements given an entity, an attribute to filter on, and the filter values.
    This was used for building the index of facts.
    :param ring_id:
    :type ring_id:
    :param version:
    :type version:
    :return:
    :rtype:
    """

    # Get the request dictionary out of the JSON body
    request_dict = request.json if request.content_type == "application/json" else {}

    # Given a dict with:
    # {
    #     "entity": "<entity>",
    #     "filter_attribute": "<filter_attribute>",
    #     "filter_values": ["<id_1>", "<id_2>", ...]
    # }

    if not request_dict:
        return "No request provided."

    ring = get_or_create_ring(ring_id, version)
    operation_ontology = OperationOntology()
    statement_generation_mode = GenerationMode.OneStatementPerRow
    doc_manager = DocumentManager(ring, operation_ontology, statement_generation_mode=statement_generation_mode)

    # Pull out features from the request dictionary
    entity_name = request_dict["entity"]
    filter_attribute_name = request_dict["filter_attribute"]

    output = {}
    for filter_value in request_dict["filter_values"]:

        # Resolve the entity and attribute against the ring objects
        entity = [ent for ent in ring.entities if ent.name == entity_name][0]
        filter_attribute = entity.attributes[filter_attribute_name]

        # Define the information requirements
        info_requirements = [
            # EntityClassWithMetrics(entity),
            # EntityClassWithRelatedEntityMetrics(entity),
            # EntityInstanceCategories(entity, filter_attribute, filter_value),
            # EntityInstanceWithMetrics(entity, filter_attribute, filter_value),
            # EntityInstanceWithRelatedEntityMetrics(entity, filter_attribute, filter_value)
            # SubjectProperties(entity, filter_attribute, filter_value),
            # StayProperties(entity_name, filter_attribute_name, filter_value)
        ]

        # Generate the plans
        raw_plans = doc_manager.info_planner.get_raw_plans_from_requirements(info_requirements)
        plans = doc_manager.info_planner.generate_plans_from_raw_plans(raw_plans)

        # Express these plans in natural language by generating a template where their results can be slotted in
        full_plans = [(p, doc_manager.plan_statement_generator.generate_statement_template_from_plan(p)) for p in plans]

        # Get the factual statements by executing each plan and slotting the result into the language template
        factual_statements = []
        for plan_with_template in full_plans:
            factual_statements.extend(doc_manager.get_plan_execution_result(plan_with_template))

        # Store the results
        output[filter_value] = factual_statements

    return output

@api.route("/get_llm_response/", methods=["GET", "POST"])
@api_key_check
def get_llm_response():

    # Get the request dictionary out of the JSON body
    request_dict = request.json if request.content_type == "application/json" else {}

    # Given a dict with:
    # {
    #     "prompt": "<prompt>",
    #     "llm": <"gpt3.5" | "gpt4" | "mistral" | "mixtral" | "stablebeluga2" | "code_interpreter" | "none">
    #     "llm_url": "<url_to_mixtral_or_mistral_endpoint>",
    #     "ring_id": "<ring_id>"
    # }

    if not request_dict:
        return "No request provided."


    llm = GPT4TurboInterface()
    if 'llm' in request_dict and request_dict['llm'] == 'gpt3.5':
        llm = GPT35Interface()
    elif 'llm' in request_dict and request_dict['llm'] == 'stablebeluga2':
        llm = StableBelugaInterface()
    elif 'llm' in request_dict and request_dict['llm'] == 'mistral':
        if not request_dict['llm_url']:
            return "Please provide 'llm_url' for Mistral."
        llm = Mixtral8x7BInterface(request_dict['llm_url'])
    elif 'llm' in request_dict and request_dict['llm'] == 'mixtral':
        if not request_dict['llm_url']:
            return "Please provide 'llm_url' for Mixtral."
        llm = Mixtral8x7BInterface(request_dict['llm_url'])
    elif 'llm' in request_dict and 'ring_id' in request_dict and request_dict['llm'] == 'code_interpreter':
        ring = get_or_create_ring(request_dict['ring_id'], '1')
        llm = CodeInterpreterInterface(ring.name)
    elif 'llm' in request_dict and request_dict['llm'] == 'gpt4o-mini':
        llm = GPT4oMiniInterface()

    # Make the call to the language model
    return llm.generate(request_dict['prompt'])


@api.route("/question_gen/<ring_id>/<version>/", methods=["GET", "POST"])
@api_key_check
def generate_question(ring_id, version):
    """
    Generates a question for the SQR plan provided in the JSON body.
    This is used for testing. DO NOT MODIFY.
    """

    # Get the question out of the JSON body
    plan_dict = request.json if request.content_type == "application/json" else {}

    if not plan_dict:
        return "No plan provided."
    ring = get_or_create_ring(ring_id, version)
    operation_ontology = OperationOntology()
    # question_generator = QuestionGenerator(ring, operation_ontology)
    statement_generator = StatementGenerator(ring, operation_ontology)
    plan_parser = AnalysisPlanParser(operation_ontology)
    plan = plan_parser.parse(plan_dict)
    return statement_generator.question_generator.generate_question_from_plan(plan)

@api.route("/unittest_fact_gen_one_per_row/<ring_id>/<version>/", methods=["GET", "POST"])
@api_key_check
def unittest_generate_facts_one_per_row(ring_id, version):
    """
    Generates the factual statements for the SQR plan provided in the JSON body.
    This is used for testing. DO NOT MODIFY.
    """

    # Get the question out of the JSON body
    plan_dict = request.json if request.content_type == "application/json" else {}

    if not plan_dict:
        return "No plan provided."
    ring = get_or_create_ring(ring_id, version)
    operation_ontology = OperationOntology()
    statement_generation_mode = GenerationMode.OneStatementPerRow
    statement_generator = StatementGenerator(ring, operation_ontology, mode=statement_generation_mode)
    plan_parser = AnalysisPlanParser(operation_ontology)
    plan = plan_parser.parse(plan_dict)
    factual_statement_template = statement_generator.generate_statement_template_from_plan(plan)

    doc_manager = DocumentManager(ring, operation_ontology, statement_generation_mode=statement_generation_mode)
    return doc_manager.get_plan_execution_result((plan, factual_statement_template))

@api.route("/unittest_fact_gen_one_per_plan/<ring_id>/<version>/", methods=["GET", "POST"])
@api_key_check
def unittest_generate_facts_one_per_plan(ring_id, version):
    """
    Generates a question for the SQR plan provided in the JSON body.
    This is used for testing. DO NOT MODIFY.
    """

    # Get the question out of the JSON body
    plan_dict = request.json if request.content_type == "application/json" else {}

    if not plan_dict:
        return "No plan provided."
    ring = get_or_create_ring(ring_id, version)
    operation_ontology = OperationOntology()
    statement_generation_mode = GenerationMode.OneStatementPerPlan
    statement_generator = StatementGenerator(ring, operation_ontology, mode=statement_generation_mode)
    plan_parser = AnalysisPlanParser(operation_ontology)
    plan = plan_parser.parse(plan_dict)
    factual_statement_template = statement_generator.generate_statement_template_from_plan(plan)

    doc_manager = DocumentManager(ring, operation_ontology, statement_generation_mode=statement_generation_mode)
    return doc_manager.get_plan_execution_result((plan, factual_statement_template))


@api.route("/imp_plan/<ring_id>/<version>/", methods=["GET", "POST"])
@api_key_check
def test_improved_planning(ring_id, version):

    # Get the request dictionary out of the JSON body
    request_dict = request.json if request.content_type == "application/json" else {}

    # Given a dict with:
    # {
    #     "report_type": "<report_type>",
    #     "entity_name": "<entity_name>",
    #     "entity_instance_identifier_attribute_name": "<filter_attribute_name>",
    #     "entity_instance_identifier_value": "<filter_value>",
    #     "metric_entity_name": "<entity_name>",
    #     "metric_attribute_name": "<attribute_name>",
    #     "metric_aggregation": "<aggregation_operation>",
    #     "metric_preference_direction": <"+inf", "-inf">,
    #     "metric_sort_direction": <"desc", "asc">,
    #     "metric_set_filter": "<dict with SQR filters>",
    #     "statement_generation_method": <"template" | "table" | "recursive">,
    #     "prompt_type": <"baseline" | "baseline_with_reqs" | "baseline_with_facts">
    #     "llm": <"gpt3.5" | "gpt4" | "mistral" | "mixtral" | "stablebeluga2" | "code_interpreter" >
    #     "llm_url": "<url_to_mixtral_or_mistral_endpoint>"
    # }

    if not request_dict:
        return "No request provided."

    ring = get_or_create_ring(ring_id, version)
    operation_ontology = OperationOntology()
    llm = None
    if 'llm' in request_dict and request_dict['llm'] == 'gpt4':
        llm = GPT4Interface()
    elif 'llm' in request_dict and request_dict['llm'] == 'gpt3.5':
        llm = GPT35Interface()
    elif 'llm' in request_dict and request_dict['llm'] == 'stablebeluga2':
        llm = StableBelugaInterface()
    elif 'llm' in request_dict and request_dict['llm'] == 'mistral':
        if not request_dict['llm_url']:
            return "Please provide 'llm_url' for Mistral."
        llm = Mixtral8x7BInterface(request_dict['llm_url'])
    elif 'llm' in request_dict and request_dict['llm'] == 'mixtral':
        if not request_dict['llm_url']:
            return "Please provide 'llm_url' for Mixtral."
        llm = Mixtral8x7BInterface(request_dict['llm_url'])
    elif 'llm' in request_dict and request_dict['llm'] == 'code_interpreter':
        llm = CodeInterpreterInterface(ring.name)
    doc_manager = DocumentManager(ring,
                                  operation_ontology,
                                  statement_generation_mode=GenerationMode.OneStatementPerPlan,
                                  language_model=llm,
                                  plan_statement_generator=StatementGeneratorTemplateBased if request_dict['statement_generation_method'] == 'template' else StatementGenerator)
    sqr_composer = SQRComposer(ring, operation_ontology)

    # Extract some directions used in the reports
    metric_sort_direction = 'desc'
    if 'metric_sort_direction' in request_dict:
        metric_sort_direction = "asc" if request_dict['metric_sort_direction'] == 'asc' else 'desc'

    metric_preference_direction = '+inf'
    if 'metric_preference_direction' in request_dict:
        metric_preference_direction = "-inf" if request_dict['metric_preference_direction'] == '-inf' else '+inf'

    def get_entity_reference(entity_name: str,
                             entity_instance_identifier_attribute_name: str,
                             entity_instance_identifier_value: str) -> str:
        entity = ring.get_entity_by_name(entity_name)
        if entity.reference and ArgType.Identifier in entity.attributes[entity_instance_identifier_attribute_name].type:
            return doc_manager.plan_statement_generator.step_expressor.fill_reference_template(entity_name,
                                                                                               entity_instance_identifier_attribute_name,
                                                                                               entity_instance_identifier_value,
                                                                                               entity.reference)
        else:
            return request_dict['entity_instance_identifier_value']

    # Pull out features from the request dictionary
    report_type = eval(request_dict['report_type'])
    # Report Type: Performance Report
    # report = report_type(request_dict['entity_name'], request_dict['filter_attribute_name'], request_dict['filter_value'], entity_cohorts=[])

    # Determine the entity reference for the target entity
    entity_reference = get_entity_reference(request_dict['entity_name'],
                                            request_dict['entity_instance_identifier_attribute_name'],
                                            request_dict['entity_instance_identifier_value'])

    metric_set_filter = request_dict['metric_set_filter'] if 'metric_set_filter' in request_dict else {}

    if report_type == RankingBlueprint:
        report = report_type(request_dict['entity_name'],
                             request_dict['entity_instance_identifier_attribute_name'],
                             request_dict['entity_instance_identifier_value'],
                             entity_reference,
                             request_dict['metric_entity_name'],
                             request_dict['metric_attribute_name'],
                             request_dict['metric_aggregation'],
                             metric_set_filter,
                             metric_preference_direction,
                             ring,
                             metric_sort_direction = metric_sort_direction)
    elif report_type == ComparativeBenchmarkBlueprint:
        report = report_type(request_dict['entity_name'],
                             request_dict['entity_instance_identifier_attribute_name'],
                             request_dict['entity_instance_identifier_value'],
                             entity_reference,
                             request_dict['metric_entity_name'],
                             request_dict['metric_attribute_name'],
                             request_dict['metric_aggregation'],
                             metric_set_filter,
                             metric_preference_direction,
                             ring,
                             benchmark_target = request_dict['benchmark_target'])
    elif report_type == TimeOverTimeBlueprint:
        report = report_type(request_dict['entity_name'],
                             request_dict['entity_instance_identifier_attribute_name'],
                             request_dict['entity_instance_identifier_value'],
                             entity_reference,
                             request_dict['metric_entity_name'],
                             request_dict['metric_attribute_name'],
                             request_dict['metric_aggregation'],
                             metric_set_filter,
                             metric_preference_direction,
                             ring,
                             time_attribute_name = request_dict['time_attribute_name'],
                             time_zero = request_dict['time_zero'],
                             time_one = request_dict['time_one'])
    else:
        raise ValueError(f"Unknown report type being requested: {request_dict['report_type']}")

    # Get the list of {"plan_name": ..., "base_plan": ..., "access_plans": ..., "slot_fillers": ...}
    composition_specs = report.get_plan_composition_specs()

    # Remove any empty access plan filters from the composition specs
    for spec in composition_specs:
        spec.clean()

    # Generate the plans and gather useful metadata for generating factual statements
    plans_and_metadata = []
    for spec in composition_specs:
        # Gather all the info
        composed_plan, slots_to_ref = sqr_composer.compose(spec)
        base_plan_name = spec.base_plan_name
        slot_fillers = spec.slot_fillers

        # Gather the info
        plans_and_metadata.append({
            "plan": composed_plan,
            "base_plan_name": base_plan_name,
            "slot_fillers": slot_fillers,
            "slots_to_ref": slots_to_ref,
            "results": None
        })

    # Perform the analysis
    with closing(doc_manager.ring.db.session_maker()) as session:
        all_results = [doc_manager.analysis_engine.sqr_single_ring_analysis(plan['plan'], doc_manager.ring, session) for plan in plans_and_metadata]

    for plan, result in zip(plans_and_metadata, all_results):
        plan['results'] = result
        plan['plan'].result = result

    # Generate statement_templates and fill with results
    if request_dict['statement_generation_method'] == 'recursive':
        # Express these plans in natural language by generating a template where the results can be slotted in
        statement_templates = [doc_manager.plan_statement_generator.generate_statement_template_from_plan(p['plan']) for p in plans_and_metadata]
        factual_statements = reduce(
            lambda a, plans_and_template: a + doc_manager.plan_statement_generator.fill_result(*plans_and_template),
            zip([p['plan'] for p in plans_and_metadata], statement_templates), [])

        # Clean the factual_statements by removing extra spaces
        factual_statements = [" ".join(f.split()) for f in factual_statements]

    elif request_dict['statement_generation_method'] == 'table':
        # Express the results of these plans as a table of results
        factual_statements = []
        for p in plans_and_metadata:
            # Build the table that will comprise one of the factual statements
            x = PrettyTable()
            x.field_names = p['results']['fieldNames']
            x.add_rows(p['results']['results'])

            # Save the factual statement
            factual_statements.append(str(x))

    else:
        # Express these plans in natural language by using a stored template where the results can be slotted in
        base_plan_store = BasePlanStore()
        factual_statements = [doc_manager.plan_statement_generator.generate_statement(base_plan_store.templates[p['base_plan_name']]['statement_templates'][0],
                                                                                      p['results'],
                                                                                      p['slot_fillers'],
                                                                                      p['plan'],
                                                                                      metric_set_filter) for p in plans_and_metadata]

        # Clean the factual_statements by removing extra spaces
        factual_statements = [" ".join(f.split()) for f in factual_statements]

    # Generate prompt that can be used for generation
    def get_filter_statement(filter_steps: Dict[str, str]) -> str:
        # Parse in raw filter steps from the API endpoint (metric_set_filter from the request_dict) into an AnalysisPlan
        filter_plan = doc_manager.analysis_engine.plan_parser.parse_plan_snippet(filter_steps)

        # Get the reference of the final filter step
        final_step_ref = filter_plan.get_leaves()[0]

        # Call the step_expressor to express the filter step in natural language
        filter_statement = "for " + doc_manager.plan_statement_generator.step_expressor.express_filter_step(final_step_ref, filter_plan)

        return filter_statement

    filter_statement = get_filter_statement(metric_set_filter) if metric_set_filter else ""
    prompt_type = request_dict["prompt_type"] if "prompt_type" in request_dict else "baseline_with_facts"
    if prompt_type == 'baseline':
        prompt = report.build_baseline_prompt(entity_reference, filter_statement)
    elif prompt_type == 'baseline_with_reqs':
        prompt = report.build_baseline_prompt_with_info_reqs(entity_reference, filter_statement)
    else:
        prompt = report.build_baseline_prompt_with_facts(entity_reference, filter_statement, factual_statements)

    if llm:
        # Produce reports using the LLM conditioned on the factual statements
        report = doc_manager.language_model.generate(prompt)
    else:
        # Produce reports consisting of just the factual statements concatenated together
        report = " ".join(factual_statements)

    output = {
        'plans': [p['plan'].to_json() for p in plans_and_metadata],
        'facts': factual_statements,
        'prompt': prompt,
        'report': report
    }

    return output

@api.route("/unittest_sqr_compose/<ring_id>/<version>/", methods=["GET", "POST"])
@api_key_check
def unittest_sqr_composition(ring_id, version):
    # Get the request dictionary out of the JSON body
    request_dict = request.json if request.content_type == "application/json" else {}

    # Given a dict with:
    # {
    #     "access_plan": {...},
    #     "base_plan": {...},
    #     "slot_fillers": {"<slot:0>": "<filler_value>", ...},
    #     "target_plan": {...}
    # }

    if not request_dict:
        return "No request provided."

    # Init various required objects
    ring = get_or_create_ring(ring_id, version)
    operation_ontology = OperationOntology()
    sqr_composer = SQRComposer(ring, operation_ontology)
    analysis_engine = AnalysisEngine(ring)
    plan_filler = SQRPlanFiller(ring)

    # Parse the raw plans into AnalysisStep objects
    access_plan_steps = analysis_engine.plan_parser.create_analysis_steps(request_dict['access_plan'])
    base_plan_steps = analysis_engine.plan_parser.create_analysis_steps(request_dict['base_plan'])
    target_plan_steps = analysis_engine.plan_parser.create_analysis_steps(request_dict['target_plan'])

    # Fill in the plans with the specified slot fillers
    access_plan_steps = plan_filler.fill_plan(access_plan_steps, request_dict['slot_fillers'])
    base_plan_steps = plan_filler.fill_plan(base_plan_steps, request_dict['slot_fillers'])
    target_plan_steps = plan_filler.fill_plan(target_plan_steps, request_dict['slot_fillers'])

    # Compose the plan
    composed_plan_steps = sqr_composer.compose_access_plans_and_base_plan(base_plan_steps, access_plan_steps)

    # Create the AnalysisPlan objects which will be executed by the AnalysisEngine
    composed_plan = analysis_engine.plan_parser.parse_from_analysis_steps(composed_plan_steps)
    target_plan = analysis_engine.plan_parser.parse_from_analysis_steps(target_plan_steps)

    # Run the analysis
    with closing(ring.db.session_maker()) as session:
        composed_plan_results = analysis_engine.sqr_single_ring_analysis(composed_plan, ring, session)
    with closing(ring.db.session_maker()) as session:
        target_plan_results = analysis_engine.sqr_single_ring_analysis(target_plan, ring, session)

    # this next line is a bit of a hack to deal with un-jsonable things by coercing them
    # to strings without having to write quick managers for every possible type (date, datetime, int64, etc)
    composed_plan_results = json.loads(json.dumps(composed_plan_results, default=str))
    target_plan_results = json.loads(json.dumps(target_plan_results, default=str))

    # print(composed_plan.to_json())
    # print(composed_plan_results)
    # print(target_plan_results)

    return {
        "composed_plan": composed_plan.to_json(),
        "composed_plan_results": composed_plan_results,
        "target_plan_results": target_plan_results
    }

@api.route("/generate_composition_specs/<ring_id>/<version>/", methods=["GET", "POST"])
@api_key_check
def generate_composition_specs(ring_id, version):

    # Get the request dictionary out of the JSON body
    request_dict = request.json if request.content_type == "application/json" else {}

    if not request_dict:
        return "No request provided."

    # Load the ring and SQR composer
    ring = get_or_create_ring(ring_id, version)
    operation_ontology = OperationOntology()
    sqr_composer = SQRComposer(ring, operation_ontology)
    base_plan_store = BasePlanStore()
    plan_generator = PlanGenerator(ring, operation_ontology, sqr_composer, base_plan_store)

    # Generate the set of plans
    access_plans_and_questions = []
    base_plans_and_questions = []
    if request_dict["use_access_plans"]:
        access_plans_and_questions.extend(plan_generator.generate_with_access_plans(request_dict["desired_entities"], request_dict["num_filters"]))
    if request_dict["use_base_plans"]:
        base_plans_and_questions.extend(plan_generator.generate_with_base_plans(request_dict["desired_entities"], [request_dict["target_base_plan"]], request_dict["num_filters"]))

    # Calculate some statistics about the generations
    info = {
        "num_access_plans": len(access_plans_and_questions),
        "num_base_plans": len(base_plans_and_questions),
        "num_access_plan_questions": 0,
        "num_base_plan_questions": 0
    }
    for plan_and_questions in access_plans_and_questions:
        info["num_access_plan_questions"] += len(plan_and_questions["questions"])
    for plan_and_questions in base_plans_and_questions:
        info["num_base_plan_questions"] += len(plan_and_questions["questions"])
    info["total_plans"] = info["num_access_plans"] + info["num_base_plans"]
    info["total_questions"] = info["num_access_plan_questions"] + info["num_base_plan_questions"]

    # Make the final dictionary
    # TODO: Add in "base_plan_name": plan_and_spec['spec'].base_plan_name, for each of the base plan generations?
    all_plans_and_questions = access_plans_and_questions + base_plans_and_questions
    final_output = {
        "info": info,
        "plans_and_questions": [{
            "plan": pq["plan"].to_json(),
            "questions": pq["questions"],
            "ring_id": ring_id,
            "base_plan": pq["base_plan"]
        } for pq in all_plans_and_questions]
    }

    print(json.dumps(final_output, indent=4))

    # Save the generated plans/questions to the specified file location
    final_file_path = request_dict["file_save_location"]
    if request_dict["use_access_plans"]:
        final_file_path += "AccessPlans_"
    if request_dict["use_base_plans"]:
        final_file_path += request_dict["target_base_plan"] + "_"
    final_file_path += ring_id + ".json"
    with open(final_file_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(final_output, indent=4))

    return final_output

@api.route("/generate_question/<ring_id>/<version>/", methods=["GET", "POST"])
@api_key_check
def generate_question_with_template(ring_id, version):
    # Get the request dictionary out of the JSON body
    request_dict = request.json if request.content_type == "application/json" else {}

    # Given a dict with:
    # {
    #       "base_plan_template_name": "<string>",
    #       "slot_fillers": { "<slot_name>": "<slot_value>" },
    #       "metric_filler_name: "<string>",
    #       "analysis_plan": {"|1|": ... , "|2|": ..., ...},
    #       "filter_steps_for_postfix": {...}
    # }

    if not request_dict:
        return "No request provided."

    from satyrn.core.Planning.QuestionGeneratorTemplateBased import QuestionGeneratorTemplateBased
    ring = get_or_create_ring(ring_id, version)
    question_generator = QuestionGeneratorTemplateBased()
    question = question_generator.generate_question(request_dict['base_plan_template_name'],
                                                    request_dict['slot_fillers'],
                                                    request_dict['metric_filler_name'],
                                                    request_dict['analysis_plan'],
                                                    request_dict['filter_steps_for_postfix'])

    return {"generated_question": question}

@api.route("/rephrase_question/", methods=["GET", "POST"])
@api_key_check
def rephrase_question():
    # Get the request dictionary out of the JSON body
    request_dict = request.json if request.content_type == "application/json" else {}

    # Given a dict with:
    # {
    #     "question": "<question_string>"
    #      optional:
    #       "prompt_type": "<str for type of prompting>"
    #       "query": "<query_string>"
    # }

    if not request_dict:
        return "No request provided."
    
    # print(request_dict)
    # assume GPT rephraser
    # TODO: add param to specify rephrasing method
    # from satyrn.core.Planning.QuestionRephrasing.QuestionRephraser import QuestionRephraser
    from satyrn.core.Planning.QuestionRephrasing.GPTQuestionRephraser import GPTQuestionRephraser

    # question_rephraser = QuestionRephraser()
    # questions = question_rephraser.rephrase(request_dict['question'])
    
    question_rephraser = GPTQuestionRephraser(request_dict.get("prompt_type", "question_only"))
    if request_dict.get("ring_id", None):
        request_dict["ring"] = get_or_create_ring(request_dict["ring_id"], version=1)
    question = question_rephraser.rephrase(**request_dict)
    return { "rephrased_question": question}

@api.route("/question_space/<ring_id>/<version>/", methods=["GET", "POST"])
@api_key_check
def generate_question_space(ring_id, version):

    # Get the request dictionary out of the JSON body
    request_dict = request.json if request.content_type == "application/json" else {}

    if not request_dict:
        return "No request provided."

    from satyrn.core.Planning.Contextualization.QuestionSpaceGenerator import QuestionSpaceGenerator
    ring = get_or_create_ring(ring_id, version)
    operation_ontology = OperationOntology()
    base_plan_store = BasePlanStore()
    space_generator = QuestionSpaceGenerator(ring, operation_ontology, base_plan_store)

    # Generate the question space
    questions = space_generator.generate_space(request_dict["desired_entities"],
                                               request_dict["desired_base_plans"])

    # Build the final output dictionary
    output_dict = {
        "num_questions": len(questions),
        "questions": questions
    }

    return output_dict

@api.route("/contextualize/<ring_id>/<version>/", methods=["GET", "POST"])
@api_key_check
def contextualize(ring_id, version):

    # Get the request dictionary out of the JSON body
    request_dict = request.json if request.content_type == "application/json" else {}

    if not request_dict:
        return "No request provided."

    # Process the input
    target_question = request_dict["question"]
    num_contextual_questions = request_dict.get("num_contextual_questions", 5)

    # Init important objects
    ring = get_or_create_ring(ring_id, version)
    operation_ontology = OperationOntology()
    base_plan_store = BasePlanStore()

    desired_entities = request_dict.get("desired_entities", [])
    desired_base_plans = request_dict.get("desired_base_plans", [])
    mode = request_dict.get("mode", "generate_from_entities")

    question_contextualizer = QuestionContextualizer(ring, operation_ontology, base_plan_store)

    if mode == "question_space":
        # Generate the space of questions that can likely be answered by the question
        question_space = question_contextualizer.question_space_generator.generate_space(desired_entities, desired_base_plans)
        print(question_space)

        # Pick the top 5 that are most relevant to the given question
        most_relevant_questions = question_contextualizer.get_relevant_questions(target_question, question_space, limit=num_contextual_questions)
        print(most_relevant_questions)

        # Adapt those questions to the specifics of the given question
        adapted_questions = question_contextualizer.adapt_questions(target_question, most_relevant_questions)
        print(adapted_questions)

        return {
            "contextual_questions": adapted_questions,
            "relevant_general_questions": most_relevant_questions,
            "question_space": question_space
        }

    elif mode == "generate_from_entities":
        questions = question_contextualizer.generate_relevant_questions_with_entities_and_attributes(target_question,
                                                                                                     limit=num_contextual_questions)

        return {
            "contextual_questions": questions
        }

    else:
        raise ValueError(f"Unknown contextualization mode: {mode}")

@api.route("/sqr_to_sql/<ring_id>/<version>/", methods=["GET", "POST"])
@api_key_check
def convert_to_sql(ring_id, version):
    """
    Given a dict that is the raw SQR plan:
    {
        "|1|": (retrieve_entity ...),
        ...
    }
    """

    # Get the request dictionary out of the JSON body
    request_dict = request.json if request.content_type == "application/json" else {}

    if not request_dict:
        return "No request provided."

    # Parse the inputs
    raw_analysis_plan = request_dict

    # Init important objects
    from satyrn.core.Planning.PlanGeneration.SQLConverter import SQLConverter
    ring = get_or_create_ring(ring_id, version)
    sql_converter = SQLConverter()

    # Convert the SQR plan to SQR
    sql_query_string = sql_converter.convert_to_sql(raw_analysis_plan, ring, clean_aliases=True)
    sql_query_string_original_aliases = sql_converter.convert_to_sql(raw_analysis_plan, ring, clean_aliases=False)
    return { "sql": sql_query_string, "sql_original_aliases": sql_query_string_original_aliases }

# timeout for long-running calls on very complex queries?
# @timeout(10)
@api.route("/simplify_sql/<ring_id>/<version>/", methods=["GET", "POST"])
@api_key_check
def simplify_sql(ring_id, version):
    """
    Given a dict containing a SQL query:
    {
        "sql": "<query>"
    }
    """
    # Get the request dictionary out of the JSON body
    request_dict = request.json if request.content_type == "application/json" else {}

    if not request_dict:
        return "No request provided."


    # Init important objects
    from satyrn.core.Planning.PlanGeneration.SQLSimplifier import SQLSimplifier
    ring = get_or_create_ring(ring_id, version)
    sql_simplifier = SQLSimplifier()
    simplified_sql = sql_simplifier.simplify_sql(request_dict.get("sql"))
    return { "sql": request_dict.get("sql"), "sql_simplified": simplified_sql}


@api.route("/generate_plans/<ring_id>/<version>/", methods=["GET", "POST"])
@api_key_check
def generate_plans(ring_id, version):

    # Get the request dictionary out of the JSON body
    request_dict = request.json if request.content_type == "application/json" else {}

    if not request_dict:
        return "No request provided."

    # timeout_seconds = request_dict.get("timeout_seconds")
    timeout_seconds = 30
    # timeout_seconds = None
    if timeout_seconds:
        # Use fork so the child inherits the Flask app state (rings/cache) without rehydration.
        ctx = multiprocessing.get_context("fork")
        output_queue = ctx.Queue(maxsize=1)
        worker = ctx.Process(
            target=_generate_plans_payload_process,
            args=(ring_id, version, request_dict, output_queue),
        )
        worker.start()
        worker.join(timeout_seconds)
        if worker.is_alive():
            worker.terminate()
            worker.join()
            return {"plans_and_questions": []}
        if output_queue.empty():
            return {"plans_and_questions": []}
        return output_queue.get()
    else:
        if not app.plan_generator or app.plan_generator.ring.id != ring_id:
            # Load the ring and SQR composer
            ring = get_or_create_ring(ring_id, version)
            operation_ontology = OperationOntology()
            sqr_composer = SQRComposer(ring, operation_ontology)
            base_plan_store = BasePlanStore()
            cache_manager = CacheManager(ring, max_items=200, max_values_per_item=500)
            app.plan_generator = PlanGenerator(ring, operation_ontology, sqr_composer, base_plan_store, cache_manager)

        plans_and_questions = _generate_plans_internal(app.plan_generator, request_dict)

    # Make the final dictionary
    final_output = {
        "plans_and_questions": [{
            "plan": pq["plan"].to_json() if pq["plan"] else None,
            "questions": pq["questions"],
            "ring_id": ring_id,
            "base_plan": pq["base_plan"],
            "source": pq["source"],
            "access_plans": pq["access_plans"] if "access_plans" in pq else {},
            "sql": pq["sql"] if "sql" in pq else None,
        } for pq in plans_and_questions]
    }

    # print(json.dumps(final_output, indent=4))
    print(f"Generated {len(final_output['plans_and_questions'])} plans.")

    return final_output

@api.route("/compile_sqr/<version>/", methods=["GET", "POST"])
@api_key_check
def compile_sqr(version):
    """
    Given a dict that is the raw SQR plan:
    {
        "|1|": (retrieve_entity ...),
        ...
    }
    """

    # Get the request dictionary out of the JSON body
    request_dict = request.json if request.content_type == "application/json" else {}

    if not request_dict:
        return "No request provided."

    # Parse the inputs
    raw_analysis_plan = request_dict

    # Init important objects
    from satyrn.core.Planning.SQRCompiler import SQRCompiler
    operation_ontology = OperationOntology()
    plan_parser = AnalysisPlanParser(operation_ontology)
    sqr_compiler = SQRCompiler(plan_parser)

    # Convert the SQR plan to SQR
    compiled_sqr_plan = sqr_compiler.compile(plan_parser.parse(raw_analysis_plan), True)
    return compiled_sqr_plan.to_json()

@api.route("/get_base_plans/", methods=["GET", "POST"])
@api_key_check
def get_base_plans():
    base_plan_store = BasePlanStore()
    return base_plan_store.templates

@api.route("/generate_filter/", methods=["GET", "POST"])
@api_key_check
def generate_filter():
    # Get the request dictionary out of the JSON body
    request_dict = request.json if request.content_type == "application/json" else {}

    if not request_dict:
        return "No request provided."

    # Init the important objects
    from satyrn.core.Planning.PlanGeneration.FilterGenerator import FilterGenerator
    ring = get_or_create_ring(request_dict["ring_id"], "1")
    operation_ontology = OperationOntology()
    filter_generator = FilterGenerator(ring, operation_ontology)

    # Get the entity and attribute from the ring
    ring_entity = ring.get_entity_by_name(request_dict["entity"])
    # ring_attr = ring_entity.attributes[request_dict["attribute"]]

    filter_steps = filter_generator.build_filter_with_entity(ring_entity,
                                                             request_dict["min_atomic_filters"],
                                                             request_dict["max_atomic_filters"])

    return {k: str(v) for k, v in filter_steps.items()}

@api.route("/get_ring_ents_attrs/<ring_id>/<version>/", methods=["GET", "POST"])
@api_key_check
def get_ring_ents_attrs(ring_id, version):
    ring = get_or_create_ring(ring_id, version)
    return {
        "ents_and_attrs": ring.get_entities_and_attributes_string()
    }
