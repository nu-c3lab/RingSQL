import json, os, time
from satyrn.core.Planning.PlanManager import PlanManager
from satyrn.core.Planning.QuestionGenerator import QuestionGenerator
from satyrn.core.RingCompiler import compile_rings
from satyrn.core.Analysis.OperationOntology import OperationOntology

version = 1

if os.environ.get("SATYRN_SITE_CONFIG"):
    with open(os.environ.get("SATYRN_SITE_CONFIG")) as f:
        site_conf = json.load(f)

operation_ontology = OperationOntology()
rings, _ = compile_rings(site_conf.get("rings", []), operation_ontology=operation_ontology)

# Init the operation ontology
ontology = OperationOntology()

for ring_id in rings:

    ring = rings[ring_id][version]

    # Init the plan manager
    plan_manager = PlanManager(ring, ontology)

    # Generate the plans
    print('Generating Plans')
    raw_plans, plans = plan_manager.generate()

    question_generator = QuestionGenerator(ring, ontology)

    print('Generating Questions')
    questions = []
    for i, plan in enumerate(plans):
        print(i+1, '/', len(plans))
        time.sleep(5)
        questions.append(question_generator.generate_question_from_plan(plan))
    # questions = [question_generator.generate_question_from_plan(plan) for plan in plans]

    # Format and return the results
    with open(f'{ring_id}_questions.json', 'w') as outfile:
        json.dump({
                "plan_templates": raw_plans,
                "plans": plans,
                "questions": questions
            }, outfile, default=str, indent=4)
