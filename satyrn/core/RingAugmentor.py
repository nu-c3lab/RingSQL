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

from typing import List

from satyrn.core.RingObjects.Ring import Ring
from satyrn.core.Operations.ArgType import ArgType
from satyrn.core.Operations.Operation import Operation
from satyrn.core.RingObjects.RingEntity import RingEntity
from satyrn.core.RingObjects.RingAttribute import RingAttribute
from satyrn.core.Analysis.OperationOntology import OperationOntology
from satyrn.core.Analysis.AnalysisEngine import AnalysisEngine
from satyrn.core.Planning.StepExpressor import StepExpressor


class RingAugmentor:
    def __init__(self, ring: Ring, operation_ontology: OperationOntology):
        self.ring = ring
        self.operation_ontology = operation_ontology
        self.analysis_engine = AnalysisEngine()
        self.step_expressor = StepExpressor(self.ring, self.operation_ontology)

    def generate_derived_attributes(self) -> None:
        """
        Note: Updates the Ring in-place.
        :return:
        :rtype:
        """

        # TODO: Generate attributes for operations like duration

        # Generate derived attributes for each of the entities
        for ent in self.ring.entities:
            self.generate_metric_aggregations_over_related_entities(ent)
            self.generate_counts_over_related_entities(ent)
            self.generate_durations_for_entity(ent)

        return None

    def generate_access_plans(self) -> None:
        """
        Note: Updates the Ring in-place.
        :return:
        :rtype:
        """

        for entity in self.ring.entities:
            for attr_name, attr in entity.attributes.items():
                # Get the identifier for this entity
                identifier_attributes = [
                    attr
                    for attr_name, attr in entity.attributes.items()
                    if ArgType.Identifier in attr.type
                ]
                composite_identifier_attributes = [
                    attr
                    for attr_name, attr in entity.attributes.items()
                    if ArgType.CompositeIdentifier in attr.type
                ]
                # identifier_attribute_name = 'id' if len(identifier_attributes) < 1 else identifier_attributes[0].name
                # only assume "id" as identifier if no Identifier or CompositeIdentifiers are definec
                identifier_attribute_name = (
                    ("if" if len(composite_identifier_attributes) < 1 else None)
                    if len(identifier_attributes) < 1
                    else identifier_attributes[0].name
                )

                # assume either a sinlge Identifier or multiple CompositeIdentifiers
                if identifier_attribute_name:
                    if attr_name == identifier_attribute_name:
                        attr.access_plan = {
                            "|1|": f"(retrieve_entity {entity.name})",
                            "|2|": f"(retrieve_attribute |1| {attr.name})",
                            "|3|": "(collect |2|)",
                            "|4|": "(return |3|)",
                        }
                    else:
                        attr.access_plan = {
                            "|1|": f"(retrieve_entity {entity.name})",
                            "|2|": f"(retrieve_attribute |1| {attr.name})",
                            "|3|": f"(retrieve_attribute |1| {identifier_attribute_name})",
                            "|4|": "(collect |2| |3|)",
                            "|5|": "(return |4|)",
                        }
                else:
                    # retrieve all composite identifiers along with attribute
                    composite_identifier_attribute_names = [
                        attr.name for attr in composite_identifier_attributes
                    ]
                    if attr_name in composite_identifier_attribute_names:
                        retrieve_id_steps = {
                            f"|{i + 2}|": f"(retrieve_attribute |1| {id_attr})"
                            for i, id_attr in enumerate(
                                composite_identifier_attribute_names
                            )
                        }
                        attr.access_plan = {
                            "|1|": f"(retrieve_entity {entity.name})",
                        }
                        for step in retrieve_id_steps.keys():
                            attr.access_plan[step] = retrieve_id_steps[step]

                        attr.access_plan[f"|{len(retrieve_id_steps) + 2}|"] = (
                            f"(collect {' '.join(list(retrieve_id_steps.keys()))})"
                        )
                        attr.access_plan[f"|{len(retrieve_id_steps) + 3}|"] = (
                            f"(return |{len(retrieve_id_steps) + 2}|)"
                        )
                    else:
                        retrieve_id_steps = {
                            f"|{i + 3}|": f"(retrieve_attribute |1| {id_attr})"
                            for i, id_attr in enumerate(
                                composite_identifier_attribute_names
                            )
                        }

                        attr.access_plan = {
                            "|1|": f"(retrieve_entity {entity.name})",
                            "|2|": f"(retrieve_attribute |1| {attr.name})",
                        }

                        for step in retrieve_id_steps.keys():
                            attr.access_plan[step] = retrieve_id_steps[step]

                        attr.access_plan[f"|{len(retrieve_id_steps) + 3}|"] = (
                            f"(collect |2| {' '.join(list(retrieve_id_steps.keys()))})"
                        )
                        attr.access_plan[f"|{len(retrieve_id_steps) + 4}|"] = (
                            f"(return |{len(retrieve_id_steps) + 3}|)"
                        )
                attr.access_plan_without_id = {
                            "|1|": f"(retrieve_entity {entity.name})",
                            "|2|": f"(retrieve_attribute |1| {attr.name})",
                            "|3|": "(collect |2|)",
                            "|4|": "(return |3|)",
                        }

        return None

    def generate_durations_for_entity(self, target_entity: RingEntity) -> None:
        # TODO: Implement this
        return None

    def get_count_operations(self) -> List[Operation]:
        operations_to_get = {"count_unique"}
        return [
            self.operation_ontology.analysis_operations[op]
            for op in operations_to_get
            if op in self.operation_ontology.analysis_operations
        ]

    def generate_counts_over_related_entities(self, target_entity: RingEntity) -> None:
        count_operations = self.get_count_operations()

        # Get the o2m relationships from this entity to the other entities
        related_entity_names = []
        for relationship in self.ring.relationships:
            if relationship.fro == target_entity.name and relationship.type in [
                "o2m",
                "m2m",
            ]:
                related_entity_names.append(relationship.to)
            elif relationship.to == target_entity.name and relationship.type in [
                "m2o",
                "m2m",
            ]:
                related_entity_names.append((relationship.fro))

        # Get the RingEntity objects for each of the related entities
        related_entities = [
            ent for ent in self.ring.entities if ent.name in related_entity_names
        ]

        for related_ent in related_entities:
            # Get the set of attributes that can be counted on the related entity (arithmetic attributes of the related entity)
            countable_attributes = [
                attr
                for attr_name, attr in related_ent.attributes.items()
                if ArgType.Identifier in attr.type and not attr.is_derived()
            ]

            # Get the set of attributes that can be grouped by on the target entity (the identifier of the target entity)
            groupby_attributes = [
                attr
                for attr_name, attr in target_entity.attributes.items()
                if ArgType.Identifier in attr.type and not attr.is_derived()
            ]

            # For each combination, create a new RingAttribute
            for countable_attr in countable_attributes:
                for groupby_attr in groupby_attributes:
                    for count_op in count_operations:
                        # Create the derived attribute
                        new_attribute = self.create_aggregation_attribute(
                            countable_attr,
                            groupby_attr,
                            count_op,
                            target_entity,
                            related_ent,
                        )

                        # Add this derived attribute to the appropriate ring entity
                        target_entity.attributes[new_attribute.name] = new_attribute
                        target_entity.attribute_name.append(new_attribute.name)

        return None

    def get_metric_aggregation_operations(self) -> List[Operation]:
        operations_to_get = {"average", "max", "min", "median", "sum", "std_dev"}
        return [
            self.operation_ontology.analysis_operations[op]
            for op in operations_to_get
            if op in self.operation_ontology.analysis_operations
        ]

    def generate_metric_aggregations_over_related_entities(
        self, target_entity: RingEntity
    ) -> None:
        metric_aggregation_operations = self.get_metric_aggregation_operations()

        # Get the o2m relationships from this entity to the other entities
        related_entity_names = []
        for relationship in self.ring.relationships:
            if relationship.fro == target_entity.name and relationship.type in [
                "o2m",
                "m2m",
            ]:
                related_entity_names.append(relationship.to)
            elif relationship.to == target_entity.name and relationship.type in [
                "m2o",
                "m2m",
            ]:
                related_entity_names.append((relationship.fro))

        # Get the RingEntity objects for each of the related entities
        related_entities = [
            ent for ent in self.ring.entities if ent.name in related_entity_names
        ]

        for related_ent in related_entities:
            # Get the set of attributes that can be aggregated on the related entity (arithmetic attributes of the related entity)
            aggregation_attributes = [
                attr
                for attr_name, attr in related_ent.attributes.items()
                if ArgType.Arithmetic in attr.type and not attr.is_derived()
            ]

            # Get the set of attributes that can be grouped by on the target entity (the identifier of the target entity)
            groupby_attributes = [
                attr
                for attr_name, attr in target_entity.attributes.items()
                if ArgType.Identifier in attr.type and not attr.is_derived()
            ]

            # For each combination, create a new RingAttribute
            for agg_attr in aggregation_attributes:
                for groupby_attr in groupby_attributes:
                    for agg_op in metric_aggregation_operations:
                        # Create the derived attribute
                        new_attribute = self.create_aggregation_attribute(
                            agg_attr, groupby_attr, agg_op, target_entity, related_ent
                        )

                        # Add this derived attribute to the appropriate ring entity
                        target_entity.attributes[new_attribute.name] = new_attribute
                        target_entity.attribute_name.append(new_attribute.name)

        return None

    def create_aggregation_attribute(
        self,
        agg_attr: RingAttribute,
        groupby_attr: RingAttribute,
        agg_op: Operation,
        target_ent: RingEntity,
        related_ent: RingEntity,
    ) -> RingAttribute:
        """
        Creates a RingAttribute object which represents a derived attribute found by
        using the specified operations, entities, and attributes.
        :param agg_op: The operation to perform on the agg_attr.
        :type agg_op: Operation
        :param agg_attr: The attribute to be aggregated.
        :type agg_attr: RingAttribute
        :param groupby_attr: The attribute to be grouped by.
        :type groupby_attr: RingAttribute
        :param target_ent: The ring entity which has the grouby_attr.
        :type target_ent: RingEntity
        :param related_ent: The ring entity which has the agg_attr.
        :type related_ent: RingEntity
        :return: The fully specified RingAttribute.
        :rtype: RingAttribute
        """
        new_attribute = RingAttribute(parent_entity=target_ent)

        # Generate the access subplans for each combination
        new_attribute.access_plan = {
            "|1|": f"(retrieve_entity {target_ent.name})",
            "|2|": f"(retrieve_entity {related_ent.name})",
            "|3|": f"(retrieve_attribute |1| {groupby_attr.name})",
            "|4|": f"(retrieve_attribute |2| {agg_attr.name})",
            "|5|": "(groupby |3|)",
            "|6|": f"({agg_op.name} |4| |5|)",
            "|7|": "(collect |3| |6|)",
            "|8|": "(return |7|)",
        }

        new_attribute.name = f"{agg_op.name}_{related_ent.name}_{agg_attr.name}"
        # new_attribute.nicename = [f"{agg_op.name} {agg_attr.nicename[0]}", f"{agg_op.name} {agg_attr.nicename[0]}"]

        # Inherit the isas TODO: This is not correct and should be updated. The type of the attribute may change based on the aggregation being applied
        new_attribute.baseisa = agg_attr.base_isa
        new_attribute.isa = agg_attr.isa

        # Assign the types
        new_attribute.type = agg_op.output_args[0].arg_types
        if (
            ArgType.Datetime not in agg_attr.type
            and ArgType.Datetime in new_attribute.type
        ):
            new_attribute.type.remove(ArgType.Datetime)

        # Set the properties relating to derived attributes
        new_attribute.is_aggregated = True
        new_attribute.aggregated_entity = related_ent

        # Get units for the derived attribute
        analysis_plan = self.analysis_engine.plan_parser.parse(
            new_attribute.access_plan
        )
        new_query_args = (
            self.analysis_engine.query_builder_sqr.build_query_arguments_from_sqr_plan(
                analysis_plan, self.operation_ontology
            )
        )
        units = self.analysis_engine.get_units(new_query_args, self.ring)
        new_attribute.units = units[-1]

        expressed_step = self.step_expressor.express_step(
            "|" + str(6) + "|", analysis_plan, skip_groupbys=True
        )
        new_attribute.nicename = [expressed_step, expressed_step]

        return new_attribute
