"""
Script for converting spider databases to Satyrn V2 rings. Takes one argument: path to a folder containing spider sqlite files.
"""

import re, glob, json, os, uuid
import argparse
from functools import reduce
from sqlalchemy import create_engine, MetaData

type_dict = {
    "int": "integer",
    "integer": "integer",
    "mediumint": "integer",
    "smallint": "integer",
    "tinyint": "integer",
    "bigint": "integer",
    "year": "integer",
    "text": "string",
    "varchar": "string",
    "varchar2": "string",
    "char": "string",
    # "blob": "string",
    "float": "float",
    "real": "float",
    "number": "float",
    "numeric": "float",
    "decimal": "float",
    "double": "float",
    "datetime": "datetime",
    "date": "datetime",
    "timestamp": "datetime",
    "boolean": "boolean",
    "bool": "boolean",
    "bit": "boolean",
    "null": "boolean",
    "blob": "document"
}

attr_type_dict = {
    "integer": ["Arithmetic", "Metric"],
    "float": ["Arithmetic", "Metric"],
    "string": ["Categorical"],
    "boolean": ["Categorical"],
    "document": ["Document"],
    "datetime": ["Datetime"]
}

def build_rings(paths):
    for path in paths:
        for filename in glob.iglob(os.path.join(path, '**/*.sqlite'), recursive=True):
            print(filename)

            # Data Source
            data_source = {
                "type": "sqlite",
                "connectionString": filename
            }

            engine = create_engine(f'sqlite:///{filename}')
            m = MetaData()
            m.reflect(engine)

            columns = {}
            for table in m.tables.values():
                columns[table.name] = {}
                for column in table.c:
                    columns[table.name][column.name] = type_dict[str(column.type).partition('(')[0].lower()]

            data_source["tables"] = [
                {
                    "name": table.name,
                    "primaryKey": {column.name.lower():columns[table.name][column.name] for column in table.primary_key.columns} if table.primary_key \
                        else {table.columns[0].name:columns[table.name][table.columns[0].name]}
                } for table in m.tables.values()
            ]

            data_source["joins"] = [
                {
                    "name": f"{fk.constraint.parent.name}.{fk.constraint.column_keys[0]}->{fk.target_fullname.split('.')[0]}.{fk.target_fullname.split('.')[1]}",
                    "from": fk.constraint.parent.name,
                    "to": fk.target_fullname.split('.')[0],
                    "path": [
                        [
                            f"{fk.constraint.parent.name}.{fk.constraint.column_keys[0].lower()}",
                            f"{fk.target_fullname.split('.')[0]}.{fk.target_fullname.split('.')[1].lower()}",
                            columns[fk.constraint.parent.name][fk.constraint.column_keys[0]]
                        ]
                    ]
                } for fk in reduce(lambda a, table: a.union(table.foreign_keys), m.tables.values(), set())
            ]

            # Ontology
            entities = []
            for table in data_source['tables']:
                entity_nicename = ' '.join(word.capitalize() for word in table["name"].split('_'))
                entity = {
                    "name": entity_nicename.replace(' ', ''),
                    "nicename": [
                        entity_nicename,
                        entity_nicename + 's' # Use GPT for plurality here instead
                    ],
                    "table": table["name"],
                    "id": list(table['primaryKey'].keys()),
                    "idType": list(table['primaryKey'].values()),
                    "reference": " ".join(f"{{{pk}}}" for pk in table['primaryKey'].keys()),
                    "metrics": [],
                    "attributes": {}
                }
                for col_name, col_type in columns[table['name']].items():
                    attribute_nicename = ' '.join(word.capitalize() for word in col_name.split('_'))
                    attribute = {
                        "nicename": [
                            attribute_nicename,
                            attribute_nicename + 's' # Use GPT for plurality here instead
                        ],
                        "isa": columns[table['name']][col_name],
                        "type": attr_type_dict[columns[table['name']][col_name]].copy(),
                        "source": {
                            "table": table['name'],
                            "columns": [col_name.lower()]
                        }
                    }
                    if col_name.lower() in table['primaryKey'].keys():
                        if len(table['primaryKey']) == 1:
                            attribute['type'] = ['Categorical', 'Identifier']
                        else:
                            attribute['type'] = ['Categorical', 'CompositeIdentifier']
                    entity["attributes"][col_name] = attribute
                entities.append(entity)

            relationships = []
            for join in data_source['joins']:
                relationship = {
                    "from": ''.join(word.capitalize() for word in join['from'].split('_')),
                    "to": ''.join(word.capitalize() for word in join['to'].split('_')),
                    "join": [join['name']],
                    "relation": "m2o"
                }
                relationship['name'] = f"{relationship['from']}.{''.join(word.capitalize() for word in join['path'][0][0].rpartition('.')[2].split('_'))}->{relationship['to']}.{''.join(word.capitalize() for word in join['path'][0][1].rpartition('.')[2].split('_'))}"
                relationships.append(relationship)

            ring_name = filename.split("/")[-2]
            ring_id = f'{ring_name}-{uuid.uuid4()}'
            with open(f'./{ring_name}.json', 'w') as f:
                json.dump({
                        "rid": ring_id,
                        "name": ' '.join(word.capitalize() for word in ring_name.split('_')),
                        "description": "",
                        "version": 1,
                        "schemaVersion": 2.1,
                        "dataSource": data_source,
                        "ontology": {
                            # "defaultTargetEntity": "",
                            "relationships": relationships,
                            "entities": entities
                        }
                    }, f, indent=4)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='create rings from spider dataset schemas.')
    parser.add_argument('path', type=str, nargs='+', help='path to the spider dataset.')
    args = parser.parse_args()

    build_rings(args.path)
