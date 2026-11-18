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

from typing import Set

from satyrn.core.RingObjects.RingAttribute import RingAttribute

class InputAssignment:
    """
    A simple data structure for keeping track of the attributes assigned to each input slot
    """
    def __init__(self,
                 attr: RingAttribute = None,
                 inputs: Set[str] = None):
        self.attr = attr                             # The attribute assigned to one or more inputs of a base plan
        self.inputs = inputs if inputs else set()    # The set of input values the attribute is assigned to (e.g. ["|A|", "|C|"])

    def __eq__(self, other):
        if isinstance(other, InputAssignment):
            return self.attr == other.attr and self.inputs == other.inputs
        return False
