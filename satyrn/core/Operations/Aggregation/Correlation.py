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

from typing import List, Any

from sqlalchemy import func

from satyrn.core.Operations.ArgType import ArgType
from satyrn.core.Operations.SQLAInterface import SQLAInterface
from satyrn.core.Operations.PandasInterface import  PandasInterface
from satyrn.core.Operations.OperationArgument import OperationArgument
from satyrn.core.Operations.AggregationOperation import AggregationOperation

class Correlation(AggregationOperation, SQLAInterface, PandasInterface):
    def __init__(self):
        name = 'correlation'
        input_args = [
            OperationArgument(2, 2, [ArgType.Arithmetic, ArgType.Metric, ArgType.Datetime]),
            OperationArgument(0, 1, [ArgType.Group])
        ]
        output_args = [
            OperationArgument(1, 1, [ArgType.Arithmetic, ArgType.Metric, ArgType.Datetime])
        ]
        template = "correlation between {0} and {1}"
        super().__init__(name, input_args, output_args, template)

    def sqlalchemy_op(self,
                      operation_input: List[Any],
                      db_type: str) -> None:
        if db_type == 'postgres':
            return func.corr(*operation_input)
        else:
            # raise TypeError(f"{db_type} does not support this operation.")
            (c1, c2) = operation_input
            return ((func.count() * func.sum(c1 * c2)) - (func.sum(c1) * func.sum(c2))
                / func.sqrt(
                    (func.count() * func.sum(c1 * c1) - func.pow(func.sum(c1), 2))
                    * (func.count() * func.sum(c2 * c2) - func.pow(func.sum(c2), 2))
                    )
            )
            

    def pandas_op(self,
                 operation_input: List[Any]) -> None:
        # TODO: Implement this
        return None
