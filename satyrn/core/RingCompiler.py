"""
This file is part of Satyrn.
Satyrn is free software: you can redistribute it and/or modify it under 
the terms of the GNU General Public License as published by the Free Software Foundation, 
either version 3 of the License, or (at your option) any later version.
Satyrn is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with Satyrn. 
If not, see <https://www.gnu.org/licenses/>.
"""

import os
import json
import datetime
from typing import List, Dict, Tuple, Union

import sqlalchemy as sa
from sqlalchemy import Column, ForeignKey, String, DateTime, Date, Text
from sqlalchemy.orm import column_property
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import extract, cast

# try:
#     from RingInterface import RingInterface
# except:
#     from .RingInterface import RingInterface

try:
    from api import sql_func
except:
    from satyrn.core.api import sql_func

# Import for sqlite extension
try:
    from satyrnBundler import app
except:
    from satyrn.core.satyrnBundler import app

try:
    from api.utils import rel_math, mirror_rel, walk_rel_path
except:
    from satyrn.core.api.utils import rel_math, mirror_rel, walk_rel_path
# end of stuff for sqlite extension

try:
    from satyrn.core.RingObjects.Ring import Ring
    from satyrn.core.RingObjects.RingAttribute import RingAttribute
    from satyrn.core.RingObjects.RingEntity import RingEntity
    from RingDB import DBWrapper
    from satyrn.core.DatabaseInterface import DatabaseInterface
    from satyrn.core.RingAugmentor import RingAugmentor
    from satyrn.core.Analysis.OperationOntology import OperationOntology
except:
    from .RingObjects.Ring import Ring
    from .RingObjects.RingAttribute import RingAttribute
    from .RingObjects.RingEntity import RingEntity
    from .RingDB import RingDB
    from .DatabaseInterface import DatabaseInterface
    from .RingAugmentor import RingAugmentor
    from .Analysis.OperationOntology import OperationOntology


class RingCompiler(object):
    """
    Generates the ORM (the connection to the database).
    """

    def __init__(self, ring: Ring):
        self.ring = ring
        self.db = None

        # Get upper ontology
        default_path = (
            os.environ.get("SATYRN_ROOT_DIR")
            + "/"
            + "core"
            + "/"
            + "upperOntology.json"
        )
        with open(default_path, "r") as file:
            defaults = json.load(file)
            self.upper_ontology = defaults
            self.upper_ontology.update(UPPER_ONTOLOGY)

    def build_orm(self) -> RingDB:
        """
        Builds the connection between the ring configuration and the database via SQL Alchemy.
        :return: The database wrapper object that gives access to the SQL Alchemy session and tables.
        :rtype: RingDB
        """

        # Init a wrapper object whose props will be filled in soon
        self.db = RingDB()
        if self.ring.data_source.spark_address:
            self.db.spark = self.ring.data_source.make_apache_spark_connection()

        # Create the SQL Alchemy models
        models, relationship_list = self.build_models()

        # Add each model we created to the database wrapper
        for model in models:
            setattr(self.db, model.__name__, model)

        # Create a session that can be used for running queries against the database
        self.db.eng, self.db.session_maker = self.ring.data_source.make_connection(
            self.db
        )  # PENDING: Maybe pass model here or check if corresponding csv

        # Creates the tables from the SQL Alchemy model definitions
        # self.ring.data_source.base.metadata.create_all(self.db.eng) # pretty sure this isn't necessary since we aren't actually creating any new database tables

        # Build the SQL Alchemy relationship columns and add them to the SQL Alchemy entities
        self.populate_relationships(relationship_list)

        return self.db

    def build_models(self) -> Tuple[list, list]:
        """
        Generates a mapping from Satyrn entities to SQL Alchemy specifications and uses that to generate the SQL Alchemy models.
        :return: A list of SQL Alchemy models along with the relationships to link them with.
        :rtype: Tuple[List, List]
        """

        # Check configuration for validity before constructing models
        if not self.ring.is_valid()[0]:
            raise ValueError(self.ring.is_valid()[1])

        # Build the model stubs with the table name and primary key(s)
        model_map = {}
        for table in self.ring.data_source.tables:
            model_map[table["name"]] = {
                "__tablename__": table["name"],
            }
            for pk_col_name, pk_col_type in table["primaryKey"].items():
                model_map[table["name"]][pk_col_name] = self.column_with_type(
                    pk_col_type, primary_key=True
                )

        # Create the joins and determine the relationships between the tables, upstream of per-entity stuff
        model_map, relationship_list = (
            self.add_joins_to_model_map_and_create_relationship_list(model_map)
        )

        # Generate the SQLAlchemy Attributes for each of the entities
        for entity in self.ring.entities:
            model_map = self.populate_models_from_entity(entity, model_map)

        # Create the ORM models dynamically from the model map
        models = [
            type(name, (self.ring.data_source.base,), model_info)
            for name, model_info in model_map.items()
        ]

        return models, relationship_list

    def populate_models_from_entity(self, entity: RingEntity, model_map: dict) -> dict:
        """
        Prepare the attributes for the entity using SQLAlchemy.
        :param entity: The entity whose attributes are being added to the model map.
        :type entity: RingEntity
        :param model_map: The mapping used to create the SQL Alchemy ORM.
        :type model_map: dict
        :return: The updated model_map dictionary.
        :rtype: dict
        """
        # Add entity id keys if they don't exist already
        for id_key, id_type in zip(entity.id, entity.id_type):
            if id_key not in model_map[entity.primary_table]:
                model_map[entity.primary_table][id_key] = self.column_with_type(id_type)

        # Add entity attributes
        for attribute in entity.attributes.values():
            base_type = self.resolve_base_type(attribute.isa)
            for sc in attribute.source_columns:
                if sc not in model_map[attribute.source_table]:
                    # TODO (Cameron): When implementing multi-column attributes, it doesn't overwrite the previously created column.
                    #       Thus, the order of the attribute iteration affects what type the column ends up being.
                    #       Which is bad because it means columns won't always be created with the proper types.
                    model_map[attribute.source_table][sc] = self.column_with_type(
                        base_type
                    )

                    # TODO: Might want to move the following lines to where we handle differing database types (e.g. postgres vs sqlite)
                    # if base_type == "date:year":
                    #     # Cast the date:year to a Date
                    #     model_map[attribute.source_table][sc] = self.column_with_type("date")       # THIS IS WRONG, BUT STOPS IT FROM CRASHING
                    #     # model_map[attribute.source_table][sc] = sql_func.date_cast(model_map[attribute.source_table][sc], self.ring.data_source.type)

            # Add derived columns for date times
            if (
                base_type == "date" or base_type == "datetime"
            ):  # or base_type == "date:year":      # TODO: This should likely be updated to handling types like date:year
                model_map = self.add_derived_datetime_columns_to_model_map(
                    model_map, attribute
                )

        return model_map

    def populate_relationships(self, relationship_list: List[List[str]]) -> None:
        """
        Populates the SQL Alchemy entities with relationship columns based on the ring configuration.
        :param relationship_list: List of list of the columns which specify the relationships.
        :type relationship_list: list[list[str]]
        :return: None
        :rtype: None
        """

        for rel_name, from_, to_ in relationship_list:
            # Get the table, column, and entity names
            from_table, from_col = from_.split(".")
            to_table, to_col = to_.split(".")
            
            # handle self-joins
            remote_side_forward = None
            remote_side_backward = None
            if from_table == to_table:
                rel_obj = [r for r in self.ring.relationships if r.join == [rel_name]]
                model = getattr(self.db, from_table)
                if rel_obj:
                    rel_type = rel_obj[0].type

                    remote_side_forward = None if not rel_obj or rel_type != "m2o" else [model.__dict__[to_col]]
                    remote_side_backward = None if not rel_obj or rel_type != "o2m" else [model.__dict__[from_col]]
                
            from_entity = getattr(self.db, from_table)
            to_entity = getattr(self.db, to_table)
            # temp_insp = sa.inspect(self.db.cases)
            # temp_insp.relationships.items()
            # back_ref_name = from_table+'_'+from_col # the back refrence relationship will be created by this name, table name and col names are used to keep the name unique
            back_ref_name = "reverse_" + rel_name

            # Setting relationship: from_table->to_table
            relation = relationship(
                to_table,
                back_populates=back_ref_name,
                primaryjoin=f"{from_}=={to_}",
                uselist=True,
                viewonly=True,
                remote_side=remote_side_forward,
            )
            setattr(from_entity, rel_name, relation)
            # setting relationship: to_table -> from_table
            relation = relationship(
                from_table,
                back_populates=rel_name,
                primaryjoin=f"{to_}=={from_}",
                uselist=True,
                viewonly=True,
                remote_side=remote_side_backward,
            )
            setattr(to_entity, back_ref_name, relation)

        return None

    def add_derived_datetime_columns_to_model_map(
        self, model_map: dict, attribute: RingAttribute
    ) -> dict:
        """
        Makes new columns (SQL Alchemy column property objs) by extracting the date at the level of granularity specified by the ring.
        :param model_map: The mapping used to create the SQL Alchemy ORM.
        :type model_map: dict
        :param attribute: The Satyrn attribute which is a datetime.
        :type attribute: RingAttribute
        :return: The updated model map
        :rtype: dict
        """
        """ 
        PENDING: when defining these, it might be good to have info from the entity attribute
        about the granularity we wanna go to, as well as defaults for granularity
        PENDING: what happens if value is Null? Everything returns null? RN seems to automatically cast it to now()
        Might need to put a path there to also return null if underlying value is also null
        PENDING: add a leading 0 if needed for month
        # NOTE: currently we are assuming only one source_column
        # For the fields smaller than "field", concatenate and add new column property
        # Edge cases to remove/rename:
        # - datetime: year month day hour minute second
        # - date: year month day
        # - time: hour minute second
        """
        col_name = attribute.source_columns[0]
        col = model_map[attribute.source_table][col_name]
        table = attribute.source_table

        # todo: need to check if these are the correct names for extracting from SQLAlchemy
        ordered_fields = [
            "year",
            "month",
            "day",
            "hour",
            "minute",
            "second",
            "microsecond",
        ]
        min_field = attribute.date_min_granularity
        max_field = attribute.date_max_granularity
        min_id = ordered_fields.index(min_field)
        max_id = ordered_fields.index(max_field)

        relevant_fields = ordered_fields[max_id : min_id + 1]

        datetime_component_col_dict = {}

        # Create the SQL Alchemy derived columns (column properties) for individual granularities (one per desired granularity)
        for field in relevant_fields:
            # Specify the granularity level
            gran_name = ":only" + field if field != "year" else ":" + field

            # Extract the component from the datetime column
            datetime_component_col = extract(field, col)

            if field != "year" and field != "microsecond":
                datetime_component_col = sql_func.sql_right(
                    "00" + cast(datetime_component_col, String),
                    self.ring.data_source.type,
                    2,
                )
            else:
                datetime_component_col = cast(datetime_component_col, String)

            # Create the SQL Alchemy derived column
            model_map[table][col_name + gran_name] = column_property(
                datetime_component_col
            )
            datetime_component_col_dict[field] = datetime_component_col

        # Add more column properties for the datetime
        if min_id > 1 and max_id == 0:
            # add column property for year/month/day
            model_map[table][col_name + ":day"] = column_property(
                datetime_component_col_dict["year"]
                + "/"
                + datetime_component_col_dict["month"]
                + "/"
                + datetime_component_col_dict["day"]
            )
            # add column property for day of week
            model_map[table][col_name + ":dayofweek"] = column_property(
                cast(
                    extract("dow", model_map[attribute.source_table][col_name]), String
                )
            )

        # Add column property for year+month
        if min_id > 0 and max_id == 0:
            model_map[table][col_name + ":month"] = column_property(
                datetime_component_col_dict["year"]
                + "/"
                + datetime_component_col_dict["month"]
            )

        return model_map

    def add_joins_to_model_map_and_create_relationship_list(
        self, model_map: Dict
    ) -> Tuple[Dict, List]:
        """
        Adds join columns to_col_name the mapping from Satyrn entities to_col_name SQL Alchemy specs.
        :param model_map: A mapping from Satyrn entities to_col_name SQL Alchemy specs.
        :type model_map: dict
        :return: The model map enhanced with join specs, along with a list of relationships.
        :rtype: Tuple[Dict, List[List]]
        """
        # TODO: make this fully handle multi-hops and all one-to_col_name-many, many-to_col_name-many, etc conditions

        # Get a mapping of the tables to_col_name the corresponding primary key
        primary_key_dict = {
            table_dict["name"]: table_dict["primaryKey"]
            for table_dict in self.ring.data_source.tables
        }

        relationship_list = []
        fks_for_tables = {}
        for join in self.ring.data_source.joins:
            rel_name = join.name
            for col_pair_with_type in join.path:
                # Pull out the table join specifications
                try:
                    from_col_name, to_col_name, key_type = col_pair_with_type
                    from_table, foreign_key_in_from_table = from_col_name.split(".")
                    to_table, primary_key_in_to_table = to_col_name.split(".")
                    relationship_list.append([rel_name, from_col_name, to_col_name])
                except:
                    print(
                        f"ERROR: Failed to_col_name parse join path with invalid format: {col_pair_with_type}"
                    )

                # TODO: handle joins on multiple columns - need to add a sa.ForeignKeyConstraint on lists of columns to table objects
                if from_table in fks_for_tables:
                    if foreign_key_in_from_table in fks_for_tables[from_table]:
                        fks_for_tables[from_table][foreign_key_in_from_table][
                            "fks"
                        ].append(to_col_name)
                    else:
                        fks_for_tables[from_table][foreign_key_in_from_table] = {
                            "fks": [to_col_name],
                            "type": key_type,
                        }
                else:
                    fks_for_tables[from_table] = {
                        foreign_key_in_from_table: {
                            "fks": [to_col_name],
                            "type": key_type,
                        }
                    }

        for t in fks_for_tables:
            for c in fks_for_tables[t]:
                model_map[t][c] = self.column_with_type(
                    fks_for_tables[t][c]["type"],
                    primary_key=c in primary_key_dict[t].keys(),
                    foreign_key=fks_for_tables[t][c]["fks"],
                )

        return model_map, relationship_list

    def column_with_type(
        self,
        type_string: str,
        primary_key: bool = False,
        foreign_key: Union[str, List[str]] = None,
    ) -> Column:
        """
        Creates a SQLAlchemy Column object.
        :param type_string: The SQLAlchemy type for the Column.
        :type type_string: str
        :param primary_key: Denotes whether this column is the primary key.
        :type primary_key: bool
        :param foreign_key: String denoting the column that is the foreign key.
        :type foreign_key: str
        :return: Column with the specified types.
        :rtype: Column

        # TODO: Modify this method to be able to deal with different kinds of data types
        # grab the upper ontology (maybe in the init it exists and we have it as a class attr)
        # If type in it, use that for the underlying data type
        # If not, revert to the just doing normal column stuff
        """

        if type_string in self.upper_ontology:
            sa_type = getattr(sa, self.upper_ontology[type_string].capitalize())
        elif type_string == "datetime":
            sa_type = DateTime
        elif type_string == "date":
            sa_type = Date
        elif type_string == "document":
            sa_type = Text
        else:
            sa_type = getattr(sa, type_string.capitalize())

        if primary_key and foreign_key == None:
            return Column(sa_type, primary_key=True)

        if foreign_key != None:
            fks = (
                [ForeignKey(foreign_key)]
                if type(foreign_key) == str
                else [ForeignKey(fk) for fk in foreign_key]
            )
            if primary_key:
                return Column(sa_type, *fks, primary_key=True)
            else:
                if type_string == "datetime":
                    return Column(
                        DateTime,
                        *fks,
                        default=datetime.datetime.utcnow,
                    )
                elif type_string == "date":
                    return Column(Date, *fks, default=datetime.date.today)
                else:
                    return Column(sa_type, *fks)
        elif type_string == "datetime":
            return Column(DateTime, default=datetime.datetime.utcnow)
        elif type_string == "date":
            return Column(Date, default=datetime.date.today)
        else:
            return Column(sa_type)

    def resolve_base_type(self, type: str) -> str:
        """
        Returns the highest level type in the ontology for the given type.
        :param type: The type to find the base type for.
        :type type: str
        :return: The base type in the ontology.
        :rtype: str

        # TODO: Flesh out details of ontology

        """
        if type in self.upper_ontology:
            return self.resolve_base_type(self.upper_ontology[type]["isa"])
        return type


def compile_rings(
    rings_list: List[str], operation_ontology: OperationOntology, augment_rings=True
) -> Tuple[dict, dict]:
    """
    Wrapper function for compiling multiple rings using compile_ring and a RingCompiler.
    :param rings_list: A list of paths to ring files.
    :type rings_list: List of strings
    :return: The rings and extractors that were compiled/built.
    :rtype: Tuple
    """

    # for now, rings_list is a list of paths on filesystem
    # in the future, rings_list will be a list of ids in db OR list of json objects, TBD
    rings = {}
    extractors = {}
    for ring_path in rings_list:
        ring = compile_ring(
            ring_path, operation_ontology, in_type="path", augment_ring=augment_rings
        )
        if (
            ring.id not in rings
        ):  # TODO: Should probably check if the ring id from the config is already in rings before building the ring again (possibly for the second time)
            rings[ring.id] = {}
            extractors[ring.id] = {}
        rings[ring.id][ring.version] = ring
        # extractors[ring.id][ring.version] = RingInterface(ring)
    return rings, extractors


def compile_ring(
    ring_config: Union[str, dict],
    operation_ontology: OperationOntology,
    in_type: str = "json",
    augment_ring=True,
) -> Ring:
    """
    Builds the ring configuration object and the SQLAlchemy ORM.
    :param ring_config: A path to the json file containing the ring configuration.
    :type ring_config: Union[str,dict]
    :param in_type: {json|path} specifying how the ring is provided.
    :type in_type: str
    :return: The ring configuration object.
    :rtype: Ring
    """

    ring = Ring()
    if in_type == "path":  # ring is a path to a json file
        ring.parse_file_from_path(ring_config)
    else:  # ring should be the json of a ring
        ring.parse(ring_config)
    ring.compiler = RingCompiler(ring)
    ring.db = ring.compiler.build_orm()
    ring.db_interface = DatabaseInterface(ring.db)

    # Derive additional attributes for the rings based on the available entities/attributes/relationships and analytics
    if augment_ring:
        ring_augmentor = RingAugmentor(ring, operation_ontology)
        ring_augmentor.generate_access_plans()
        ring_augmentor.generate_derived_attributes()
    return ring


# NEW VERSION
def currency_converter(amt, inDen, outDen):
    # TODO: someday
    return amt


UPPER_ONTOLOGY = {
    "currency": {
        "isa": "float",
        "subtypes": ["denomination"],
        "conversions": {"denominations": currency_converter},
        # TODO: how to cover info about styling (templates?), types of denominations, etc
    }
}
