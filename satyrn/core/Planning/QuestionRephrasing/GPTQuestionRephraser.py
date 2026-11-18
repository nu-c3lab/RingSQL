"""
This file is part of Satyrn.
Satyrn is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software Foundation,
either version 3 of the License, or (at your option) any later version.
Satyrn is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with Satyrn.
If not, see <https://www.gnu.org/licenses/>.
"""

import re
from typing import List
# from core.LanguageGeneration.GPT4Interface import GPT4Interface
from satyrn.core.LanguageGeneration.GPT4oMiniInterface import GPT4oMiniInterface
from satyrn.core.Planning.QuestionRephrasing.QuestionRephraser import QuestionRephraser
from sqlalchemy import text
from satyrn.core.Planning.QuestionRephrasing.ExampleBank import ExampleBank

# TODO: inherit from QuestionRephraser
# TODO: implement different prompting approaches and eval them
# try: 
# - just question
# - question with CoT
# - question and query with CoT
# - question, query and some of data with CoT


# TODO: may want to refactor the classes below or use these methods externally
from sentence_transformers.cross_encoder import CrossEncoder


# class QuoraRobertaInterface:
#     def __init__(self):
#         self.model = CrossEncoder("cross-encoder/quora-roberta-large")

#     def filter_non_duplicate_questions(
#         self, q: str, rephrased_questions: List[str], threshold=0.5
#     ) -> List[bool]:
#         scores = self.model.predict([(q, rq) for rq in rephrased_questions])
#         return [
#             rephrased_questions[i] for i in range(len(scores)) if scores[i] > threshold
#         ]


# class GPT4DuplicationChecker:
#     def __init__(self):
#         self.model = GPT4Interface()

#     def filter_non_duplicate_questions(
#         self, q: str, rephrased_questions: List[str], threshold=0.5
#     ) -> List[bool]:
#         filtered_questions = []
#         for rq in rephrased_questions:
#             response = self.model.generate(
#                 GPT_DUPLICATE_PROMPT.format(original_question=q, rephrased_question=rq)
#             )
#             if response == "Yes.":
#                 filtered_questions.append(rq)
#             elif response == "No.":
#                 pass
#             else:
#                 print(f"Unknown Response: {response}")
#         return filtered_questions


# DEFAULT_REPHRASING_PROMPT = """
#     I will rephrase a given question as a question 5 times and as an instruction 5 times.
#     Question: What was the percent change in the average wildfire size in California over the past 10 years?
#     Rephrased questions and instuctions:
#     1. How much did the average wildfire size in California change percentage-wise over the past 10 years?
#     2. Was there a percentage shift in the average wildfire size in California during the last decade?
#     3. Can you determine the percent change in the average size of wildfires in California over the past 10 years?
#     4. Did the average wildfire size in California experience a percent change over the last 10 years?
#     5. What percentage change occurred in the average size of wildfires in California throughout the past 10 years?
#     6. Calculate the percentage change in the average wildfire size in California over the past decade.
#     7. Determine the percent difference in the average size of wildfires in California between the current year and 10 years ago.
#     8. Assess the percentage change in the average wildfire size across California over the previous 10 years.
#     9. Compute the percent change in the average size of wildfires in California over the past 10 years.
#     10. Analyze the percentage shift in the average wildfire size in California over the last 10 years.
    
#     Question: What is the max air quality index grouped by year for state of Washington?
#     Rephrased questions and instructions:
#     1. What is the maximum air quality index grouped by year for the state of Washington?
#     2. Can you provide the highest air quality index grouped by year for Washington state?
#     3. What are the yearly maximums for air quality index in Washington?
#     4. What are the air quality index maximums grouped by year in Washington state?
#     5. What is the yearly max air quality index in Washington?
#     6. Compile the maximum air quality index data grouped by year for the state of Washington.
#     7. Organize the air quality index data by year to find the maximum for each year in Washington.
#     8. Group the air quality index data by year and determine the maximum for each year within Washington.
#     9. Collect the air quality index measurements and categorize them by year to identify the maximum for each year in Washington.
#     10. Tabulate the air quality index information, arranging it by year to establish the maximum for each year in Washington.
    
#     Question: {question}
#     Rephrased questions and instructions:"""

# GPT_DUPLICATE_PROMPT = """I will determine if the two questions provided are duplicates. My answer will be either "Yes." or "No."
#                         Question 1: What is the average star rating for business of Lou Malnalti’s?
#                         Question 2: Give me the mean star rating for Lou Malnalti's.
#                         Yes.
#                         Question 1: What is the average star rating for business of Lou Malnalti’s?
#                         Question 2: What is the median star rating for Lou Malnalti's?
#                         No.
#                         Question 1: {original_question}
#                         Question 2: {rephrased_question}"""

# logging file for evaluating performance
# FN = "question_generator_results/GPT4_Quora_"

PROMPTS = {
#   "question_only": """The following question was generated using a template \
# based on a SQL query. Please use your knowledge of SQL to rephrase the \
# following question to make it sound more natural and conversational while \
# ensuring that all information necessary to reconstruct the SQL query is \
# preserved. Only respond with a single rephrased question.

# Question: {question}""",
"question_only": """The following question was generated using a template based \
on a SQL query. Please use your knowledge of SQL to rephrase the following \
question to make it sound more natural and conversational while ensuring that \
all information necessary to reconstruct the SQL query is preserved and \
replacing keywords with synonyms where possible. Only respond with a single \
rephrased question.

Question: {question}""",
  "question_cot": """The following question was generated using a template \
based on a SQL query. Please use your knowledge of SQL to rephrase the \
following question to make it sound more natural and conversational while \
ensuring that all information necessary to reconstruct the SQL query is \
preserved. Think it through in multiple steps and then finish by providing \
the rephrased question proceeded by "Rephrased Question:".

Question: {question}""",
  "question_query_cot": """The given question was generated using a template \
based on the given SQL query. Please use your knowledge of SQL to rephrase the \
question to make it sound more natural and conversational while \
ensuring that all information necessary to reconstruct the SQL query is \
preserved. Think it through in multiple steps and then finish by providing \
the rephrased question proceeded by "Rephrased Question:".

Query: {query}

Question: {question}""",
  "question_query_data_cot": """The given question was generated using a template \
based on the given SQL query. Please use your knowledge of SQL to rephrase the \
question to make it sound more natural and conversational while \
ensuring that all information necessary to reconstruct the SQL query is \
preserved. Data from the first 5 rows of the query's result are also included. \
Think it through in multiple steps and then finish by providing the rephrased \
question proceeded by "Rephrased Question:".

Query: {query}

Data: {data}

Question: {question}""",
# adding specific prompt for rephrasing temporal things seems to work better
  "question_query_cot_few_shot": """The given question was generated using a template \
based on the given SQL query. Please use your knowledge of SQL to rephrase the \
question to make it sound more natural and conversational while \
ensuring that all information necessary to reconstruct the SQL query is \
preserved. Think it through in multiple steps and then finish by providing \
the rephrased question proceeded by "Rephrased Question:". If temporal values \
are referenced, the to use more natural words like youngest, first, most \
recent, etc... rather than more data agnostic phrasings.

Here are some examples of queries and their rephrased questions.

{examples}

Now please rephrase the following question for the given query to be more \
similar to the examples provided.

Query: {query}

Question: {question}""",

    "question_query_cot_few_shot_with_db_summary": """The given question was generated using a template \
based on the given SQL query. Please use your knowledge of SQL to rephrase the \
question to make it sound more natural and conversational while \
ensuring that all information necessary to reconstruct the SQL query is \
preserved. Think it through in multiple steps and then finish by providing \
the rephrased question proceeded by "Rephrased Question:". If temporal values \
are referenced, the to use more natural words like youngest, first, most \
recent, etc... rather than more data agnostic phrasings.

Here are some examples of queries and their rephrased questions.

{examples}

Now please rephrase the following question for the given query to be more \
similar to the examples provided. This question, query pair pertains to the \
database described below. Please use domain specific language in your rephrased \
question where possible.

Dataset Name: {ring_name}
Database Description: {ring_description}

Query: {query}

Question: {question}""",

    "question_query_cot_0_shot_with_db_summary": """The given question was generated using a template \
based on the given SQL query. Please use your knowledge of SQL to rephrase the \
question to make it sound more natural and conversational while \
ensuring that all information necessary to reconstruct the SQL query is \
preserved. Think it through in multiple steps and then finish by providing \
the rephrased question proceeded by "Rephrased Question:". If temporal values \
are referenced, the to use more natural words like youngest, first, most \
recent, etc... rather than more data agnostic phrasings. Please rephrase the \
following question for the given query pertaining to the \
database described below. Please use domain specific language in your rephrased \
question where possible and use natural language rather than SQL specific \
keywords or database schema items like table and column names.  Please also make\
the question as succinct as possible.

Dataset Name: {ring_name}
Database Description: {ring_description}

Query: {query}

Question: {question}""",

    "query_only_cot_0_shot_with_db_summary": """The given query was generated \
using a template. Please use your knowledge of SQL to provide a \ 
question that sounds natural and conversational while \
ensuring that all information necessary to reconstruct the SQL query is \
preserved. Think it through in multiple steps and then finish by providing \
the question proceeded by "Rephrased Question:". If temporal values \
are referenced, the to use more natural words like youngest, first, most \
recent, etc... rather than more data agnostic phrasings. Please provide a \
question for the given query pertaining to the \
database described below. Please use domain specific language in your rephrased \
question where possible and use natural language rather than SQL specific \
keywords or database schema items like table and column names. Please also make\
the question as succinct as possible.

Dataset Name: {ring_name}
Database Description: {ring_description}

Query: {query}"""

}

def format_examples(examples):
    return "\n\n".join([f"Query: {query}\nRephrased Question: {question}" for question, query in zip(examples["questions"], examples["queries"])])


# TODO: update this to support sqlite?
def execute_query(query, ring, n_rows=5):
    # print(ring.db_interface)
    # print(ring.db)
    # print(ring.db.eng)
    # print(type(ring.db.eng))
    # print(ring.db.session_maker)
    with ring.db.eng.connect() as conn:
        cursor = conn.execute(text(query))
        header = cursor.keys()
        data = cursor.fetchall()
    return header, data[:n_rows]

def display_data(header, data):
    # TODO: may want to execute plan to support including units?
    display = "\n" + "| " + " | ".join([c for c in header]) + " |"
    display += "\n|" + " | ".join(["---" for c in header]) + " |"
    for r in data:
        display += "\n| " + " | ".join([str(v) for v in r]) + " |"
    return display

class GPTQuestionRephraser(QuestionRephraser):
    def __init__(self, prompt_type="question_only", example_bank=None):
        if prompt_type not in PROMPTS.keys():
            raise ValueError(f"Unrecognized prompt_type {prompt_type}. Must be one of the following: {', '.join(PROMPTS.keys())}")
        super().__init__()
        self.rephrasing_model = GPT4oMiniInterface()
        # self.duplication_model = (
        #     duplication_model if duplication_model else QuoraRobertaInterface()
        # )
        self.prompt_type = prompt_type
        self.example_bank = example_bank


    def rephrase(self, question: str, query: str = None, ring=None, **kwargs) -> List[str]:
        #       Call self.rephrasing model with a prompt for rephrasing the question
        #       Parse the results
        #       Filter out results that are not identified as duplicates of the initial question
        #       Return the list of questions
        print(f"rephrasing question with {self.prompt_type} prompt")
        if self.prompt_type in ["question_only", "question_cot"]:
            prompt = PROMPTS[self.prompt_type].format(question=question)
        elif self.prompt_type == "question_query_cot":
            if not query:
                raise ValueError(f"For prompt_type {self.prompt_type} a query must be provided.")
            prompt = PROMPTS[self.prompt_type].format(question=question, query=query)
        elif self.prompt_type == "question_query_cot_few_shot":
            if not query:
                raise ValueError(f"For prompt_type {self.prompt_type} a query must be provided.")
            split = kwargs.get("split", None)
            if not split:
                raise ValueError(f"For prompt_type {self.prompt_type} a split must be provided.")
            db_id = kwargs.get("db_id", None)
            if not db_id:
                raise ValueError(f"For prompt_type {self.prompt_type} a db_id must be provided.")
            if not self.example_bank:
                self.example_bank = ExampleBank()
            prompt = PROMPTS[self.prompt_type].format(question=question, query=query, examples=format_examples(self.example_bank.query_examples(db_id, split, query, question)))
        elif self.prompt_type == "question_query_cot_few_shot_with_db_summary":
            if not query:
                raise ValueError(f"For prompt_type {self.prompt_type} a query must be provided.")
            split = kwargs.get("split", None)
            if not split:
                raise ValueError(f"For prompt_type {self.prompt_type} a split must be provided.")
            db_id = kwargs.get("db_id", None)
            if not db_id:
                raise ValueError(f"For prompt_type {self.prompt_type} a db_id must be provided.")
            if not self.example_bank:
                self.example_bank = ExampleBank()
            prompt = PROMPTS[self.prompt_type].format(question=question, query=query, examples=format_examples(self.example_bank.query_examples(db_id, split, query, question)), ring_name=ring.name, ring_description=ring.description)
        elif self.prompt_type == "question_query_cot_0_shot_with_db_summary":
            if not query:
                raise ValueError(f"For prompt_type {self.prompt_type} a query must be provided.")
            db_id = kwargs.get("db_id", None)
            if not db_id:
                raise ValueError(f"For prompt_type {self.prompt_type} a db_id must be provided.")
            prompt = PROMPTS[self.prompt_type].format(question=question, query=query, ring_name=ring.name, ring_description=ring.description)
        elif self.prompt_type == "query_only_cot_0_shot_with_db_summary":
            if not query:
                raise ValueError(f"For prompt_type {self.prompt_type} a query must be provided.")
            db_id = kwargs.get("db_id", None)
            if not db_id:
                raise ValueError(f"For prompt_type {self.prompt_type} a db_id must be provided.")
            prompt = PROMPTS[self.prompt_type].format(query=query, ring_name=ring.name, ring_description=ring.description)
        elif self.prompt_type == "question_query_data_cot":
            if not query:
                raise ValueError(f"For prompt_type {self.prompt_type} a query must be provided.")
            if not ring:
                raise ValueError(f"For prompt_type {self.prompt_type} a ring id must be provided to execute the query.")
            header, data = execute_query(query, ring, n_rows=5)
            # print(data)
            # print(display_data(header, data))
            # data = "<data-here>"
            prompt = PROMPTS[self.prompt_type].format(question=question, query=query, data=display_data(header, data))
        
        # print(prompt)
        # return prompt
        
        response = self.rephrasing_model.generate(prompt, temp=1)
        rephrased_question = response.split("Rephrased Question:")[-1].strip('" ')
        return rephrased_question


        # TODO: may need to parse responses differently
        # rephrased_questions = [s.strip() for s in re.split(r"\d+\.", response) if s]



        # logging for eval
        # f_rephrased = open(FN + "rephrased.txt", "a")
        # f_rephrased.write(f"\nOriginal: {question}\n")
        # for q in rephrased_questions:
        #     f_rephrased.write(q)
        #     f_rephrased.write("\n")

        # filtered_questions = self.duplication_model.filter_non_duplicate_questions(
        #     question, rephrased_questions
        # )

        # logging for eval
        # f_filtered = open(FN + "filtered.txt", "a")
        # f_filtered.write(f"\nOriginal: {question}\n")
        # for q in filtered_questions:
        #     f_filtered.write(q)
        #     f_filtered.write("\n")

        # return filtered_questions

    def batch_rephrase(self, questions: List[str]) -> List[List[str]]:
      raise NotImplemented