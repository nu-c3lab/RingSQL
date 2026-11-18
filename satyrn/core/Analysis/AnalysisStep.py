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

from typing import List

class AnalysisStep():
    def __init__(self,
                 ref: str,
                 operation: str,
                 args: List[str]):
        self.ref = ref
        self.operation = operation
        self.args = args

        # handle ent or attr names with spaces
        # need to update this if sqr retrieval ops take in additional args
        if self.operation == "retrieve_entity":
            self.args = [" ".join(self.args)]
        elif self.operation == "retrieve_attribute":
            self.args = [str(a) for a in self.args]
            self.args = [self.args[0], " ".join(self.args[1:])]

    def __repr__(self):
        cleaned_args = ['\"' + str(arg) + '\"' if ' ' in str(arg).strip() or "'" in str(arg).strip() else str(arg) for arg in self.args]
        return f"({self.operation} {' '.join(cleaned_args)})"

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        return self.__repr__() == other.__repr__()
