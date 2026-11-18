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
from math import inf
from typing import Dict

import networkx as nx

from satyrn.core.api.utils import is_arg_reference
from satyrn.core.Analysis.AnalysisPlan import AnalysisPlan
from satyrn.core.Analysis.AnalysisStep import AnalysisStep
from satyrn.core.Planning.AnalysisPlanParser import AnalysisPlanParser

class SQRCompiler:
    def __init__(self,
                 plan_parser: AnalysisPlanParser):
        self.plan_parser = plan_parser

    def _remove_equivalent_subgraphs(self,
                                     analysis_plan: AnalysisPlan) -> Dict[str, AnalysisStep]:

        def same_node(node_a, node_b):
            # Nodes are the "same" if they have the same operation and the args are either equal or are references
            return node_a['data'].operation == node_b['data'].operation and len(node_a['data'].args) == len(node_b['data'].args) \
                and all((is_arg_reference(arg_a) and is_arg_reference(arg_b)) or arg_a == arg_b for arg_a, arg_b in zip(node_a['data'].args, node_b['data'].args))

        subgraphs = {alias: self.plan_parser.create_plan_graph(subplan.steps, allow_broken_refs=True) for alias, subplan in analysis_plan.subplans.items()}
        subgraph_sets = {}
        new_arg_mapping = {}
        for subgraph_alias in subgraphs:
            match = False
            for representative_alias in subgraph_sets:
                if nx.is_isomorphic(subgraphs[subgraph_alias], subgraphs[representative_alias], node_match=same_node):
                    match = True
                    subgraph_sets[representative_alias].append(subgraph_alias)

                    # The subgraphs are isomorphic...find mappings
                    ismags = nx.isomorphism.ISMAGS(subgraphs[subgraph_alias], subgraphs[representative_alias], node_match=same_node)
                    symmetry_mapping = next(ismags.find_isomorphisms(symmetry=False))

                    new_arg_mapping.update(symmetry_mapping)
                    break
            if not match:
                subgraph_sets[subgraph_alias] = []

        new_plan_steps = {}
        for alias in analysis_plan.subplans:
            if alias in subgraph_sets:
                for step in analysis_plan.subplans[alias].steps.values():
                    for i, arg in enumerate(step.args):
                        if is_arg_reference(arg) and arg in new_arg_mapping:
                            step.args[i] = new_arg_mapping[arg]
                new_plan_steps.update(analysis_plan.subplans[alias].steps)

        return new_plan_steps

    def _remove_exact_duplicates(self, plan_steps: Dict[str, AnalysisStep]) -> Dict[str, AnalysisStep]:

        plan_step_set = {}
        for step in plan_steps.values():
            if str(step) not in plan_step_set:
                plan_step_set[str(step)] = []
            plan_step_set[str(step)].append(step)

        duplicates = filter(lambda unique_step: len(unique_step) > 1, plan_step_set.values())
        new_ref_mapping = {duplicate.ref: duplicate_set[0].ref for duplicate_set in duplicates for duplicate in duplicate_set[1:]}

        new_plan_steps = {}
        for ref, step in plan_steps.items():
            if ref not in new_ref_mapping:
                for i, arg in enumerate(step.args):
                    if is_arg_reference(arg) and arg in new_ref_mapping:
                        step.args[i] = new_ref_mapping[arg]
                new_plan_steps[ref] = step
        return new_plan_steps

    def _renumber(self, plan_steps: Dict[str, AnalysisStep]) -> Dict[str, AnalysisStep]:
        plan_graph = self.plan_parser.create_plan_graph(plan_steps)
        renumbered_plan_steps = {}
        step_order_mapping = {step: f'|{idx + 1}|' for idx, step in enumerate(nx.topological_sort(plan_graph))}

        for old_step_num, new_step_num in step_order_mapping.items():
            step = plan_steps[old_step_num]
            for i, arg in enumerate(step.args):
                if is_arg_reference(arg):
                    step.args[i] = step_order_mapping[arg]
            step.ref = new_step_num
            renumbered_plan_steps[new_step_num] = step
        return renumbered_plan_steps

    def _alpha_number(self, plan_steps: Dict[str, AnalysisStep]) -> Dict[str, AnalysisStep]:
        parsed_plan = self.plan_parser.parse_from_analysis_steps(plan_steps)

        outer_alias_num = max(map(lambda alias: int(alias.partition('_')[-1]), parsed_plan.subplans.keys()))
        ordered_alias_numbers = sorted(map(lambda alias: int(alias.partition('_')[-1]), parsed_plan.subplans.keys()), reverse=True)
        step_letter_mapping = {}
        for alias_num in ordered_alias_numbers:
            alias = f"alias_{alias_num}"
            for step in parsed_plan.subplans[alias].steps.keys():
                step_letter_mapping[step] = '' if alias_num == outer_alias_num else chr(65 + alias_num)

        letter_to_number = {}
        for step, letter in step_letter_mapping.items():
            if letter not in letter_to_number:
                letter_to_number[letter] = []
            letter_to_number[letter].append(step)

        step_number_mapping = {}
        for letter in letter_to_number:
            # renumber by resetting count per subquery and adding letters
            step_number_mapping.update({old_num: f'|{i+1}{letter}|' for i,old_num in enumerate(sorted(letter_to_number[letter], key=lambda x: int(re.match(r'\|(\d+)\|', x).group(1))))}) # order by step order and then change to 1, 2, 3, ...

        renumbered_plan_steps = {}

        for old_step_num, new_step_num in step_number_mapping.items():
            step = plan_steps[old_step_num]
            for i, arg in enumerate(step.args):
                if is_arg_reference(arg):
                    step.args[i] = step_number_mapping[arg]
            step.ref = new_step_num
            renumbered_plan_steps[new_step_num] = step
        return renumbered_plan_steps

    def compile(self,
                analysis_plan: AnalysisPlan,
                alpha_numbering: bool = False) -> AnalysisPlan:
        """
        Compliles an analysis plan.
        :param raw_analysis_plan:
        :type raw_analysis_plan:
        :return:
        :rtype:
        """

        new_plan_steps = self._remove_equivalent_subgraphs(analysis_plan)

        num_old_plan_steps = inf

        while len(new_plan_steps) < num_old_plan_steps:
            num_old_plan_steps = len(new_plan_steps)
            deduped_plan_steps = self._remove_exact_duplicates(new_plan_steps)
            new_plan_steps = self._renumber(deduped_plan_steps)

        if alpha_numbering:
            new_plan_steps = self._alpha_number(new_plan_steps)

        return self.plan_parser.parse_from_analysis_steps(new_plan_steps)
