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

from typing import Any, List

from satyrn.core.Operations.ArgType import ArgType
from satyrn.core.Operations.OperationArgument import OperationArgument
from satyrn.core.Operations.BooleanOperation import BooleanOperation

class Between(BooleanOperation):
    def __init__(self):
        name = "between"
        input_args = [
            OperationArgument(1, 1, [ArgType.Metric, ArgType.Arithmetic]),
            OperationArgument(2, 2, [ArgType.Metric, ArgType.Arithmetic])
        ]
        output_args = [
            OperationArgument(1, 1, [ArgType.Filter])
        ]
        template = "{0} between {1} and {2}"
        super().__init__(name, input_args, output_args, template)

    def sqlalchemy_op(self,
                      operation_input: List[Any],
                      db_type: str) -> None:
        return operation_input[0].between(operation_input[1], operation_input[2])
