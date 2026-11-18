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

from typing import Dict

from satyrn.core.Operations.Operation import Operation

from satyrn.core.Operations.Standard.Sort import Sort
from satyrn.core.Operations.Standard.Limit import Limit
from satyrn.core.Operations.Standard.RowNum import RowNum
from satyrn.core.Operations.Standard.Collect import Collect
from satyrn.core.Operations.Standard.Distinct import Distinct
from satyrn.core.Operations.Standard.Return import Return
from satyrn.core.Operations.Logical.Exact import Exact
from satyrn.core.Operations.Logical.Contains import Contains
from satyrn.core.Operations.Logical.StartsWith import StartsWith
from satyrn.core.Operations.Logical.EndsWith import EndsWith
from satyrn.core.Operations.Logical.LessThan import LessThan
from satyrn.core.Operations.Logical.GreaterThan import GreaterThan
from satyrn.core.Operations.Logical.LessThanEq import LessThanEq
from satyrn.core.Operations.Logical.GreaterThanEq import GreaterThanEq
from satyrn.core.Operations.Logical.Like import Like
from satyrn.core.Operations.Logical.Between import Between
from satyrn.core.Operations.Logical.And import And
from satyrn.core.Operations.Logical.Or import Or
from satyrn.core.Operations.Logical.Not import Not
from satyrn.core.Operations.Standard.Groupby import Groupby
from satyrn.core.Operations.Standard.RetrieveEntity import RetrieveEntity
from satyrn.core.Operations.Standard.RetrieveAttribute import RetrieveAttribute

from satyrn.core.Operations.Aggregation.Average import Average
from satyrn.core.Operations.Aggregation.Count import Count
from satyrn.core.Operations.Aggregation.CountUnique import CountUnique
from satyrn.core.Operations.Aggregation.CountAll import CountAll
from satyrn.core.Operations.Aggregation.Max import Max
from satyrn.core.Operations.Aggregation.Median import Median
from satyrn.core.Operations.Aggregation.Min import Min
from satyrn.core.Operations.Aggregation.Sum import Sum
from satyrn.core.Operations.Aggregation.StdDev import StdDev
from satyrn.core.Operations.Aggregation.StringAgg import StringAgg
from satyrn.core.Operations.Aggregation.GetOne import GetOne
from satyrn.core.Operations.Aggregation.Correlation import Correlation

from satyrn.core.Operations.Math.Add import Add
from satyrn.core.Operations.Math.Subtract import Subtract
from satyrn.core.Operations.Math.Multiply import Multiply
from satyrn.core.Operations.Math.Divide import Divide
from satyrn.core.Operations.Math.Sqrt import Sqrt
from satyrn.core.Operations.Math.Abs import Abs
from satyrn.core.Operations.Math.PercentChange import PercentChange
from satyrn.core.Operations.Math.Duration import Duration
from satyrn.core.Operations.Math.Percentage import Percentage

from satyrn.core.Operations.Set.Union import Union
from satyrn.core.Operations.Set.Intersect import Intersect
from satyrn.core.Operations.Set.Except import Except

from satyrn.core.Operations.Logical.Exists import Exists
from satyrn.core.Operations.Logical.In import In

class OperationOntology:
    def __init__(self):
        self.retrieval_operations = self.load_retrieval_operations()
        self.aggregation_operations = self.load_aggregation_operations()
        self.boolean_operations = self.load_boolean_operations()
        self.subquery_bool_ops = self.load_subquery_bool_ops()
        self.collect_operations = self.load_collect_operations()
        self.distinct_operations = self.load_distinct_operations()
        self.return_operations = self.load_return_operations()
        self.set_operations = self.load_set_operations()
        self.sort_operations = self.load_sort_operations()
        self.limit_operations = self.load_limit_operations()
        self.rownum_operations = self.load_rownum_operations()
        self.analysis_operations = self.load_analysis_operations()
        self.arithmetic_operations = self.load_arithmetic_operations()

    def load_retrieval_operations(self) -> Dict[str, Operation]:
        ret_ent = RetrieveEntity()
        ret_attr = RetrieveAttribute()
        return {
            ret_ent.name: ret_ent,
            ret_attr.name: ret_attr
        }

    def load_aggregation_operations(self) -> Dict[str, Operation]:
        groupby_op = Groupby()
        return {
            groupby_op.name: groupby_op
        }

    def load_boolean_operations(self) -> Dict[str, Operation]:
        boolean_ops = [Exact, Contains, StartsWith, EndsWith, LessThan, GreaterThan, LessThanEq, GreaterThanEq, And, Or, Not, Like, Between]
        return {**{op().name: op() for op in boolean_ops}, **self.load_subquery_bool_ops()}

    def load_subquery_bool_ops(self) -> Dict[str, Operation]:
        boolean_ops = [Exists, In]
        return {op().name: op() for op in boolean_ops}

    def load_arithmetic_operations(self) -> Dict[str, Operation]:
        arithmetic_ops = [Add, Subtract, Multiply, Divide, Sqrt, Abs, PercentChange, Duration, Percentage]
        # also load and, or, and not operations here
        return {op().name: op() for op in arithmetic_ops}

    def load_collect_operations(self) -> Dict[str, Operation]:
        collect_op = Collect()
        return {
            collect_op.name: collect_op
        }

    def load_distinct_operations(self) -> Dict[str, Operation]:
        distinct_op = Distinct()
        return {
            distinct_op.name: distinct_op
        }

    def load_return_operations(self) -> Dict[str, Operation]:
        return_op = Return()
        return {
            return_op.name: return_op
        }

    def load_set_operations(self) -> Dict[str, Operation]:
        set_ops = [Union, Intersect, Except]
        return {op().name: op() for op in set_ops}

    def load_sort_operations(self) -> Dict[str, Operation]:
        sort_op = Sort()
        return {
            sort_op.name: sort_op
        }

    def load_limit_operations(self) -> Dict[str, Operation]:
        limit_op = Limit()
        return {
            limit_op.name: limit_op
        }

    def load_rownum_operations(self) -> Dict[str, Operation]:
        rownum_op = RowNum()
        return {
            rownum_op.name: rownum_op
        }

    def load_analysis_operations(self) -> Dict[str, Operation]:
        # TODO: Make this dynamically load in all analysis operations in specific subdirectory (i.e. a plug-ins directory)
        # Get a list of the analysis operation classes
        analysis_ops = [Average, Count, CountAll, CountUnique, Max, Median, Min, Sum, StdDev, StringAgg, GetOne, Correlation]

        # Create the dictionary with the analysis operations instantiated
        analysis_ops_dict = {op().name: op() for op in analysis_ops}

        return analysis_ops_dict

    def load_plugin_operations(self) -> Dict[str, Operation]:
        plugin_ops = [Duration, Percentage]
        return {op().name: op() for op in plugin_ops}

    def is_retrieval_operation(self,
                               operation_name: str) -> bool:
        return operation_name in self.retrieval_operations

    def is_analysis_operation(self,
                              operation_name: str) -> bool:
        return operation_name in self.analysis_operations

    def is_collect_operation(self,
                            operation_name: str) -> bool:
        return operation_name in self.collect_operations

    def is_distinct_operation(self,
                             operation_name: str) -> bool:
        return operation_name in self.distinct_operations

    def is_return_operation(self,
                          operation_name: str) -> bool:
        return operation_name in self.return_operations

    def is_set_operation(self,
                         operation_name: str) -> bool:
        return operation_name in self.set_operations

    def is_sort_operation(self,
                          operation_name: str) -> bool:
        return operation_name in self.sort_operations

    def is_limit_operation(self,
                           operation_name: str) -> bool:
        return operation_name in self.limit_operations

    def is_rownum_operation(self,
                            operation_name: str) -> bool:
        return operation_name in self.rownum_operations

    def is_boolean_operation(self,
                             operation_name: str) -> bool:
        return operation_name in self.boolean_operations

    def is_subquery_bool_operation(self,
                                   operation_name: str) -> bool:
        return operation_name in self.subquery_bool_ops

    def is_aggregation_operation(self,
                                 operation_name: str) -> bool:
        return operation_name in self.aggregation_operations

    def is_arithmetic_operation(self,
                                operation_name: str) -> bool:
        return operation_name in self.arithmetic_operations

    def resolve_operation(self,
                          operation_name: str) -> Operation:
        if operation_name in self.analysis_operations:
            return self.analysis_operations[operation_name]
        elif operation_name in self.retrieval_operations:
            return self.retrieval_operations[operation_name]
        elif operation_name in self.set_operations:
            return self.set_operations[operation_name]
        elif operation_name in self.aggregation_operations:
            return self.aggregation_operations[operation_name]
        elif operation_name in self.boolean_operations:
            return self.boolean_operations[operation_name]
        elif operation_name in self.collect_operations:
            return self.collect_operations[operation_name]
        elif operation_name in self.distinct_operations:
            return self.distinct_operations[operation_name]
        elif operation_name in self.return_operations:
            return self.return_operations[operation_name]
        elif operation_name in self.sort_operations:
            return self.sort_operations[operation_name]
        elif operation_name in self.limit_operations:
            return self.limit_operations[operation_name]
        elif operation_name in self.arithmetic_operations:
            return self.arithmetic_operations[operation_name]
        elif operation_name in self.rownum_operations:
            return self.rownum_operations[operation_name]
        else:
            raise ValueError("Unable to resolve the operation name to operation object.")
