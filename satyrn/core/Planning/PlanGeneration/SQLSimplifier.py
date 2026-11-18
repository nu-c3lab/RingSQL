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
import traceback
# TODO: implement this or add import to requirements
# from timeout_decorator import timeout
# from contextlib import closing
# from typing import Union, Dict

# from satyrn.core.RingObjects.Ring import Ring
# from satyrn.core.Analysis.AnalysisPlan import AnalysisPlan
# from satyrn.core.Analysis.AnalysisEngine import AnalysisEngine

class SQLSimplifier:
    def __init__(self):
        # self.analysis_engine = AnalysisEngine()
        # TODO: make this more efficient?
        self.alias_match_re = re.compile('((?:\([^\)]*\)|\S)+) AS ((?:"[^"]+")|(?:[^\s\),]+))')
        # assumes like in enclosed in parens which is what sqlalchemy does
        # self.like_match_re = re.compile('\(([^\(]\S+) LIKE ([^\)]+\([^\)]+\)[^\)]+|[^\)]+)+\)')
        self.like_match_re = re.compile("\(([^\(]\S+) LIKE ([^\)\(]*lower\((?:'[^']+'|[^\)]+)\)[^\)]*[^\)\(]*)+\)")
        # assumes lower is not wrapped around another function which shouldn't occur in generated data
        self.lower_match_re = re.compile('lower\((.+?)\)')
        # self.val_match_re = re.compile("'(.+?)'")
        # self.val_match_re = re.compile("'(.+?)'|lower\('?(.+?)'?\)")
        self.val_match_re = re.compile("lower\((?:'(.+?)'|([^'\)]+?))\)|'(.+?)'")
        # TODO: define this dependent on db dialect - this is for sqlite
        self.removable_quotes_re = re.compile('("[^0-9^()\/,\-% .#][^()\/,\-% .#]+[^0-9^()\/,\-% .#]")')
        # probably incomplete but should be good enough for spider dbs
        # TODO: refactor commone SQL keywords and re into separate module?
        self.sql_keywords = set([k.lower() for k in [
            "ADD",
            "ALL",
            "ALL",
            "ALTER",
            "AND",
            "ANY",
            "AS",
            "ASC",
            "AVG",
            "BACKUP",
            "BETWEEN",
            "BY",
            "CASE",
            "CHECK",
            "COLUMN",
            "CONSTRAINT",
            "COUNT",
            "CREATE",
            "DATABASE",
            "DEFAULT",
            "DELETE",
            "DESC",
            "DISTINCT",
            "DROP",
            "EXEC",
            "EXISTS",
            "FOREIGN",
            "FROM",
            "FULL",
            "GROUP",
            "HAVING",
            "IN",
            "INDEX",
            "INNER",
            "INSERT",
            "INTO",
            "IS",
            "JOIN",
            "KEY",
            "LEFT",
            "LIKE",
            "LIMIT",
            "MAX",
            "MIN",
            "NOT",
            "NULL",
            "OR",
            "ORDER",
            "OUTER",
            "PRIMARY",
            "PROCEDURE",
            "REPLACE",
            "RIGHT",
            "ROWNUM",
            "SELECT",
            "SET",
            "SUM",
            "TABLE",
            "TOP",
            "TRUNCATE",
            "UNION",
            "UNIQUE",
            "UPDATE",
            "VALUES",
            "VIEW",
            "WHERE",
        ]])
    # @timeout(5)
    def simplify_nested_query(self, sql_query):
        toks = sql_query.split()
        if "AS" not in toks:
            return sql_query
        toks_rev = toks.copy()
        toks_rev.reverse()
        # print(toks)
        # print(toks_rev)
        alias = toks[len(toks) - toks_rev.index("AS")]

        select_from_alias_re = re.compile(f'(SELECT[\s]+(?:{alias}\.[^\s]+[\s]+)+?[\s]*FROM[\s]+)')
        # select_from_alias_re = re.compile(f'({alias}\.[^\s]+[\s]+)+?')
        # select_from_alias_re = re.compile(f'(SELECT[\S]+({alias}\.[^\S]+[\S]+)+[\S]*FROM[\S]+\()')
        # print(select_from_alias_re)

        # TODO: handle case of schema items with parens?
        open_paren_splits = sql_query.split("(")
        outer_select = open_paren_splits[0]
        # print(outer_select)
        match = re.findall(select_from_alias_re, outer_select)
        # print(match)
        if match:
          # print("matched unneccessarily nested query")
          q = "(".join(open_paren_splits[1:])
          closed_paren_splits = q.split(")")
          assert f"AS {alias}" in closed_paren_splits[-1]
          return (")".join(closed_paren_splits[:-1]) \
                  + closed_paren_splits[-1].replace(f"AS {alias}", ""))


        else:
          return sql_query

    

    # @timeout(5)
    def remove_aliases(self, sql_query: str):
        # TODO: may want to remove more aliases?
        # for now just remove column aliases from the outer select
        # need to map aliases to their cols in case they are referenced in a condition, groupby or orderby
        split_on_froms = sql_query.split(" FROM ")
        outer_select = split_on_froms[0]
        rest = split_on_froms[1:]

        alias_matches = re.findall(self.alias_match_re, outer_select)
        aliases = {}
        for col, alias in alias_matches:
            aliases[alias] = col

        # print(aliases)

        outer_select = re.sub(self.alias_match_re, lambda x: aliases[x.group(2)], outer_select)

        # TODO: replace aliases in rest carefully - don't replace in subqueies?
        # if subqueries use unique col aliases which they seem to this is fine

        sql_query = " FROM ".join([outer_select] + rest)

        # keep aliases in subqueries
        subqueries = re.findall(r"\(\s*SELECT\s+.*?\s+FROM\s+.*?\)", sql_query)
        for sq in subqueries:
            sql_query = sql_query.replace(sq, "<subquery>")

        for a in aliases:
            # assumes spaces separate aliases ref and conditions or keywords - should hold
            sql_query = sql_query.replace(f" {a} ", f" {aliases[a]} ")

        # replace subqueries back into query string
        for sq in subqueries:
            sql_query = sql_query.replace("<subquery>", sq, 1)

        return sql_query

    # @timeout(5)
    def simplify_like(self, match:re.Match):
        # simplifies like statements - removing lower() functions and pipes
        col = match.group(1)
        vals = match.group(2)
        
        # print(col)
        # assumes no recursive lower() which should hold
        col_lower_match = re.findall(self.lower_match_re, col)[0]
        if col_lower_match:
            col = col_lower_match
        
        vals = re.findall(self.val_match_re, vals)
        # print(vals)
        val = "".join(["".join(v) for v in vals])
        return f"{col} LIKE '{val}'"

    def strip_unnecessary_quotes(self, sql_query):
        # matches = re.findall(self.removable_quotes_re, sql_query)
        # print(matches)
        sql_query = re.sub(
            self.removable_quotes_re,
            lambda x: x.group(1).strip('"') if x.group(1).strip('"').lower() not in self.sql_keywords else x.group(1),
            sql_query
        )
        return sql_query
    
    def simplify_joins(self, sql_query: str) -> str:
        sql, _ = re.subn(r"LEFT OUTER JOIN", "JOIN", sql_query, flags=re.IGNORECASE)
        return sql

    def simplify_sql(self,
                         sql_query: str) -> str:
        """
        Simplifies the SQL query by removing unneccessary aliases and simplifying
        LIKE conditions.
        :param sql_query: The SQL query string to simplify.
        :type sql_query: str
        :return: The simplified SQL query.
        :rtype: str
        """

        # Simplify the table aliases
        # simplified_query = sql_query.replace('alias_', 't')

        # Simplify the select/column aliases
        # match_set = set(re.findall(self.alias_match_regex, simplified_query))
        # for idx, alias in enumerate(match_set):
        #     simplified_query = simplified_query.replace(alias, f"c{idx}")

        # print(f"simplifying sql: {sql_query}")

        # TODO: determine ring db type, if schema objects are case-sensitive skip this but use it for sqlite
        # TODO: may cause issues with likes?? or string equality so use regex for matching these outside of ''
        #   - doesnt seem to be an issue
        simplified_query = self.strip_unnecessary_quotes(sql_query)
        # simplified_query = sql_query

        try:
            # simplify likes
            simplified_query = re.sub(self.like_match_re, lambda x: self.simplify_like(x), simplified_query)

            # these 2 simplification steps don't work for very complex queries 
            # so need to handle them with the AST
            # simplified_query = self.remove_aliases(simplified_query)

            # # may want to do this first eventually but now since re is inefficient 
            # # and we split on first from it makes it weird
            # simplified_query = self.simplifsy_nested_query(simplified_query)

            simplified_query = self.simplify_joins(simplified_query)

        except Exception as e:
            print(e)
            print(traceback.format_exc())
            pass
        
        return simplified_query.strip()
