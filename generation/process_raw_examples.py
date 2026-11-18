import os
import traceback
import re
import sys
import json
import sqlite3
import sqlparse
import random
from os import listdir, makedirs
from collections import OrderedDict
from nltk import word_tokenize, tokenize
from os.path import isfile, isdir, join, split, exists, splitext
import argparse

# from process_sql import get_sql


class Schema:
    """
    Simple schema which maps table&column to a unique identifier
    """

    def __init__(self, schema, table):
        self._schema = schema
        self._table = table
        self._idMap = self._map(self._schema, self._table)

    @property
    def schema(self):
        return self._schema

    @property
    def idMap(self):
        return self._idMap

    def _map(self, schema, table):
        column_names_original = table["column_names_original"]
        table_names_original = table["table_names_original"]
        # print 'column_names_original: ', column_names_original
        # print 'table_names_original: ', table_names_original
        for i, (tab_id, col) in enumerate(column_names_original):
            if tab_id == -1:
                idMap = {"*": i}
            else:
                key = table_names_original[tab_id].lower()
                val = col.lower()
                idMap[key + "." + val] = i

        for i, tab in enumerate(table_names_original):
            key = tab.lower()
            idMap[key] = i

        return idMap


def get_schemas_from_json(fpath):
    with open(fpath) as f:
        data = json.load(f)
    db_names = [db["db_id"] for db in data]

    tables = {}
    schemas = {}
    for db in data:
        db_id = db["db_id"]
        schema = {}  # {'table': [col.lower, ..., ]} * -> __all__
        column_names_original = db["column_names_original"]
        table_names_original = db["table_names_original"]
        tables[db_id] = {
            "column_names_original": column_names_original,
            "table_names_original": table_names_original,
        }
        for i, tabn in enumerate(table_names_original):
            table = str(tabn.lower())
            cols = [str(col.lower()) for td, col in column_names_original if td == i]
            schema[table] = cols
        schemas[db_id] = schema

    return schemas, db_names, tables


def process_one(ex, table_file="../../generation/generated_data/satdb_v1/tables.json"):
    # sql = "SELECT name ,  country ,  age FROM singer ORDER BY age DESC WHERE age > 30 AND country = 'USA'"
    # db_id = "concert_singer"
    # table_file = "tables.json"
    # question = "Show name, country, age for all singers ordered by age from the oldest to the youngest."
    ex = ex.copy()
    sql = ex["query"]
    db_id = ex["db_id"]
    question = ex["question"]
    # print(sql)

    ex["query_toks"] = tokenize.word_tokenize(sql)
    ex["question_toks"] = tokenize.word_tokenize(question)
    ex["query_toks_no_value"] = tokenize.word_tokenize(
        re.sub(r"'(.*?)'|[0-9]+", "value", sql).lower()
    )

    # print(ex)

    # schemas, db_names, tables = get_schemas_from_json(table_file)
    # schema = schemas[db_id]
    # table = tables[db_id]
    # schema = Schema(schema, table)
    # sql_label = get_sql(schema, sql)

    # print(sql_label)
    return ex


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--dir_in", type=str)
    parser.add_argument("--dir_out", type=str)
    args = parser.parse_args()

    dir_in = args.dir_in
    dir_out = args.dir_out

    err_count = 0
    success_count = 0
    for d in os.listdir(dir_in):
        print(d)
        # ignore files for now but could fix if needed
        if os.path.isdir(os.path.join(dir_in, d)):
            for fn in os.listdir(os.path.join(dir_in, d)):
                data = json.loads(open(os.path.join(dir_in, d, fn), "r").read())
                results = []
                for ex in data:
                    try:
                        results.append(process_one(ex))
                        success_count += 1
                    except Exception as e:
                        # print(ex)
                        raise e
                        err_count += 1
                if not os.path.exists(os.path.join(dir_out, d)):
                    os.makedirs(os.path.join(dir_out, d))
                f = open(os.path.join(dir_out, d, fn), "w")
                f.write(json.dumps(results))
        else:
            if not d.startswith(".") and d.endswith(".json"):
                data = json.loads(open(os.path.join(dir_in, d), "r").read())
                results = []
                for ex in data:
                    try:
                        results.append(process_one(ex))
                        success_count += 1
                    except Exception as e:
                        # print(ex)
                        raise e
                        err_count += 1
                if not os.path.exists(os.path.join(dir_out)):
                    os.makedirs(os.path.join(dir_out))
                f = open(os.path.join(dir_out, d), "w")
                f.write(json.dumps(results))

    print(err_count, "TOTAL ERRORS")
    print(success_count, "SUCCEEDED")
