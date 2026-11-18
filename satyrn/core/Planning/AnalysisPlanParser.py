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


import re
import shlex
import networkx as nx
from ast import literal_eval
from typing import Dict, List
from satyrn.core.Analysis.OperationOntology import OperationOntology
from satyrn.core.Analysis.AnalysisPlan import AnalysisPlan
from satyrn.core.Analysis.AnalysisStep import AnalysisStep
from satyrn.core.Analysis.AnalysisSubplan import AnalysisSubplan

from satyrn.core.api import utils

class AnalysisPlanParser:
    def __init__(self,
                 operation_ontology: OperationOntology):
        self.operation_ontology = operation_ontology

    def parse(self,
              raw_analysis_plan: dict) -> AnalysisPlan:
        """
        Converts the given analysis plan in dictionary form into an AnalysisPlan object.
        :param raw_analysis_plan: The raw analysis plan which maps step refs to SQR operations.
        :type raw_analysis_plan: dict
        :return: The given plan as an AnalysisPlan object
        :rtype: AnalysisPlan
        """
        plan_steps = self.create_analysis_steps(raw_analysis_plan)
        return self.parse_from_analysis_steps(plan_steps)

    def parse_from_analysis_steps(self,
                                  plan_steps: Dict[str, AnalysisStep]) -> AnalysisPlan:
        """
        Converts the given plan steps into an AnalysisPlan object.
        :param plan_steps: A dictionary mapping step refs to AnalysisStep objects.
        :type plan_steps: dict[str, AnalysisStep]
        :return: The given steps as an AnalysisPlan object
        :rtype: AnalysisPlan
        """
        plan_graph = self.create_plan_graph(plan_steps)
        subplans = self.determine_subplans(plan_steps, plan_graph)
        return AnalysisPlan(plan_steps, plan_graph, subplans)

    def parse_plan_snippet(self,
                           raw_analysis_plan: dict) -> AnalysisPlan:
        """
        Converts the given analysis plan snippet in dictionary form into an AnalysisPlan object.
        :param raw_analysis_plan: The raw analysis plan snippet which maps step refs to SQR operations.
        :type raw_analysis_plan: dict
        :return: The given plan snippet as an AnalysisPlan object
        :rtype: AnalysisPlan
        """
        plan_steps = self.create_analysis_steps(raw_analysis_plan)
        plan_graph = self.create_plan_graph(plan_steps)
        return AnalysisPlan(plan_steps, plan_graph, {})

    def parse_plan_snippet_from_analysis_steps(self,
                                               plan_steps: Dict[str, AnalysisStep]) -> AnalysisPlan:
        """
        Converts the given plan steps (which may not be a full SQR plan) into an AnalysisPlan object.
        :param plan_steps: A dictionary mapping step refs to AnalysisStep objects.
        :type plan_steps: dict[str, AnalysisStep]
        :return: The given steps as an AnalysisPlan object
        :rtype: AnalysisPlan
        """
        plan_graph = self.create_plan_graph(plan_steps)
        return AnalysisPlan(plan_steps, plan_graph, {})

    def create_analysis_steps(self,
                              raw_analysis_plan: Dict[str, str]) -> Dict[str, AnalysisStep]:

        def get_literal_arg(arg):
            try:
                return literal_eval(arg)
            except:
                return arg

        # Map the step index to a list of ops/args for that step
        d = {}
        for k, v in raw_analysis_plan.items():
            stripped = re.fullmatch(r'\((.*)\)', v.strip()).group(1) # Remove outer parentheses
            lst = shlex.split(stripped)     # Note: The shlex.split preserves substrings surrounded by quotes
            if self.operation_ontology.is_boolean_operation(lst[0]):
                # Preserve quotes if this is a boolean operation step
                lst = shlex.split(stripped, posix=False)
            d[k] = {
                "op": lst[0],
                "args": [get_literal_arg(arg) for arg in lst[1:]]
                # "args": lst[1:] # NOTE: Added this at some point to fix a bug, but was itself causing a bug (in case the original bug comes up again).
            }

        # Create each of the AnalysisStep objects
        plan_steps = {step_ref: AnalysisStep(step_ref, op_dict['op'], op_dict['args']) for step_ref, op_dict in d.items()}

        return plan_steps

    def create_plan_graph(self,
                          steps: Dict[str, AnalysisStep],
                          allow_broken_refs: bool = False) -> nx.DiGraph:
        # Init the graph
        G = nx.DiGraph()

        # Add each step to the graph
        for step_ref, step in steps.items():
            G.add_node(step_ref, data=step)

        # Add the links between each of the steps in the graph
        for step_ref, step in steps.items():
            for parent in self.get_parents(step, steps, allow_broken_refs):
                G.add_edge(parent.ref, step_ref)  # Edge from the parent to the child (i.e. the current step)

        return G

    def get_leaves(self,
                   plan_graph: nx.DiGraph) -> List[str]:
        """
        Get the leaf nodes of the plan graph.
        :param plan_graph:
        :type plan_graph:
        :return: A list of step references (e.g. ['|7|']).
        :rtype: list of str
        """
        return [node for node in plan_graph.nodes if plan_graph.out_degree(node) == 0]

    def determine_subplans(self,
                           plan_steps: Dict[str, AnalysisStep],
                           plan_graph: nx.DiGraph) -> Dict[str, AnalysisSubplan]:
        # TODO: Figure out which parts of the incoming plan are individual subqueries and what the hierarchical structure of it is

        leaf_ref = self.get_leaves(plan_graph)[0]
        leaf = plan_steps[leaf_ref]
        subplan_dict, _ = self.split_on_returns(leaf, plan_steps, {})

        # Remove duplicate subplans
        deduped_subplan_dict = {}
        for alias, subplan in subplan_dict.items():
            if subplan not in deduped_subplan_dict.values():
                deduped_subplan_dict[alias] = subplan

        # Convert the values in the dictionary to AnalysisSubplan objects
        return {k: AnalysisSubplan(v) for k, v in deduped_subplan_dict.items()}

    def split_on_returns(self,
                         start_node: AnalysisStep,
                         all_steps: dict,
                         subplan_steps: dict,
                         alias_idx: int = 0) -> dict:
        if not (self.operation_ontology.is_return_operation(start_node.operation) or self.operation_ontology.is_set_operation(start_node.operation)):
            raise Exception("Error: plan does not end with return or set operation!")
        new_plan_dict = {start_node.ref: start_node}

        stack = self.get_parents(start_node, all_steps)
        explored = [start_node.ref]
        while stack:
            node = stack.pop()
            if node.ref not in explored:
                if self.operation_ontology.is_return_operation(node.operation) or self.operation_ontology.is_set_operation(node.operation):
                    subplan_steps, alias_idx = self.split_on_returns(node, all_steps, subplan_steps, alias_idx)
                else:
                    new_plan_dict[node.ref] = node
                    stack.extend(self.get_parents(node, all_steps))
            explored.append(node.ref)
        subplan_steps[f'alias_{alias_idx}'] = new_plan_dict
        return subplan_steps, alias_idx + 1

    def get_parents(self,
                    step: AnalysisStep,
                    all_steps: Dict[str, AnalysisStep],
                    allow_broken_refs: bool = False) -> List[AnalysisStep]:

        def arg_is_parent_ref(idx_and_arg: tuple):
            idx, arg = idx_and_arg
            if utils.is_arg_reference(arg):
                if step.operation == 'retrieve_attribute':
                    if idx == 0:
                        if allow_broken_refs and arg not in all_steps:
                            return False
                        return True
                    return False
                if self.operation_ontology.is_set_operation(step.operation):
                    if allow_broken_refs and arg not in all_steps:
                        return False
                    return True
                if step.operation == 'in':
                    if idx == 1 and allow_broken_refs and arg not in all_steps:
                        return False
                if step.operation == 'exists':
                    if allow_broken_refs and arg not in all_steps:
                        return False
                return True
            return False

        # Get the references in this step's arguments
        parent_references = filter(arg_is_parent_ref, enumerate(step.args))
        # parent_references = filter(lambda idx_and_arg: utils.is_arg_reference(idx_and_arg[1]) and (step.operation != 'retrieve_attribute' or idx_and_arg[0] == 0), enumerate(step.args))

        # Retrieve those steps
        return [all_steps[idx_and_ref[1]] for idx_and_ref in parent_references]

    def is_arg_alias(self,
                     arg: str) -> bool:
        """
        Checks if the given arg is an alias for a subplan.
        Note: An alias is any string that begins with "alias_"
        :param arg: The argument string to be checked.
        :type arg: str
        :return: True if the arg is an alias.
        :rtype: bool
        """
        return arg.startswith("alias_")
