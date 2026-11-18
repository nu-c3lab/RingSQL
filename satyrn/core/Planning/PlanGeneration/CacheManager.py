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

import random
from typing import List, Union, Tuple
from contextlib import closing
from sqlalchemy.sql.expression import func
from cachetools import cachedmethod, LRUCache

from satyrn.core.RingObjects.Ring import Ring
from satyrn.core.Analysis.AnalysisEngine import AnalysisEngine
from satyrn.core.RingObjects.RingAttribute import RingAttribute

class CacheManager:
    def __init__(self,
                 ring: Ring,
                 max_items: int = 100,
                 max_values_per_item: int = 500):
        self.ring = ring
        self.max_items = max_items
        self.max_values_per_item = max_values_per_item
        self.value_cache = {}
        self.cache = LRUCache(maxsize=self.max_items)

    @cachedmethod(lambda self: self.cache)
    def get_distinct_attribute_values(self,
                                      attr: Union[RingAttribute, Tuple[RingAttribute]]) -> List:
        """
        Queries the database for values, caches the distinct values, and returns the contents of the cache.
        :param attr: The attribute to get values for.
        :type attr: RingAttribute
        :return: A list of distinct values for this attribute.
        :rtype: List
        """
        if isinstance(attr, RingAttribute):
            if attr.source_table:
                # For attributes that have a source table in the database (i.e. non-derived attributes)
                with closing(self.ring.db_interface.db.session_maker()) as session:
                    # Get the SQL Alchemy model associated with the model name string
                    model = getattr(self.ring.db_interface.db, attr.source_table)

                    # Get the SQL Alchemy object representing this field
                    field = getattr(model, attr.source_columns[0])

                    # Execute the query to get the distinct values and clean the output
                    distinct_attribute_values = session.query(field).filter(field.isnot(None)).order_by(func.random()).limit(self.max_values_per_item).all()
                    # distinct_attribute_values = session.query(field).distinct().all()
                    all_values = [value[0] for value in distinct_attribute_values]
            else:
                # For attributes that have no source table (i.e. derived attributes)
                analysis_engine = AnalysisEngine(self.ring)
                analysis_plan = analysis_engine.plan_parser.parse(attr.access_plan)

                # Run the analysis
                with closing(self.ring.db.session_maker()) as session:
                    result_dict = analysis_engine.sqr_single_ring_analysis(analysis_plan, self.ring, session)

                # Get the second column of values from the results        # TODO: Figure out a way to get the right values, in general
                all_values = [row[1] if len(row) > 1 else row[0] for row in result_dict['results']]
        else:
            # assume attr is list of id attributes so will have corresponding source tables
            with closing(self.ring.db_interface.db.session_maker()) as session:
                    # Get the SQL Alchemy model associated with the model name string
                    attr_vals = []
                    for att in attr:
                        model = getattr(self.ring.db_interface.db, att.source_table)

                        # Get the SQL Alchemy object representing this field
                        field = getattr(model, att.source_columns[0])

                        # Execute the query to get the distinct values and clean the output
                        attr_vals.append([value[0] for value in session.query(field).filter(field.isnot(None)).order_by(func.random()).limit(self.max_values_per_item).all()])
                    # distinct_attribute_values = session.query(field).distinct().all()
                    all_values = zip(*attr_vals)

        # Get all the unique values
        distinct_attribute_values = list(set([self.list_to_db_string(v) if isinstance(v, list) else v for v in all_values]))

        # Save the values in the cache
        random.shuffle(distinct_attribute_values)
        return distinct_attribute_values[:self.max_values_per_item]

    def list_to_db_string(self,
                          l: List) -> str:
        return "{" + ",".join(l) + "}"
