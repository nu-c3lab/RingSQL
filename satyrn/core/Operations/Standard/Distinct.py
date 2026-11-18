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

import math

from satyrn.core.Operations.ArgType import ArgType
from satyrn.core.Operations.DataOperation import DataOperation
from satyrn.core.Operations.OperationArgument import OperationArgument

class Distinct(DataOperation):
    def __init__(self):
        name = "distinct"
        input_args = [
            OperationArgument(1, math.inf, [ArgType.Attribute])
        ]
        output_args = [
            OperationArgument(1, 1, [ArgType.AttributeCollection])
        ]
        super().__init__(name, input_args, output_args)
