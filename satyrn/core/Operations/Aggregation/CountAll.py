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

class CountAll(AggregationOperation, SQLAInterface, PandasInterface):
    def __init__(self):
        name = 'count_all'
        # TODO: may want to find a better way to do this since attribute input 
        # isn't really needed but this seems to work fine when used in collect 
        # with other args
        input_args = [
            OperationArgument(1, 1, [ArgType.Arithmetic, ArgType.Metric]),
            OperationArgument(0, 1, [ArgType.Group])
        ]
        output_args = [
            OperationArgument(1, 1, [ArgType.Arithmetic, ArgType.Metric])
        ]
        # TODO: may want to improve this language to use entity nicename
        template = "number of rows"
        super().__init__(name, input_args, output_args, template)

    def sqlalchemy_op(self,
                      operation_input: List[Any],
                      db_type: str) -> None:
        return func.count()

    def pandas_op(self,
                 operation_input: List[Any]) -> None:
        # TODO: Implement this
        return None
