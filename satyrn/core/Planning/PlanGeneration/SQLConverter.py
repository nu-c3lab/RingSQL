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

import re
from contextlib import closing
from typing import Union, Dict

from satyrn.core.RingObjects.Ring import Ring
from satyrn.core.Analysis.AnalysisPlan import AnalysisPlan
from satyrn.core.Analysis.AnalysisEngine import AnalysisEngine

class SQLConverter:
    def __init__(self):
        self.analysis_engine = AnalysisEngine()
        self.alias_match_regex = re.compile('AS ("[a-zA-Z0-9()\/_,\-% ]+")')

    def convert_to_sql(self,
                       sqr: Union[AnalysisPlan, Dict[str, str]],
                       ring: Ring,
                       clean_aliases: bool=False,
                       remove_table_quotes=True) -> str:
        """
        Converts the given SQR plan to a SQL query.
        :param sqr: The SQR plan to convert.
        :type sqr: Union[AnalysisPlan, Dict[str, str]]
        :param ring: The ring this SQR plan is associated with.
        :type ring: Ring
        :param clean_aliases: A flag for whether or not the aliases in the SQL query should be simplified.
        :type clean_aliases: bool
        :return: The SQL query as a string.
        :rtype: str
        """

        # Make sure the SQR plan is of the correct type
        if isinstance(sqr, Dict):
            analysis_plan = self.analysis_engine.plan_parser.parse(sqr)
        else:
            analysis_plan = sqr

        # print(analysis_plan.get_roots())
        retrieved_ents = [analysis_plan.plan_steps[r].args[0] for r in analysis_plan.get_roots() if analysis_plan.plan_steps[r].operation == "retrieve_entity"]
        # print(retrieved_ents)
        # TODO: handle potential issues with entities that have attrs in multiple tables
        necessary_tables = set([ring.get_entity_by_name(ent).primary_table for ent in retrieved_ents])
        # print("TABLES:", necessary_tables)
        # necessary_tables = [t.lower() for t in necessary_tables]
        # print("TABLES:", necessary_tables)

        # Set some db interface props
        original_round_values = ring.db_interface.round_values
        ring.db_interface.round_values = False
        original_cast_values = ring.db_interface.cast_values
        ring.db_interface.cast_values = False

        # Build the query based on the SQR plan
        new_query_args = self.analysis_engine.query_builder_sqr.build_query_arguments_from_sqr_plan(analysis_plan, self.analysis_engine.ontology)
        with closing(ring.db.session_maker()) as session:
            query = self.analysis_engine.complex_query(new_query_args, ring, session, remove_table_refs_for_cols=len(necessary_tables) < 2)

        # Convert the query to a usable string
        sql_query_string = query.statement.compile(compile_kwargs={"literal_binds": True}).string
        # print("QUERY:", sql_query_string)

        # Reinstate old db_interface values
        ring.db_interface.round_values = original_round_values
        ring.db_interface.cast_values = original_cast_values

        # Clean up the query that was produced
        if clean_aliases:
            sql_query_string = self.simplify_aliases(sql_query_string)

        # Remove newlines from the query string
        sql_query_string = " ".join(sql_query_string.splitlines())

        # hacked together solution for stripping table quotes that aren't
        # needed in sqlite
        if remove_table_quotes:
            for t in necessary_tables:
                sql_query_string = sql_query_string.replace(f'"{t}"', t)

        return sql_query_string

    def simplify_aliases(self,
                         sql_query: str) -> str:
        """
        Simplifies complex aliases within the SQL query by replacing them with two character aliases (e.g. t1, c3).
        :param sql_query: The SQL query string to simplify.
        :type sql_query: str
        :return: The simplified SQL query.
        :rtype: str
        """

        # Simplify the table aliases
        simplified_query = sql_query.replace('alias_', 't')

        # Simplify the select/column aliases
        match_set = set(re.findall(self.alias_match_regex, simplified_query))
        for idx, alias in enumerate(match_set):
            simplified_query = simplified_query.replace(alias, f"c{idx}")

        return simplified_query
