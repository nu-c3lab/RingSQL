# FROM o3
"""
simplify_sql.py
Simplify SQL queries into a compact Spider-style form, removing
unneeded aliases, type casts and (when safe) inlining scalar
sub-queries that are referenced only once.

Requires:  sqlglot  >= 24.0      pip install sqlglot
Usage:     python simplify_sql.py "SELECT …"
           python simplify_sql.py -f query.sql
           (prints simplified SQL to stdout)
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from typing import Dict, Set

from tqdm import tqdm
import sqlite3
import sqlglot
from sqlglot import exp
from sqlglot.optimizer import simplify  # expression-level algebraic simplifier

# from copy import deepcopy
import re
import json

# overwrite neq sql to be "!=" for sqlite
def neq_sql(self, expression: exp.NEQ) -> str:
    return self.binary(expression, "!=")


sqlglot.generator.Generator.neq_sql = neq_sql


def ast_to_dict(node):
    if isinstance(node, exp.Expression):
        node_dict = {
            "kind": str(type(node)),
            "expression": node.sql(), # Or a more detailed representation of the node's SQL
            "args": {}
        }
        for arg_name, arg_value in node.args.items():
            if isinstance(arg_value, list):
                node_dict["args"][arg_name] = [ast_to_dict(item) for item in arg_value]
            elif isinstance(arg_value, exp.Expression):
                node_dict["args"][arg_name] = ast_to_dict(arg_value)
            else:
                node_dict["args"][arg_name] = arg_value
        return node_dict
    else:
        return str(node) # Handle non-Expression nodes, like literals or identifiers

class Simplifier:
    """
    Rewrites a parsed sqlglot expression tree in-place.
    """

    def __init__(self, root: exp.Expression):
        # self.root = simplify.simplify(root)  # 1️⃣ algebraic / cast cleanup
        self.root = root
        self.alias_to_subquery: Dict[str, exp.Subquery] = {}
        self.alias_ref_count: Counter[str] = Counter()
        # self._index_alias_usage()
        # print("WITH:", repr(self.root.args["with"]))

    # --------------------------------------------------------------------- #
    #                           public entry point                          #
    # --------------------------------------------------------------------- #
    def run(self, dialect="sqlite"):
        """
        Main function to standardize and simplify SQL queries.
        
        Args:
            sql_query: SQL query string
            dialect: SQL dialect (default: sqlite)
        
        Returns:
            Simplified SQL query string
        """
        try:
            # Parse the SQL query
            # parsed = sqlglot.parse_one(sql_query, dialect=dialect)
            # print(self.root)
            # Remove all CAST expressions
            # TODO: leave casts to float where needed?
            self.root = self.remove_casts(self.root)

            # print("ROOT:", self.root)

            # Simplify subqueries
            self.root = self.simplify_subqueries(self.root)

            # print(self.root)

            self.root = self.remove_unused_aliases(self.root)

            # print(self.root)

            self.root = self.deduplicate_common_subqueries(self.root)
            
            # print(self.root)

            self.root = self.alias_tables_and_drop_unused_columns(self.root)

            # print(self.root)

            self.root = self.clean_table_and_alias_refs(self.root)
            # print(self.root)

            # Convert back to SQL
            # simplified = self.root.sql(dialect=dialect, pretty=True)
            
            # print(ast_to_dict(self.root))

            return self.root
        
        except Exception as e:
            print(f"Error processing query: {str(e)}")
            return f"Error processing query: {str(e)}"
    
    def remove_casts(self, node):
        # """Recursively remove all CAST expressions from the query."""
        return node.transform(lambda n: self.remove_casts(n.this) if isinstance(n, exp.Cast) and not isinstance(n.this, exp.Cast) else n)

    def alias_tables_and_drop_unused_columns(self, node, parent_required_aliases=None):
        """
        1. Add aliases to tables used in JOINs (and propagate to JOIN ON, WHERE, GROUP BY, ORDER BY)
        2. Drop unnecessary columns from subquery projections that aren't used by parent
        
        Args:
            node: The SQL expression node to process
            parent_required_aliases: Set of column aliases that parent query needs from this subquery
        """
        
        if parent_required_aliases is None:
            parent_required_aliases = set()
        
        if not isinstance(node, exp.Select):
            # Recursively process nested selects
            for child in node.find_all(exp.Select):
                self.alias_tables_and_drop_unused_columns(child, parent_required_aliases)
            return node
        
        # First, handle subqueries recursively to determine what columns they need
        subquery_required_aliases = {}  # subquery_alias -> set of column aliases needed
        
        # Check FROM clause for subqueries
        from_clause = node.args.get("from")
        if from_clause and isinstance(from_clause.this, exp.Subquery):
            subquery = from_clause.this
            subquery_alias = subquery.alias
            required = set()
            
            # Find all column references to this subquery in current node
            for col in node.find_all(exp.Column):
                if col.table == subquery_alias:
                    required.add(col.name)
            
            subquery_required_aliases[subquery_alias] = required
            # Recursively process the subquery
            self.alias_tables_and_drop_unused_columns(subquery.this, required)
        
        # Check JOIN clauses for subqueries
        joins = node.args.get("joins")
        if joins:
            for join in joins:
                if isinstance(join.this, exp.Subquery):
                    subquery = join.this
                    subquery_alias = subquery.alias
                    required = set()
                    
                    # Find all column references to this subquery
                    for col in node.find_all(exp.Column):
                        if col.table == subquery_alias:
                            required.add(col.name)
                    
                    subquery_required_aliases[subquery_alias] = required
                    # Recursively process the subquery
                    self.alias_tables_and_drop_unused_columns(subquery.this, required)
        
        # Now handle table aliasing for this query level
        # If there are JOINs, add aliases to all tables
        has_joins = joins and len(joins) > 0
        
        if has_joins:
            table_alias_map = {}  # old_table_name -> new_alias
            alias_counter = 0
            
            # Add alias to FROM table if it doesn't have one
            from_clause = node.args.get("from")
            if from_clause and isinstance(from_clause.this, exp.Table):
                table = from_clause.this
                table_name = table.name
                
                if not table.alias:
                    new_alias = f"t{alias_counter}"
                    alias_counter += 1
                    table.set("alias", exp.TableAlias(this=exp.Identifier(this=new_alias)))
                    table_alias_map[table_name] = new_alias
                else:
                    table_alias_map[table_name] = table.alias
            
            # Add aliases to JOIN tables if they don't have them
            for join in joins:
                if isinstance(join.this, exp.Table):
                    table = join.this
                    table_name = table.name
                    
                    if not table.alias:
                        new_alias = f"t{alias_counter}"
                        alias_counter += 1
                        table.set("alias", exp.TableAlias(this=exp.Identifier(this=new_alias)))
                        table_alias_map[table_name] = new_alias
                    else:
                        table_alias_map[table_name] = table.alias
            
            # Now update all column references to use the table aliases
            def update_column_with_alias(col):
                if not isinstance(col, exp.Column):
                    return col
                
                table_ref = col.table
                if table_ref and table_ref in table_alias_map:
                    return exp.Column(this=col.name, table=table_alias_map[table_ref])
                return col
            
            # Update SELECT expressions
            new_expressions = []
            for expr in node.expressions:
                updated_expr = expr.transform(update_column_with_alias)
                new_expressions.append(updated_expr)
            node.set("expressions", new_expressions)
            
            # Update JOIN ON conditions
            for join in joins:
                if join.args.get("on"):
                    join_on = join.args["on"]
                    updated_on = join_on.transform(update_column_with_alias)
                    join.set("on", updated_on)
            
            # Update WHERE clause
            where = node.args.get("where")
            if where:
                updated_where = where.transform(update_column_with_alias)
                node.set("where", updated_where)
            
            # Update GROUP BY clause
            group_by = node.args.get("group")
            if group_by:
                new_group_expressions = []
                for expr in group_by.expressions:
                    updated_expr = expr.transform(update_column_with_alias)
                    new_group_expressions.append(updated_expr)
                group_by.set("expressions", new_group_expressions)
            
            # Update ORDER BY clause
            order_by = node.args.get("order")
            if order_by:
                new_order_expressions = []
                for expr in order_by.expressions:
                    if isinstance(expr, exp.Ordered):
                        updated_inner = expr.this.transform(update_column_with_alias)
                        new_order_expressions.append(exp.Ordered(this=updated_inner, desc=expr.args.get("desc", False)))
                    else:
                        updated_expr = expr.transform(update_column_with_alias)
                        new_order_expressions.append(updated_expr)
                order_by.set("expressions", new_order_expressions)
            
            # Update HAVING clause
            having = node.args.get("having")
            if having:
                updated_having = having.transform(update_column_with_alias)
                node.set("having", updated_having)
        
        # Drop unnecessary columns if this is a subquery and parent specified requirements
        if parent_required_aliases:
            # Filter SELECT expressions to only include required columns
            new_expressions = []
            for expr in node.expressions:
                keep_expr = False
                
                if isinstance(expr, exp.Alias):
                    # Keep if alias is required by parent
                    if expr.alias in parent_required_aliases:
                        keep_expr = True
                else:
                    # If it's not aliased, check if it's a column that might be referenced
                    if isinstance(expr, exp.Column):
                        if expr.name in parent_required_aliases:
                            keep_expr = True
                    else:
                        # For other expressions without aliases, keep them (might be needed)
                        keep_expr = True
                
                if keep_expr:
                    new_expressions.append(expr)
            
            # Only update if we have at least one expression left
            if new_expressions:
                node.set("expressions", new_expressions)
        
        return node

    def clean_table_and_alias_refs(self, node, parent_required_aliases=None):
        """
        Clean table and alias references:
        1. Remove table prefixes in single-table queries
        2. Use aliases instead of table names in multi-table queries
        3. Replace column references in GROUP BY, WHERE, ORDER BY with aliases from SELECT when available
        4. Remove aliases from SELECT that are not referenced anywhere (including parent queries)
        
        Args:
            node: The SQL expression node to process
            parent_required_aliases: Set of (subquery_alias, column_alias) tuples that must be kept
        """
        
        if parent_required_aliases is None:
            parent_required_aliases = set()
        
        if not isinstance(node, exp.Select):
            # Recursively process nested selects
            for child in node.find_all(exp.Select):
                self.clean_table_and_alias_refs(child, parent_required_aliases)
            return node
        
        # Build a map of expression -> alias from SELECT clause
        select_alias_map = {}  # Maps normalized expression SQL to alias name
        for expr in node.expressions:
            if isinstance(expr, exp.Alias):
                # Store the expression's SQL representation as key
                expr_sql = expr.this.sql(pretty=False)
                select_alias_map[expr_sql] = expr.alias
        
        # Determine if this is a single-table query or multi-table
        tables = set()
        table_aliases = {}  # table_name -> alias
        
        # Check FROM clause
        from_clause = node.args.get("from")
        if from_clause:
            if isinstance(from_clause.this, exp.Table):
                table = from_clause.this
                table_name = table.name
                tables.add(table_name)
                if table.alias:
                    table_aliases[table_name] = table.alias
            elif isinstance(from_clause.this, exp.Subquery):
                # Subqueries always have aliases
                if from_clause.this.alias:
                    table_aliases['_subquery_'] = from_clause.this.alias
        
        # Check JOIN clauses
        joins = node.args.get("joins")
        if joins:
            for join in joins:
                if isinstance(join.this, exp.Table):
                    table = join.this
                    table_name = table.name
                    tables.add(table_name)
                    if table.alias:
                        table_aliases[table_name] = table.alias
                elif isinstance(join.this, exp.Subquery):
                    if join.this.alias:
                        table_aliases[f'_subquery_{len(table_aliases)}'] = join.this.alias
        
        is_single_table = len(tables) == 1 and not joins
        
        def clean_column_ref(col):
            """Clean a column reference based on context."""
            if not isinstance(col, exp.Column):
                return col
            
            col_name = col.name
            table_ref = col.table
            
            if is_single_table:
                # Remove table prefix in single-table queries
                return exp.Column(this=col_name)
            else:
                # In multi-table queries, use alias if available
                if table_ref and table_ref in table_aliases:
                    return exp.Column(this=col_name, table=table_aliases[table_ref])
                return col
        
        def replace_with_select_alias(expr):
            """Replace an expression with its alias from SELECT if available."""
            expr_sql = expr.sql(pretty=False)
            
            # Try to match with select aliases
            if expr_sql in select_alias_map:
                return exp.Column(this=select_alias_map[expr_sql])
            
            # For columns, also try without table prefix
            if isinstance(expr, exp.Column):
                col_only_sql = exp.Column(this=expr.name).sql(pretty=False)
                if col_only_sql in select_alias_map:
                    return exp.Column(this=select_alias_map[col_only_sql])
                
                # Try with table prefix
                if expr.table:
                    table_col_sql = exp.Column(this=expr.name, table=expr.table).sql(pretty=False)
                    if table_col_sql in select_alias_map:
                        return exp.Column(this=select_alias_map[table_col_sql])
            
            return None
        
        # Clean column references in SELECT expressions
        new_expressions = []
        for expr in node.expressions:
            if isinstance(expr, exp.Alias):
                # Clean the expression inside the alias
                cleaned_expr = expr.this.transform(clean_column_ref)
                new_expressions.append(exp.Alias(this=cleaned_expr, alias=expr.alias))
            else:
                cleaned_expr = expr.transform(clean_column_ref)
                new_expressions.append(cleaned_expr)
        
        node.set("expressions", new_expressions)
        
        # Rebuild select_alias_map with cleaned expressions
        select_alias_map = {}
        select_aliases_list = []  # Track all aliases in order
        for expr in node.expressions:
            if isinstance(expr, exp.Alias):
                expr_sql = expr.this.sql(pretty=False)
                select_alias_map[expr_sql] = expr.alias
                select_aliases_list.append(expr.alias)
        
        # Clean GROUP BY clause - use aliases when possible
        group_by = node.args.get("group")
        if group_by:
            new_group_expressions = []
            for expr in group_by.expressions:
                # First try to replace with SELECT alias
                alias_replacement = replace_with_select_alias(expr)
                if alias_replacement:
                    new_group_expressions.append(alias_replacement)
                else:
                    # Otherwise just clean the column references
                    cleaned = expr.transform(clean_column_ref)
                    new_group_expressions.append(cleaned)
            
            group_by.set("expressions", new_group_expressions)
        
        # Clean ORDER BY clause - use aliases when possible
        order_by = node.args.get("order")
        if order_by:
            new_order_expressions = []
            for expr in order_by.expressions:
                if isinstance(expr, exp.Ordered):
                    # Handle ASC/DESC
                    order_expr = expr.this
                    alias_replacement = replace_with_select_alias(order_expr)
                    if alias_replacement:
                        new_order_expressions.append(exp.Ordered(this=alias_replacement, desc=expr.args.get("desc", False)))
                    else:
                        cleaned = order_expr.transform(clean_column_ref)
                        new_order_expressions.append(exp.Ordered(this=cleaned, desc=expr.args.get("desc", False)))
                else:
                    alias_replacement = replace_with_select_alias(expr)
                    if alias_replacement:
                        new_order_expressions.append(alias_replacement)
                    else:
                        cleaned = expr.transform(clean_column_ref)
                        new_order_expressions.append(cleaned)
            
            order_by.set("expressions", new_order_expressions)
        
        # Clean WHERE clause - use aliases when possible
        where = node.args.get("where")
        if where:
            where_expr = where.this
            # Try to replace parts with SELECT aliases
            def try_replace_in_where(n):
                alias_replacement = replace_with_select_alias(n)
                if alias_replacement:
                    return alias_replacement
                return clean_column_ref(n)
            
            cleaned_where = where_expr.transform(try_replace_in_where)
            where.set("this", cleaned_where)
        
        # Clean HAVING clause - use aliases when possible
        having = node.args.get("having")
        if having:
            having_expr = having.this
            def try_replace_in_having(n):
                alias_replacement = replace_with_select_alias(n)
                if alias_replacement:
                    return alias_replacement
                return clean_column_ref(n)
            
            cleaned_having = having_expr.transform(try_replace_in_having)
            having.set("this", cleaned_having)
        
        # Now find which aliases are actually used
        used_aliases = set()
        
        # Check all clauses for alias usage
        for clause_name in ["where", "group", "having", "order", "limit", "offset"]:
            clause = node.args.get(clause_name)
            if clause:
                for col in clause.find_all(exp.Column):
                    if col.name in select_aliases_list:
                        used_aliases.add(col.name)
        
        # Before processing subqueries, collect what aliases they need to provide
        subquery_required_aliases = {}  # subquery_alias -> set of column aliases needed
        
        # Check FROM clause for subqueries
        from_clause = node.args.get("from")
        if from_clause and isinstance(from_clause.this, exp.Subquery):
            subquery = from_clause.this
            subquery_alias = subquery.alias
            required = set()
            
            # Find all column references to this subquery in current node
            for col in node.find_all(exp.Column):
                if col.table == subquery_alias:
                    required.add(col.name)
            
            subquery_required_aliases[subquery_alias] = required
        
        # Check JOIN clauses for subqueries
        joins = node.args.get("joins")
        if joins:
            for join in joins:
                if isinstance(join.this, exp.Subquery):
                    subquery = join.this
                    subquery_alias = subquery.alias
                    required = set()
                    
                    # Find all column references to this subquery
                    for col in node.find_all(exp.Column):
                        if col.table == subquery_alias:
                            required.add(col.name)
                    
                    subquery_required_aliases[subquery_alias] = required
        
        # Recursively process nested selects with information about required aliases
        from_clause = node.args.get("from")
        if from_clause and isinstance(from_clause.this, exp.Subquery):
            subquery = from_clause.this
            subquery_alias = subquery.alias
            required = subquery_required_aliases.get(subquery_alias, set())
            self.clean_table_and_alias_refs(subquery.this, required)
        
        if joins:
            for join in joins:
                if isinstance(join.this, exp.Subquery):
                    subquery = join.this
                    subquery_alias = subquery.alias
                    required = subquery_required_aliases.get(subquery_alias, set())
                    self.clean_table_and_alias_refs(subquery.this, required)
        
        # Remove unused aliases from SELECT expressions
        final_expressions = []
        for expr in node.expressions:
            if isinstance(expr, exp.Alias):
                # Keep alias if it's used in this query OR required by parent query
                if expr.alias in used_aliases or expr.alias in parent_required_aliases:
                    final_expressions.append(expr)
                else:
                    # Remove alias, just keep the expression
                    final_expressions.append(expr.this)
            else:
                final_expressions.append(expr)
        
        node.set("expressions", final_expressions)
        
        return node

    def can_inline_subquery(self, subquery, parent):
        """
        Determine if a subquery can be safely inlined.
        A subquery can be inlined if:
        1. It's a simple SELECT that can be merged with parent
        2. The parent only references columns that exist in the subquery's projection
        3. Inlining won't make the query longer or more complex
        4. The parent doesn't use this subquery in a cross product with arithmetic operations
        """
        if not isinstance(subquery, exp.Subquery):
            return False
        
        select = subquery.this
        if not isinstance(select, exp.Select):
            return False
        
        arithmetic_exps = (
            exp.Add,
            exp.Sub,
            exp.Mul,
            exp.Div,
            exp.Mod,
            exp.Pow,
        )

        # Check if parent uses arithmetic operations AND has multiple tables (cross product)
        if isinstance(parent, exp.Select):
            has_arithmetic = any(
                isinstance(expr, arithmetic_exps) or 
                (isinstance(expr, exp.Alias) and isinstance(expr.this, arithmetic_exps))
                for expr in parent.expressions
            )
            
            # Count number of tables/subqueries in FROM and JOINs
            num_sources = 0
            from_clause = parent.args.get("from")
            if from_clause:
                num_sources += 1
            
            joins = parent.args.get("joins")
            if joins:
                num_sources += len(joins)
            
            # Only prevent inlining if there's arithmetic AND multiple sources (cross product scenario)
            # But we need to check if THIS specific subquery is referenced in the arithmetic
            if has_arithmetic and num_sources > 1:
                subquery_alias = subquery.alias
                # Check if this subquery is actually used in arithmetic expressions
                subquery_used_in_arithmetic = False
                for expr in parent.expressions:
                    if isinstance(expr, arithmetic_exps) or (isinstance(expr, exp.Alias) and isinstance(expr.this, arithmetic_exps)):
                        # Check if any column in this expression references our subquery
                        actual_expr = expr.this if isinstance(expr, exp.Alias) else expr
                        for col in actual_expr.find_all(exp.Column):
                            if col.table == subquery_alias:
                                subquery_used_in_arithmetic = True
                                break
                    if subquery_used_in_arithmetic:
                        break
                
                if subquery_used_in_arithmetic:
                    return False

        # Check if subquery has operations that prevent inlining
        has_groupby = select.args.get("group")
        has_having = select.args.get("having")
        has_order = select.args.get("order")
        has_limit = select.args.get("limit")
        has_where = select.args.get("where")
        has_distinct = select.args.get("distinct")
        has_joins = select.args.get("joins")
        
        # Can't inline if subquery has LIMIT, ORDER BY, DISTINCT, or HAVING
        # These would change semantics if merged with parent
        # if has_limit or has_order or has_distinct or has_having:
        if has_limit or has_order or has_distinct or has_groupby:
            return False
        
        # If subquery is just wrapping a simple projection, it can be inlined
        expressions = select.expressions
        
        # Check if it's a trivial wrapper (single level of indirection)
        if len(expressions) == 1 and not any([has_groupby, has_where, has_joins]):
            return True
        
        # Check if parent is just selecting from this subquery
        if isinstance(parent, exp.Select):
            # Parent should have minimal complexity for safe inlining
            parent_has_filters = any([
                parent.args.get("where"),
                parent.args.get("group"),
                parent.args.get("having"),
                parent.args.get("joins")
            ])
            
            # Can inline if parent just selects columns (no filters/aggregations)
            # Subquery WHERE and GROUP BY can be preserved when inlining
            if not parent_has_filters:
                # Check if parent only references columns from this subquery
                parent_refs_only_subquery = True
                subquery_alias = subquery.alias
                
                for expr in parent.expressions:
                    # Check all columns in the expression
                    for col in expr.find_all(exp.Column):
                        if col.table and col.table != subquery_alias:
                            parent_refs_only_subquery = False
                            break
                    if not parent_refs_only_subquery:
                        break
                
                if parent_refs_only_subquery:
                    return True
        
        return False


    def propagate_subquery_aliases(self, node, subquery_alias, alias_map):
        
        # print(repr(node))
        if isinstance(node, exp.Column) and node.table == subquery_alias:
            # Replace with expression from subquery
            col_name = node.name
            # print(col_name)
            # print(node)
            if col_name in alias_map:
                new_expr = alias_map[col_name].copy()
                # print(new_expr)
                # print(repr(node.parent))
                # Preserve the alias from parent if it exists
                # if isinstance(node.parent, exp.Alias):
                #     return exp.Alias(this=new_expr, alias=node.parent.alias)
                # else:
                #     return new_expr
                # print(type(new_expr))
                return new_expr
            else:
                return node
        else:
            return node


    def inline_subquery(self, parent_select, subquery, subquery_alias):
        """
        Inline a subquery into its parent SELECT.
        Replace references to subquery alias with actual expressions from subquery.
        """
        inner_select = subquery.this
        
        # Build mapping of subquery column aliases to their expressions
        alias_map = {}
        for expr in inner_select.expressions:
            if isinstance(expr, exp.Alias):
                alias_map[expr.alias] = expr.this
            elif isinstance(expr, exp.Column):
                alias_map[expr.name] = expr
        
        # Replace all column references to the subquery with actual expressions
        parent_select = parent_select.transform(
            lambda x: self.propagate_subquery_aliases(x, subquery_alias, alias_map)
        )
        
        # Copy the FROM clause from subquery to parent
        if inner_select.args.get("from"):
            parent_select.set("from", inner_select.args["from"].copy())
        
        # Copy WHERE clause from subquery to parent (merge if parent has WHERE)
        if inner_select.args.get("where"):
            subquery_where = inner_select.args["where"].copy()
            parent_where = parent_select.args.get("where")
            
            if parent_where:
                # Combine with AND
                combined_where = exp.And(this=parent_where.this, expression=subquery_where.this)
                parent_select.set("where", exp.Where(this=combined_where))
            else:
                parent_select.set("where", subquery_where)
        
        # Copy GROUP BY clause from subquery to parent
        if inner_select.args.get("group"):
            subquery_group = inner_select.args["group"].copy()
            parent_select.set("group", subquery_group)
        
        # Copy JOIN clauses from subquery to parent
        if inner_select.args.get("joins"):
            subquery_joins = [join.copy() for join in inner_select.args["joins"]]
            parent_joins = parent_select.args.get("joins")
            
            if parent_joins:
                parent_select.set("joins", parent_joins + subquery_joins)
            else:
                parent_select.set("joins", subquery_joins)
        
        return parent_select


    def simplify_subqueries(self, node, parent=None):
        """Recursively simplify subqueries by inlining where possible."""
        
        if not isinstance(node, exp.Select):
            return node
        
        # First, recursively process all nested subqueries (bottom-up approach)
        from_clause = node.args.get("from")
        if from_clause and isinstance(from_clause.this, exp.Subquery):
            subquery = from_clause.this
            # Recursively simplify the subquery itself first and update it
            simplified_inner = self.simplify_subqueries(subquery.this, subquery)
            subquery.set("this", simplified_inner)
        
        joins = node.args.get("joins")
        if joins:
            for join in joins:
                if isinstance(join.this, exp.Subquery):
                    subquery = join.this
                    # Recursively simplify the subquery itself first and update it
                    simplified_inner = self.simplify_subqueries(subquery.this, subquery)
                    subquery.set("this", simplified_inner)
        
        # Now try to inline subqueries at this level
        from_clause = node.args.get("from")
        if from_clause and isinstance(from_clause.this, exp.Subquery):
            subquery = from_clause.this
            subquery_alias = subquery.alias
            
            # Check if we can inline this subquery
            if self.can_inline_subquery(subquery, node):
                try:
                    # Inline the subquery - this modifies node in place and returns it
                    node = self.inline_subquery(node, subquery, subquery_alias)
                except Exception as e:
                    # If inlining fails, keep the subquery
                    import traceback
                    print(f"Failed to inline subquery: {e}")
                    traceback.print_exc()
        
        # Handle JOINs with subqueries (more complex, skip for now)
        # ...
        # print("SIMPLIFIED SQS:", node)
        return node
    
    def get_column_references(self, node, table_alias=None):
        """Get all column references in a node, optionally filtered by table alias."""
        refs = set()
        for col in node.find_all(exp.Column):
            if table_alias is None or col.table == table_alias:
                refs.add(col.name)
        return refs
    
    def get_column_alias_map(self, node, table_alias=None):
        """Get all column references in a node, optionally filtered by table alias."""
        alias_map = {}
        for a in node.find_all(exp.Alias):
            # if table_alias is None or col.table == table_alias:
                # refs.add(col.name)
                # pass
            alias_map[a.alias] = a.this
        return alias_map


    def remove_unused_aliases(self, node):
        """Remove aliases from subquery projections that are not referenced in parent queries."""
        
        if isinstance(node, exp.Select):
            # Get all subqueries in FROM and JOIN clauses
            subqueries = []
            
            # Check FROM clause
            from_clause = node.args.get("from")
            if from_clause and isinstance(from_clause.this, exp.Subquery):
                subqueries.append((from_clause.this, from_clause.this.alias))
            
            # Check JOIN clauses
            joins = node.args.get("joins")
            if joins:
                for join in joins:
                    if isinstance(join.this, exp.Subquery):
                        subqueries.append((join.this, join.this.alias))
            
            # For each subquery, determine which aliases are actually used
            for subquery, subquery_alias in subqueries:
                inner_select = subquery.this
                if not isinstance(inner_select, exp.Select):
                    continue
                
                # First, recursively process the subquery
                self.remove_unused_aliases(inner_select)
                
                # Get all column references to this subquery in the parent
                referenced_cols = self.get_column_references(node, subquery_alias)
                
                # Update subquery projections to remove unnecessary aliases
                new_expressions = []
                for expr in inner_select.expressions:
                    if isinstance(expr, exp.Alias):
                        # Keep alias only if it's referenced in parent
                        if expr.alias in referenced_cols:
                            new_expressions.append(expr)
                        else:
                            # Remove the alias, just keep the expression
                            new_expressions.append(expr.this)
                    else:
                        new_expressions.append(expr)
                
                inner_select.set("expressions", new_expressions)
        
        # Recursively process all child selects
        for child in node.find_all(exp.Select):
            if child != node:
                self.remove_unused_aliases(child)
        
        return node


    def find_common_subqueries(self, node):
        """Find and extract common subqueries that appear multiple times."""
        
        if not isinstance(node, exp.Select):
            return node, []
        
        # Collect all subqueries with their SQL representation
        subquery_map = {}  # sql_string -> (subquery_node, alias, parent_node, locations)
        subquery_counter = {}  # sql_string -> count
        
        def collect_subqueries(n, parent=None):
            """Recursively collect all subqueries."""
            if isinstance(n, exp.Select):
                # Check FROM clause
                from_clause = n.args.get("from")
                if from_clause and isinstance(from_clause.this, exp.Subquery):
                    sq = from_clause.this
                    sq_sql = sq.this.sql(pretty=False)
                    
                    if sq_sql not in subquery_map:
                        subquery_map[sq_sql] = []
                        subquery_counter[sq_sql] = 0
                    
                    subquery_counter[sq_sql] += 1
                    subquery_map[sq_sql].append({
                        'node': sq,
                        'alias': sq.alias,
                        'parent': n,
                        'location': 'from'
                    })
                
                # Check JOIN clauses
                joins = n.args.get("joins")
                if joins:
                    for i, join in enumerate(joins):
                        if isinstance(join.this, exp.Subquery):
                            sq = join.this
                            sq_sql = sq.this.sql(pretty=False)
                            
                            if sq_sql not in subquery_map:
                                subquery_map[sq_sql] = []
                                subquery_counter[sq_sql] = 0
                            
                            subquery_counter[sq_sql] += 1
                            subquery_map[sq_sql].append({
                                'node': sq,
                                'alias': sq.alias,
                                'parent': n,
                                'location': ('join', i)
                            })
            
            # Recurse on children
            for child in n.iter_expressions():
                collect_subqueries(child, n)
        
        collect_subqueries(node)
        
        # Find common subqueries (appearing more than once)
        common_subqueries = []
        for sq_sql, count in subquery_counter.items():
            if count > 1:
                instances = subquery_map[sq_sql]
                # Use the first alias or generate a new one
                common_alias = instances[0]['alias']
                common_subqueries.append({
                    'sql': sq_sql,
                    'alias': common_alias,
                    'instances': instances
                })
        
        return node, common_subqueries


    def deduplicate_common_subqueries(self, node):
        """Replace duplicate subqueries with references to a single instance."""
        
        node, common_subqueries = self.find_common_subqueries(node)
        
        if not common_subqueries:
            return node
        
        # For each common subquery, we need to restructure the query
        # This is complex in the general case, so we'll focus on the most common pattern:
        # Multiple identical subqueries in FROM/JOIN clauses at the same level
        
        for common in common_subqueries:
            instances = common['instances']
            
            # Check if all instances are at the same query level
            parents = [inst['parent'] for inst in instances]
            if len(set(id(p) for p in parents)) == 1:
                # All instances are in the same parent query
                parent = parents[0]
                
                # Replace all but the first instance with table references
                first_instance = instances[0]
                first_alias = first_instance['alias']
                
                for inst in instances[1:]:
                    old_alias = inst['alias']
                    
                    # Update all column references from old_alias to first_alias
                    parent.transform(
                        lambda n: exp.Column(
                            this=n.name,
                            table=first_alias
                        ) if isinstance(n, exp.Column) and n.table == old_alias else n
                    )
                    
                    # Remove the duplicate subquery
                    if inst['location'] == 'from':
                        # This is tricky - we can't easily remove FROM clause
                        pass
                    elif isinstance(inst['location'], tuple) and inst['location'][0] == 'join':
                        # Remove this join
                        joins = parent.args.get("joins")
                        if joins:
                            join_idx = inst['location'][1]
                            if join_idx < len(joins):
                                # Replace with a table reference instead
                                joins[join_idx] = exp.Join(
                                    this=exp.Table(this=first_alias),
                                    kind="CROSS"
                                )
        
        return node


def lowercase_except_quotes(text: str) -> str:
    """
    Lowercase all text except content within single quotes (regex sub version).
    """
    # Pattern to match single-quoted strings (handles escaped quotes '')
    quoted_pattern = r"'(?:[^']|'')*'"
    
    # Find all quoted strings and their positions
    quoted_strings = []
    for match in re.finditer(quoted_pattern, text):
        quoted_strings.append((match.start(), match.end(), match.group()))
    
    # Build result by lowercasing non-quoted parts
    result = []
    last_pos = 0
    
    for start, end, quoted in quoted_strings:
        # Lowercase the part before this quote
        result.append(text[last_pos:start].lower())
        # Keep the quoted part as-is
        result.append(quoted)
        last_pos = end
    
    # Lowercase any remaining text after the last quote
    result.append(text[last_pos:].lower())
    
    return ''.join(result)

def lowercase_sql_keywords_and_functions_safe(sql: str) -> str:
    # SQL keywords and aggregation functions to lowercase
    keywords = [
        "SELECT",
        "FROM",
        "WHERE",
        "JOIN",
        "INNER",
        "LEFT",
        "RIGHT",
        "FULL",
        "ON",
        "GROUP BY",
        "ORDER BY",
        "HAVING",
        "LIMIT",
        "OFFSET",
        "AS",
        "IN",
        "UNION",
        "EXCEPT",
        "INTERSECT",
        "AND",
        "OR",
        "NOT",
        "IS",
        "NULL",
        "ASC",
        "DESC",
        "LIKE",
        "BETWEEN",
        "CASE",
        "WHEN",
        "THEN",
        "ELSE",
        "END",
        "NULLS",
        "LAST",
        "DISTINCT",
        "REAL",
        "FLOAT"
    ]

    functions = [
        "COUNT",
        "SUM",
        "MAX",
        "MIN",
        "AVG",
        "STDDEV",
        "VARIANCE",
        "COALESCE",
        "ROUND",
        "CAST",
        "LENGTH",
        "UPPER",
        "LOWER",
        "ABS",
        "IFNULL",
        "SUBSTR",
        "JULIANDAY",
    ]

    # Sort longest first to avoid partial matching (e.g., 'IN' in 'INTERSECT')
    keyword_pattern = "|".join(sorted(map(re.escape, keywords), key=len, reverse=True))
    function_pattern = "|".join(
        sorted(map(re.escape, functions), key=len, reverse=True)
    )

    # Pattern to match:
    # - Group 1: quoted strings
    # - Group 2: SQL keywords not inside quotes
    # - Group 3: Function names followed by `(` (not part of identifiers)
    pattern = re.compile(
        rf"""
        (                             # Group 1: Quoted strings (preserve case)
            (?P<quote>['"])(?:\\.|[^\\])*?(?P=quote)
        )
        |
        (?<![\w.])                    # Not preceded by word char or dot
        (?P<keyword>{keyword_pattern})\b
        |
        (?<![\w.])                    # Not preceded by word char or dot
        (?P<func>{function_pattern})(?=\s*\()
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    def replacer(match):
        if match.group(1):  # quoted string
            return match.group(1)
        elif match.group("keyword"):
            return match.group("keyword").lower()
        elif match.group("func"):
            return match.group("func").lower()
        return match.group(0)

    return pattern.sub(replacer, sql)


def is_binary_alias_function(expr: exp.Expression) -> bool:
    if isinstance(expr, exp.Alias):
        expr = expr.this  # unwrap alias

    # Must be a binary operator (>, <, +, -, etc.)
    if not isinstance(expr, exp.Binary):
        return False

    left, right = expr.args.get("this"), expr.args.get("expression")

    # Both sides must be columns with table aliases
    if isinstance(left, exp.Column) and isinstance(right, exp.Column):
        return bool(left.table and right.table)
    return False


def simplify_sql(sql: str, dialect: str | None = "sqlite") -> str:
    """
    Return a simplified SQL string equivalent to `sql`.

    Parameters
    ----------
    sql : str
        Original query text.
    dialect : str, optional
        Force sqlglot dialect (e.g. "postgres").  If omitted, sqlglot guesses.

    Notes
    -----
    • The result is *semantically* identical for scalar-subquery cases and
      common Spider dataset patterns.  More exotic SQL constructs may be left
      untouched if a safe rewrite is ambiguous.
    """
    tree = sqlglot.parse_one(sql, read=dialect)
    
    simplified_tree = tree
    
    simplified_tree = Simplifier(simplified_tree).run()
    
    sql_out = simplified_tree.sql(pretty=False, dialect=dialect)
    
    return lowercase_except_quotes(sql_out)


# --------------------------------------------------------------------------- #
#                          command-line convenience                           #
# --------------------------------------------------------------------------- #
def _main() -> None:
    parser = argparse.ArgumentParser(description="Simplify SQL queries.")
    parser.add_argument(
        "query",
        nargs="?",
        help="SQL string (omit if using -f/--file)",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=argparse.FileType("r", encoding="utf-8"),
        help="Read SQL from file",
    )
    parser.add_argument(
        "-d",
        "--dialect",
        help="SQL dialect (postgres, snowflake, sqlite, ...)",
    )
    args = parser.parse_args()

    if not (args.query or args.file):
        parser.error("Provide a query string or --file")

    sql_input = args.query or args.file.read()
    print(simplify_sql(sql_input, dialect=args.dialect))


def compare_queries(og_q, simple_q, db_id):
    db_name = db_id.split("-")[0]
    db_fn = f"../evaluation/database/{db_name}/{db_name}.sqlite"
    conn = sqlite3.connect(db_fn)
    # for handling special chars in wta_1 db
    conn.text_factory = lambda x: str(x, "latin1")
    og_results = None
    simple_results = None
    try:
        og_results = conn.execute(og_q).fetchall()
        simple_results = conn.execute(simple_q).fetchall()
        # print(og_results)
        # print(simple_results)
        if og_results == simple_results:
            return 1
        else:
            # handle diff from replacing LEFT OUTER JOIN WITH JOIN
            # if og_q.count("LEFT OUTER JOIN") == simple_q.count("JOIN"):
            # return 1
            # else:
            # return 0
            return 0
    except:
        if og_results is not None:
            return -1
        else:
            print(og_q)
            print(simple_q)
            print(db_name)
            return -2
            # raise ValueError("Invalid original query")


def test_simplification(exs):
    query_diffs = []
    db_diffs = []
    simplified_exs = []
    for ex in tqdm(exs):
        # ex["db_id"] = ex["ring_id"].split("-")[0]
        try:
            og_query = ex.pop("sql")
        except:
            og_query = ex.pop("query")
            # og_query = ex["og_query"]
        # print(og_query)
        try:
            simplified_query = simplify_sql(og_query)
        except Exception as e:
            query_diffs.append(
                {
                    "og_query": og_query,
                    "simplified_query": None,
                    "error": str(e),
                    "db_id": ex["db_id"],
                }
            )
            continue
        # print(simplified_query)
        if og_query.lower().replace("asc", " ").replace(
            " ", ""
        ) != simplified_query.lower().replace(" ", ""):
            query_diffs.append(
                {
                    "og_query": og_query,
                    "simplified_query": simplified_query,
                    "db_id": ex["db_id"],
                }
            )

        ex["og_query"] = og_query
        ex["query"] = simplified_query

        # TODO: exec on db and check results for diffs
        # comparison = compare_queries(og_query, simplified_query, ex["db_id"])
        # if comparison != 1:
        #     db_diffs.append(
        #         {
        #             "og_query": og_query,
        #             "simplified_query": simplified_query,
        #             "db_id": ex["db_id"],
        #             "comparison": comparison,
        #         }
        #     )
        #     continue

        simplified_exs.append(ex)

    return simplified_exs, query_diffs, db_diffs


# TODO: 2 main issues to fix:
#   - removing alias that is used later (from a subquery or outer query that uses order by)
#   - weird handling of multiple subqueries combined with boolean operation?

if __name__ == "__main__":
    # _main()

    # SUBQEURY FILTER - seems ok
    # q1 = "SELECT Document_Description  FROM Documents, (SELECT max(Template_ID) AS c0  FROM Documents  WHERE Document_Description LIKE 'y%') AS t0  WHERE Document_Description LIKE '%y%' AND Template_ID < t0.c0 ORDER BY Document_Description DESC NULLS LAST  LIMIT 1"
    # q2 = "SELECT Document_Description  FROM Documents WHERE Document_Description LIKE '%y%' AND Template_ID < (SELECT max(Template_ID) FROM Documents  WHERE Document_Description LIKE 'y%') ORDER BY Document_Description DESC NULLS LAST  LIMIT 1"

    # IN plan - seems ok but could be simpler
    # remove "NULLS LAST" only for DESC (as it is default) but need to leave for ASC
    # TODO: FOR SPIDER MAY WANT TO ALWAYS REMOVE NULLS LAST SINCE THEY NEVER USE IT?
    # could also remove ASC as it is the default ordering?
    # q1 = "SELECT Documents.Template_ID, Documents.Document_Name  FROM Documents  WHERE (Documents.Document_ID NOT IN (SELECT Paragraphs.Document_ID AS c1  FROM Paragraphs)) ORDER BY Documents.Document_ID ASC NULLS LAST  LIMIT 3"

    # # SET PLANS
    # q1 = "SELECT Templates.Template_ID AS c1, Templates.Version_Number AS c0  FROM Templates JOIN Documents ON Templates.Template_ID = Documents.Template_ID  WHERE Documents.Document_Name LIKE 'Customer revi%' EXCEPT SELECT Templates.Template_ID AS c1, Templates.Version_Number AS c0  FROM Templates JOIN Documents ON Templates.Template_ID = Documents.Template_ID  WHERE Documents.Document_Name = 'Customer reviews'"
    # # q1 = "SELECT Templates.Template_ID AS c1, Templates.Version_Number AS c0  FROM Templates EXCEPT SELECT Templates.Template_ID AS c1, Templates.Version_Number AS c0  FROM Templates JOIN Documents ON Templates.Template_ID = Documents.Template_ID  WHERE Documents.Document_Name = 'Customer reviews'"
    # # q1 = "SELECT Template_ID, Version_Number FROM Templates EXCEPT SELECT T1.Template_ID, T1.Version_Number FROM Templates AS T1 JOIN Documents AS T2 ON T2.Template_ID = T1.Template_ID WHERE T2.Document_Name = 'Customer reviews'"

    # ISSUES WITH EXECUTION
    # q1 = "SELECT T1.killed ,  T1.injured FROM death AS T1 JOIN ship AS t2 ON T1.caused_by_ship_id  =  T2.id WHERE T2.tonnage  =  't'"

    # q1 = 'SELECT DISTINCT T1.LName FROM STUDENT AS T1 JOIN VOTING_RECORD AS T2 ON T1.StuID  =  PRESIDENT_Vote EXCEPT SELECT DISTINCT LName FROM STUDENT WHERE Advisor  =  "2192"'

    # q1 = "SELECT Roles.role_description , count(Employees.employee_id) FROM ROLES JOIN Employees ON Employees.role_code = Roles.role_code GROUP BY Employees.role_code HAVING count(Employees.employee_id)  >  1;"

    # q1 = "SELECT order_status_code, avg(customer_id)  FROM Customer_Orders, (SELECT max(order_date) AS c2  FROM Customer_Orders) AS t0  WHERE order_date < t0.c2 OR order_date > t0.c2 GROUP BY order_status_code  HAVING count(*) = 5 ORDER BY count(order_id) ASC NULLS LAST"

    # test for more consistent simplification
    # q1 = "SELECT Templates.Template_ID AS c1, Templates.Version_Number AS c0  FROM Templates JOIN Documents ON Templates.Template_ID = Documents.Template_ID  WHERE Documents.Document_Name LIKE 'Customer revi%' EXCEPT SELECT Templates.Template_ID AS c1, Templates.Version_Number AS c0  FROM Templates JOIN Documents ON Templates.Template_ID = Documents.Template_ID  WHERE Documents.Document_Name != 'Customer reviews'"
    # q1 = "SELECT Templates.Template_Type_Code, Templates.Template_ID, Templates.Version_Number, sum(Paragraphs.Document_ID)  FROM Templates JOIN Documents ON Templates.Template_ID = Documents.Template_ID JOIN Paragraphs ON Documents.Document_ID = Paragraphs.Document_ID WHERE Paragraphs.Document_ID != 1 GROUP BY Templates.Template_ID ORDER BY Templates.Template_Type_Code ASC NULLS LAST  LIMIT 1"
    # old result
    # "SELECT T1.Template_ID, T1.Version_Number FROM Templates AS T1 JOIN Documents AS T2 ON T2.Template_ID = T1.Template_ID WHERE T2.Document_Name LIKE 'Customer revi%' EXCEPT SELECT T1.Template_ID, T1.Version_Number FROM Templates AS T1 JOIN Documents AS T2 ON T2.Template_ID = T1.Template_ID WHERE T2.Document_Name = 'Customer reviews'"

    # q1 = "SELECT Citation.cited_paper_id, Citation.paper_id, Paper.year  FROM Citation JOIN Paper ON Citation.paper_id = Paper.paper_id JOIN Author_list ON Paper.paper_id = Author_list.paper_id  WHERE Author_list.affiliation_id > 2068 OR Author_list.affiliation_id >= 1519"
    # q1 = "SELECT _, _, _  FROM _ JOIN _ ON _ = _ JOIN _ ON _ = _  WHERE _ > _ OR _ >= _"


    # TODO: better handle with
    # q1 = "WITH PropertyRecommendations AS (\n  SELECT \n    p.property_id, \n    p.property_type, \n    p.sale_price, \n    p.lot_area, \n    p.overall_qual,\n    r.score,\n    ROW_NUMBER() OVER (PARTITION BY p.property_type ORDER BY r.score DESC) AS recommendation_rank\n  FROM \n    properties p\n  INNER JOIN \n    recommendations r ON p.property_id = r.property_id\n  WHERE \n    r.score > 0.9\n),\nRecentAccessCounts AS (\n  SELECT \n    property_id, \n    COUNT(*) AS num_accesses\n  FROM \n    access_logs\n  WHERE \n    access_date >= '2023-01-01'\n  GROUP BY \n    property_id\n)\nSELECT \n  pr.property_type, \n  pr.property_id, \n  pr.sale_price, \n  pr.lot_area, \n  pr.overall_qual, \n  COALESCE(rac.num_accesses, 0) AS num_accesses\nFROM \n  PropertyRecommendations pr\n  LEFT JOIN RecentAccessCounts rac ON pr.property_id = rac.property_id\nWHERE \n  pr.recommendation_rank <= 3\nORDER BY \n  pr.score DESC\nLIMIT 5;"

    # q1 = "SELECT count(*) * sum(t1.c1 * t0.c2) - (sum(t1.c1) * sum(t0.c2)) / CAST(sqrt((count(*) * sum(t1.c1 * t1.c1) - pow(sum(t1.c1), 2)) * (count(*) * sum(t0.c2 * t0.c2) - pow(sum(t0.c2), 2))) AS NUMERIC) > 100 AS c0  FROM (SELECT VOTES.contestant_number AS c1, VOTES.vote_id AS c3  FROM VOTES) AS t1, (SELECT VOTES.phone_number AS c2, VOTES.vote_id AS c3  FROM VOTES) AS t0"

    # q1 = "SELECT t1.c1 > t0.c1 AS c2  FROM (SELECT players.player_id AS c0, max(matches.winner_rank_points) AS c1  FROM players JOIN matches ON players.player_id = matches.winner_id  WHERE players.player_id = 220421 AND matches.winner_rank_points > 2375 GROUP BY players.player_id) AS t1, (SELECT players.player_id AS c0, max(matches.winner_rank_points) AS c1  FROM players JOIN matches ON players.player_id = matches.winner_id  WHERE players.player_id = 209287 GROUP BY players.player_id) AS t0"

    # q1 = "SELECT t2.c3 - t0.c1 AS c0  FROM (SELECT min(t1.c1) AS c3  FROM (SELECT Ref_Property_Types.property_type_code AS c2, max(Properties.room_count) AS c1  FROM Ref_Property_Types JOIN Properties ON Ref_Property_Types.property_type_code = Properties.property_type_code GROUP BY Ref_Property_Types.property_type_code) AS t1) AS t2, (SELECT Ref_Property_Types.property_type_code AS c2, max(Properties.room_count) AS c1  FROM Ref_Property_Types JOIN Properties ON Ref_Property_Types.property_type_code = Properties.property_type_code  WHERE Ref_Property_Types.property_type_code = 'Shop' AND Properties.property_name LIKE '%e c%' GROUP BY Ref_Property_Types.property_type_code) AS t0"

    # q1 = "SELECT t1.c1 > t0.c1 AS c2  FROM (SELECT players.player_id AS c0, max(matches.winner_rank_points) AS c1  FROM players JOIN matches ON players.player_id = matches.winner_id  WHERE players.player_id < 220421 GROUP BY players.player_id ORDER BY players.player_id ASC LIMIT 1) AS t1, (SELECT players.player_id AS c0, max(matches.winner_rank_points) AS c1  FROM players JOIN matches ON players.player_id = matches.winner_id  WHERE players.player_id < 209287 GROUP BY players.player_id ORDER BY players.player_id DESC LIMIT 1) AS t0"
    # target_output = "SELECT (SELECT max(matches.winner_rank_points) FROM players JOIN matches ON players.player_id = matches.winner_id  WHERE players.player_id < 220421 GROUP BY players.player_id ORDER BY players.player_id LIMIT 1) > (SELECT max(matches.winner_rank_points) FROM players JOIN matches ON players.player_id = matches.winner_id  WHERE players.player_id < 209287 GROUP BY players.player_id ORDER BY players.player_id DESC LIMIT 1) AS c2"

    # q1 = "SELECT t1.c1 > t0.c1 AS c2  FROM (SELECT players.player_id AS c0, max(matches.winner_rank_points) AS c1  FROM players JOIN matches ON players.player_id = matches.winner_id  WHERE players.player_id = 220421 AND matches.winner_rank_points > 2375 GROUP BY players.player_id) AS t1, (SELECT players.player_id AS c0, max(matches.winner_rank_points) AS c1  FROM players JOIN matches ON players.player_id = matches.winner_id  WHERE players.player_id = 209287 GROUP BY players.player_id) AS t0"

    # q1 = "SELECT t1.c1 > t0.c1 as c0 FROM (SELECT MAX(points) AS c1 FROM matches as ta) AS t1, (SELECT MAX(points) AS c1 FROM matches2 as tb) AS t0"
    # target = "select (select max(points) from matches) > (select max(points) from matches2)"

    # q1 = "SELECT t2.c3 - t0.c1 AS c2  FROM (SELECT max(t1.c1) AS c3  FROM (SELECT CONTESTANTS.contestant_number AS c0, avg(VOTES.phone_number) AS c1  FROM CONTESTANTS JOIN VOTES ON CONTESTANTS.contestant_number = VOTES.contestant_number GROUP BY CONTESTANTS.contestant_number) AS t1) AS t2, (SELECT CONTESTANTS.contestant_number AS c0, avg(VOTES.phone_number) AS c1  FROM CONTESTANTS JOIN VOTES ON CONTESTANTS.contestant_number = VOTES.contestant_number  WHERE CONTESTANTS.contestant_number = 1 AND VOTES.phone_number BETWEEN 6209222712 AND 7182887233 GROUP BY CONTESTANTS.contestant_number) AS t0"

    # q1 = "SELECT VOTES.created AS c2, VOTES.phone_number AS c1  FROM VOTES, (SELECT max(t0.c1) AS c0  FROM (SELECT VOTES.phone_number AS c1, VOTES.vote_id AS c3  FROM VOTES) AS t0) AS t1  WHERE VOTES.phone_number = t1.c0"
    # target = "select created, phone_number from votes where phone_number = (select max(phone_number) from votes)"

    # q1 = "SELECT t0.c1 AS c3, count(DISTINCT (t0.c0)) AS c2  FROM (SELECT VOTES.state AS c1, VOTES.vote_id AS c0  FROM VOTES) AS t0 GROUP BY t0.c1 ORDER BY c2 DESC NULLS LAST  LIMIT 1"
    # target = "select state as c3, count(distinct (vote_id)) as c2 from votes group by c3 order by c2 desc limit 1"
    

    # DONE?: don't mess with set comparisons???
    # q1 = "SELECT t2.c1 - t0.c3 AS c2  FROM (SELECT max(t1.c3) AS c1  FROM (SELECT Staff_in_Meetings.staff_id AS c3, Staff_in_Meetings.meeting_id AS c0  FROM Staff_in_Meetings  WHERE Staff_in_Meetings.staff_id > 8) AS t1) AS t2, (SELECT Staff_in_Meetings.staff_id AS c3, Staff_in_Meetings.meeting_id AS c0  FROM Staff_in_Meetings  WHERE Staff_in_Meetings.meeting_id = 2) AS t0"

    # q1 = "SELECT t2.c1 - t0.c2 AS c3  FROM (SELECT max(t1.c2) AS c1  FROM (SELECT Asset_Parts.part_id AS c2, Asset_Parts.asset_id AS c0  FROM Asset_Parts  WHERE Asset_Parts.part_id > 1) AS t1) AS t2, (SELECT Asset_Parts.part_id AS c2, Asset_Parts.asset_id AS c0  FROM Asset_Parts  WHERE Asset_Parts.asset_id = 1) AS t0"

    # q1 = "SELECT min(t0.c2) AS c0, max(t0.c2) AS c1  FROM (SELECT TV_series.share AS c2, TV_series.id AS c3  FROM TV_series  WHERE TV_series.channel LIKE '%700%') AS t0"

    # DONE?: leave cast for pct change questions
    # q1 = "SELECT (min(t0.c0) / CAST(CAST(min(t1.c0) AS FLOAT) AS FLOAT) - 1) * 100 AS c1  FROM (SELECT AREA_CODE_STATE.area_code AS c2, min(VOTES.phone_number) AS c0  FROM AREA_CODE_STATE JOIN VOTES ON AREA_CODE_STATE.state = VOTES.state  WHERE VOTES.created = '2018-03-09 19:03:36' AND VOTES.contestant_number >= 2 GROUP BY AREA_CODE_STATE.area_code) AS t0, (SELECT AREA_CODE_STATE.area_code AS c2, min(VOTES.phone_number) AS c0  FROM AREA_CODE_STATE JOIN VOTES ON AREA_CODE_STATE.state = VOTES.state  WHERE VOTES.created = '2018-03-09 19:03:39' AND VOTES.contestant_number >= 2 GROUP BY AREA_CODE_STATE.area_code) AS t1"


    # # q1 = "SELECT t0.c1 FROM (SELECT MAX(col) AS c1 FROM table1) AS t0"


    # # q1 = "SELECT t1.c0 - t0.c3 AS c2  FROM (SELECT Students.date_left AS c0, Students.student_id AS c1  FROM Students  WHERE Students.cell_mobile_number = '(213)445-0399x85208' AND Students.cell_mobile_number = '(213)445-0399x85208') AS t1, (SELECT Students.date_first_registered AS c3, Students.student_id AS c1  FROM Students) AS t0"

    
    # # DONE: remove unecessary table names in accessing, fix aliasing in outer query - remove if possible or keep to reuse if better
    # q1 = "SELECT t0.c0 AS c1, count(DISTINCT (t0.c0)) AS c2  FROM (SELECT stadium.stadium_id AS c0  FROM stadium) AS t0 GROUP BY t0.c0 ORDER BY c2 DESC NULLS LAST  LIMIT 1"
    # # # current = "select stadium.stadium_id as c1, count(distinct (stadium.stadium_id)) as c2 from stadium group by stadium.stadium_id order by c2 desc limit 1"
    # # # target = "select stadium_id as c1, count(DISTINCT (stadium_id)) as c2 from stadium group by c1, order by c2 desc limit 1"


    # q1 = "SELECT t0.c0 > 7165647136.5 AS \"greaterthan(t0//average(Votes//phone_number),7165647136.5)\"  FROM (SELECT AREA_CODE_STATE.area_code AS c1, avg(VOTES.phone_number) AS c0  FROM AREA_CODE_STATE JOIN VOTES ON AREA_CODE_STATE.state = VOTES.state  WHERE AREA_CODE_STATE.area_code = 781 GROUP BY AREA_CODE_STATE.area_code) AS t0"
    # target = "select t0.c0 > 7165647136.5 from (select avg(t1.phone_number) as c0 from AREA_CODE_STATE as t0 join VOTES as t1 on t0.state = t1.state where t0.area_code = 781 group by t0.area_code) as t0"


    # q1 = "SELECT t2.c0 - t0.c1 AS c2  FROM (SELECT min(t1.c1) AS c0  FROM (SELECT AREA_CODE_STATE.area_code AS c3, avg(VOTES.contestant_number) AS c1  FROM AREA_CODE_STATE JOIN VOTES ON AREA_CODE_STATE.state = VOTES.state  WHERE VOTES.phone_number < 6209222712 GROUP BY AREA_CODE_STATE.area_code) AS t1) AS t2, (SELECT AREA_CODE_STATE.area_code AS c3, avg(VOTES.contestant_number) AS c1  FROM AREA_CODE_STATE JOIN VOTES ON AREA_CODE_STATE.state = VOTES.state  WHERE AREA_CODE_STATE.area_code = 912 GROUP BY AREA_CODE_STATE.area_code) AS t0"


    # q1 = "select t1.c0 > t0.c0 from (select created as c0 from VOTES where vote_id = 2) as t1, (select created as c0 from VOTES where vote_id = 1) as t0"
    # q1 = "SELECT t2.c1 - t0.c2 AS c3  FROM (SELECT max(t1.c2) AS c1  FROM (SELECT VOTES.phone_number AS c2, VOTES.vote_id AS c0  FROM VOTES  WHERE VOTES.state LIKE '%A%') AS t1) AS t2, (SELECT VOTES.phone_number AS c2, VOTES.vote_id AS c0  FROM VOTES  WHERE VOTES.vote_id = 5) AS t0"

    # sq1 = simplify_sql(q1, dialect="sqlite")
    
    # print(sq1)

    # sq2 = Simplifier(sqlglot.parse_one(sq1, read="sqlite")).run()
    # sql_out = sq2.sql(pretty=False, dialect="sqlite")
    # sql_out =  lowercase_sql_keywords_and_functions_safe(sql_out)
    # print(sql_out)

    # print()
    # #
    # sq2 = simplify_sql(q2, dialect="sqlite")
    # print(sq2)

    ############################################################################
    #
    # for running on full dataset
    # 
    ############################################################################

    import os
    import json
    import numpy as np
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_dir",
        # default="generated_data/satdb_from_bps_final",
        # default="generated_data/satdb_from_spider_full_3x_simplified_v7_improved",
        # TODO: check that proper query field is used
    )
    args = parser.parse_args()

    input_dir = args.input_dir
    # TODO: fix comparator order for = seems to reverse order?
    # TODO: will need to replace LEFT OUTER JOINS with JOIN - check satyrn sql simplifier for more cases like this?

    # base_dir = "generated_data/spider/full_splits"
    # base_dir = (
    #     "generated_data/satdb_from_spider_full_3x_simplified_v6/qq_few_shot_rephrased"
    # )

    # base_dir = "generated_data/satdb_v6_from_bps/splits_clean"
    # base_dir = "test_new_templates/simplified_sql/"

    # base_dir = "generated_data/satdb_from_spider_full_3x_simplified_v7/splits_clean"
    # base_dir = os.path.join(input_dir, "splits_clean")
    base_dir = input_dir

    # out_dir = os.path.join(input_dir, "standardized_sample")
    out_dir = os.path.join(input_dir, "standardized")
    # out_dir = os.path.join(input_dir, "standardized_updated_rephrased")
    # out_dir = os.path.join(input_dir, "standardized_sample")
    # out_dir = os.path.join(input_dir, "splits_raw/standardized_removing_with")
    os.makedirs(
        out_dir,
        exist_ok=True,
    )
    for split in ["dev.json", "test.json", "train.json"]:
    # for split in ["test.json"]:
    # for split in ["train.json"]:
        # examples = json.load(open(os.path.join(base_dir, "simplified_sql_updated_clean", split), "r"))
        examples = json.load(open(os.path.join(base_dir, "splits_clean", split), "r"))
        # examples = json.load(open(os.path.join(base_dir, "sampled_data", split), "r"))


        # examples = json.load(open(os.path.join(base_dir, "sampled_data", split), "r"))
        # examples = json.load(open(os.path.join(base_dir, "splits_raw", split), "r"))["data"]
        all_exs, query_diffs, db_diffs = test_simplification(examples)
        print("SPLIT:", split)
        print("TOTAL EXS:", len(all_exs))
        print("CHANGED QUERIES:", len(query_diffs))
        print("CHANGED RESULTS:", len(db_diffs))

        json.dump(all_exs, open(os.path.join(out_dir, split), "w"))
        json.dump(
            query_diffs, open(os.path.join(out_dir, "diff_queries_" + split), "w")
        )
        json.dump(db_diffs, open(os.path.join(out_dir, "diff_results_" + split), "w"))

        avg_og_len = np.mean([len(ex["og_query"]) for ex in all_exs])
        avg_simplified_len = np.mean([len(ex["query"]) for ex in all_exs])

        print("AVG OG LEN:", avg_og_len)
        print("AVG SIMPLIFIED LEN:", avg_simplified_len)
        print(
            f"{100 - avg_simplified_len * 100/ avg_og_len :.2f}% SHORTER ({avg_og_len - avg_simplified_len} chars on average)"
        )
        print()
