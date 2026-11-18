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
from typing import List, Any
from functools import reduce
from sqlalchemy import cast, Float

from satyrn.core.Operations.ArgType import ArgType
from satyrn.core.Operations.SQLAInterface import SQLAInterface
from satyrn.core.Operations.PandasInterface import  PandasInterface
from satyrn.core.Operations.OperationArgument import OperationArgument
from satyrn.core.Operations.ArithmeticOperation import ArithmeticOperation

class PercentChange(ArithmeticOperation, SQLAInterface, PandasInterface):
    def __init__(self):
        name = 'percent_change'
        input_args = [
            OperationArgument(2, 2, [ArgType.Arithmetic, ArgType.Metric]),
        ]
        output_args = [
            OperationArgument(1, 1, [ArgType.Arithmetic, ArgType.Metric])
        ]
        template = "percent change from {0} to {1}"
        super().__init__(name, input_args, output_args, template)

    def sqlalchemy_op(self,
                      operation_input: List[Any],
                      db_type: str) -> None:
        return ((operation_input[1] / cast(operation_input[0], Float)) - 1) * 100

    def pandas_op(self,
                 operation_input: List[Any]) -> None:
        # TODO: Implement this
        return None
