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

import torch
from typing import List, Dict
from sentence_transformers import util, SentenceTransformer

class SentenceSimilarityScorer():
    def __init__(self):
        # Load the embedding model
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')

    def get_most_similar_statements(self,
                                    subquestions: List[str],
                                    factual_statements: List[str]) -> Dict[str, str]:
        """

        :param subquestions:
        :type subquestions:
        :param factual_statements:
        :type factual_statements:
        :return: A dictionary mapping the subquestion to the most similar factual statement
        :rtype:
        """
        # Embed the factual statements
        statement_embeddings = self.embedder.encode(factual_statements, convert_to_tensor=True)

        # Find the most similar statement for each of the subquestions
        return {question: self._get_similar_statements_for_one(question, factual_statements, statement_embeddings, 1) for question in subquestions}

    def _get_similar_statements_for_one(self,
                                        question: str,
                                        factual_statements: List[str],
                                        statement_embeddings,
                                        top_k: int=1) -> str:
        if len(factual_statements) > 0:
            # Embed the current question
            query_embedding = self.embedder.encode(question)

            # Retrieve some number of cases that are most similar
            cos_scores = util.pytorch_cos_sim(query_embedding, statement_embeddings)[0]
            top_results = torch.topk(cos_scores, k=top_k)

            top_cases = []
            for score, idx in zip(top_results[0], top_results[1]):
                top_cases.append((factual_statements[idx], float(score)))
            return top_cases[0][0]
        else:
            return ""