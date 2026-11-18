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


from satyrn.core.LanguageGeneration.GPT35Interface import GPT35Interface

class UtteranceClassifier:
    def __init__(self):
        self.language_model = GPT35Interface()

    def extract_utterance_type(self, utterance: str) -> str:
        default_prompt = "You have to classify whether the message is asking for a factual question or a report. Your job is to only identify the type of the message, so do not add any explanation, but rather answer out of the following two choices: question or report. Message:"
        examples = "\nBelow are some examples of possible messages with answers.These examples should provide you with some guidance on how to classify the message. \n Write a performance report on Microsoft - report\n Tell me about Liam Wilson who works at Salesforce - report \n Information on patient code 30492. - report \n What is Emma Johnson in Blackstone doing? - report\n What is the net worth of Amazon in 2020? - question\n What is the daily average number of visits of Sunshine clinic? - question \n"
        full_prompt = default_prompt + utterance + examples
        trials = 1
        response = ""
        while trials < 4:
            response = self.language_model.generate(prompt=full_prompt)
            if response == "report" or response == "question":
                break
            trials += 1
        return response


