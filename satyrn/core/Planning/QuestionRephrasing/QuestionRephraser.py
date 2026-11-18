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

from abc import ABC, abstractmethod
from typing import List

class QuestionRephraser(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def rephrase(self,
                 question: str) -> List[str]:
        pass

    @abstractmethod
    def batch_rephrase(self,
                       questions: List[str]) -> List[List[str]]:
        pass
