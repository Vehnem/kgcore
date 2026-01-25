"""
Conversion utilities between high-level KGGraph API and Core Graph Model (CGM).

This module provides functions to convert between the two graph representations:
- High-level API: KGEntity, KGRelation, KGGraph (user-facing)
- Core Graph Model: CoreNode, CoreEdge, CoreGraph (research/teaching IR)
"""

from __future__ import annotations
from typing import Dict, Any
from kgcore.model.base import KGEntity, KGRelation
from kgcore.api.cgm import CoreNode, CoreEdge, CoreGraph, CoreLiteral
from kgcore.common.types import Lit, lit_to_core_literal, core_literal_to_lit


def kg_entity_to_core_node(entity: KGEntity) -> CoreNode:
    """
    Convert a KGEntity (high-level API) to CoreNode (CGM).
    
    Args:
        entity: KGEntity from high-level API
    
    Returns:
        CoreNode for CGM
    """
    # Convert properties, handling Lit instances
    props: Dict[str, Any | CoreLiteral] = {}
    for key, value in entity.props.items():
        if isinstance(value, Lit):
            props[key] = lit_to_core_literal(value)
        else:
            props[key] = value
    
    return CoreNode(
        id=entity.id,
        labels=entity.labels.copy(),
        properties=props
    )


def core_node_to_kg_entity(node: CoreNode) -> KGEntity:
    """
    Convert a CoreNode (CGM) to KGEntity (high-level API).
    
    Args:
        node: CoreNode from CGM
    
    Returns:
        KGEntity for high-level API
    
    Note:
        CoreLiteral instances are converted to Lit (language tag is lost)
    """
    from kgcore.common.types import Props
    
    # Convert properties, handling CoreLiteral instances
    props: Props = {}
    for key, value in node.properties.items():
        if isinstance(value, CoreLiteral):
            props[key] = core_literal_to_lit(value)
        else:
            props[key] = value
    
    return KGEntity(
        id=str(node.id),  # Ensure it's a string
        labels=node.labels.copy(),
        props=props
    )


def kg_relation_to_core_edge(relation: KGRelation) -> CoreEdge:
    """
    Convert a KGRelation (high-level API) to CoreEdge (CGM).
    
    Args:
        relation: KGRelation from high-level API
    
    Returns:
        CoreEdge for CGM
    
    Note:
        KGRelation uses `type`, CoreEdge uses `label`
    """
    # Convert properties, handling Lit instances
    props: Dict[str, Any | CoreLiteral] = {}
    for key, value in relation.props.items():
        if isinstance(value, Lit):
            props[key] = lit_to_core_literal(value)
        else:
            props[key] = value
    
    return CoreEdge(
        id=relation.id,
        source=relation.source,
        target=relation.target,
        label=relation.type,  # type -> label
        properties=props
    )


def core_edge_to_kg_relation(edge: CoreEdge) -> KGRelation:
    """
    Convert a CoreEdge (CGM) to KGRelation (high-level API).
    
    Args:
        edge: CoreEdge from CGM
    
    Returns:
        KGRelation for high-level API
    
    Note:
        CoreEdge uses `label`, KGRelation uses `type`
    """
    from kgcore.common.types import Props
    
    # Convert properties, handling CoreLiteral instances
    props: Props = {}
    for key, value in edge.properties.items():
        if isinstance(value, CoreLiteral):
            props[key] = core_literal_to_lit(value)
        else:
            props[key] = value
    
    return KGRelation(
        id=str(edge.id),  # Ensure it's a string
        type=edge.label,  # label -> type
        source=str(edge.source),
        target=str(edge.target),
        props=props
    )


def kg_graph_to_core_graph(kg_graph: "KGGraph") -> CoreGraph:
    """
    Convert a KGGraph (high-level API) to CoreGraph (CGM).
    
    Args:
        kg_graph: KGGraph instance (must implement find_entities/find_relations)
    
    Returns:
        CoreGraph instance
    
    Note:
        This requires the KGGraph to support find_entities and find_relations.
        Not all backends may support this efficiently.
    """
    core = CoreGraph()
    
    # Convert all entities
    entities = kg_graph.find_entities()
    for entity in entities:
        core.add_node(kg_entity_to_core_node(entity))
    
    # Convert all relations
    relations = kg_graph.find_relations()
    for relation in relations:
        core.add_edge(kg_relation_to_core_edge(relation))
    
    return core


def core_graph_to_kg_graph(core: CoreGraph, kg_graph: "KGGraph") -> None:
    """
    Populate a KGGraph from a CoreGraph.
    
    Args:
        core: CoreGraph to convert from
        kg_graph: KGGraph to populate (must support create_entity/create_relation)
    
    Note:
        This modifies the kg_graph in place.
    """
    # Convert all nodes to entities
    for node in core.nodes.values():
        entity = core_node_to_kg_entity(node)
        kg_graph.create_entity(entity.labels, entity.props, id=entity.id)
    
    # Convert all edges to relations
    for edge in core.edges.values():
        relation = core_edge_to_kg_relation(edge)
        kg_graph.create_relation(relation.type, relation.source, relation.target, relation.props)

