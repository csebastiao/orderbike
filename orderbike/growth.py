# -*- coding: utf-8 -*-
"""
Functions to make subtractive or additive growth of a graph.
"""

import networkx as nx
import numpy as np
import pyproj
import shapely

from orderbike import metrics, utils


def remove_node_matrix(G, node_removed, mat):
    """Update the matrix by removing the symmetrical row and column for a list of nodes from G."""
    mat = mat.copy()
    for n in node_removed:
        node_index = utils.create_node_index(G)
        mat = np.delete(mat, node_index[n], 0)  # delete row
        mat = np.delete(mat, node_index[n], 1)  # delete column
    return mat


def get_subtractive_invalid_edges(G, built=True):
    """
    Find all invalid edges that if removed would create a new, unacceptable component to the graph. A new component is unacceptable if it's not a subgraph of a component that is part of the built graph but not of the actual graph.

    Args:
        G (networkx.Graph): Graph on which we want to remove edges.
        built (bool, optional): If True, there is a built component to the graph to take into account. This is represented by an edge attribute on all edges, that is 1 if it's built, 0 if it's not built. Defaults to True.

    Returns:
        list: List of tuple, each tuple being an invalid edge to remove from G.
    """
    # Find all bridges and remove bridges that when remove leave an isolated node
    invalid_edges = [
        edge
        for edge in nx.bridges(G)
        if not any(nx.degree(G, node) == 1 for node in edge)
    ]
    # If there are elected nodes there are built edges that we can't remove
    if built:
        built_edges = [edge for edge in G.edges if G.edges[edge]["built"] == 1]
        invalid_edges += built_edges
        invalid_edges = set(invalid_edges)
        elected_nodes = elect_nodes(G.edge_subgraph(built_edges))
    # If built is False work stops before checking elected_nodes, if built is True elected_nodes is created so it works
    if built is False or nx.number_connected_components(G) == len(elected_nodes):
        return invalid_edges
    # New component can be created only if part of a new component with a built part
    else:
        updated_invalid_edges = invalid_edges.copy()
        for edge in invalid_edges:
            H = G.copy()
            H.remove_edge(*edge)
            # Accept edges (remove from invalid edges) that if removed from the graph create a new component with a built part
            if not any(
                not any(node in cc for node in elected_nodes)
                for cc in list(nx.connected_components(H))
            ):
                updated_invalid_edges.remove(edge)
        return updated_invalid_edges


def get_additive_invalid_edges(G_actual, G_final):
    """
    Find all invalid edges that if added would create a new, unacceptable component to the graph. A new component is unacceptable if it's not a subgraph of a component that is part of the final graph but not of the actual graph.

    Args:
        G_actual (networkx.Graph): Graph on which we want to add edges.
        G_final (networkx.Graph): Final graph, from where we find potential edges that can be added to the actual graph.

    Returns:
        list: List of tuple, each tuple being an invalid edge to add to G_actual from G_final.
    """
    invalid_edges = [
        edge
        for edge in G_final.edges
        if (not any(node in G_actual for node in edge)) or edge in G_actual.edges
    ]
    # If already the final number of cc or will connect in the future give list of adjacent edge only
    if nx.number_connected_components(G_actual) >= nx.number_connected_components(
        G_final
    ):
        return invalid_edges
    # Else a new component can be created, but need to be within a final component not already on the graph
    else:
        updated_invalid_edges = invalid_edges.copy()
        for edge in invalid_edges:
            new_edges = list(G_actual.edges)
            # Graph.edge_subgraph can only use list of tuple, not list of list
            new_edges.append(tuple(edge))
            H = G_final.edge_subgraph(new_edges)
            # Accept edges (remove from invalid edges) that if added to the graph create a new component that is a subgraph of a component of the final graph
            if not any(
                not any(node in cc for node in elect_nodes(H))
                for cc in list(nx.connected_components(G_final))
            ):
                updated_invalid_edges.remove(edge)
        return updated_invalid_edges


def elect_nodes(G):
    """Take one node from each components of G to represent them."""
    return [next(iter(cc)) for cc in list(nx.connected_components(G))]


def _is_disconnected(G, elected_nodes):
    "Test to make sure that the increasing number of components is not because of an isolated node"
    pass


def optimal_step(vals, steps):
    """Return the step giving the maximal value."""
    return max(zip(vals, steps))[1]


def subtractive_choice(
    G, edgelist, area, em, sm, geom, elected_nodes, metric, keep_connected=True
):
    metric_vals = []  # List of metric value after an edge have been removed
    tested_step = []  # List of corresponding edge removed
    for edge in edgelist:
        # TODO be smarter and remove from batch edges that will disconnect the graph ?
        H = G.copy()
        H.remove_edge(*edge)
        if keep_connected:
            if _is_disconnected(H, elected_nodes):
                continue
        if metric == "directness":
            new_sm = metrics.get_shortest_network_path_matrix(H)
            sdm = metrics.avoid_zerodiv_matrix(em, new_sm)
            metric_val = metrics.directness_from_matrix(sdm)
        elif metric == "relative_coverage":
            temp_g = geom.copy()
            temp_g.pop(edge)
            new_area = shapely.ops.unary_union(list(temp_g.values())).area
            metric_val = (area - new_area) / G.edges[edge]["length"]
        metric_vals.append(metric_val)
        tested_step.append(edge)
    return optimal_step(metric_val, tested_step)


# TODO use osmnx projection tool instead of this shit
def get_projected_geometries(G, local_proj, buff_size):
    project = pyproj.Transformer.from_proj(
        pyproj.Proj(init=pyproj.CRS("epsg:4326")),
        pyproj.Proj(init=pyproj.CRS(local_proj)),
    )
    geom = {
        edge: shapely.ops.transform(
            project.transform, G.edges[edge]["geometry"]
        ).buffer(buff_size)
        for edge in G.edges
    }
    return geom


def additive_choice(
    G,
    actual_edges,
    edgelist,
    metric,
    geom,
    area,
    project,
    buff_size,
    keep_connected=True,
):
    metric_vals = []  # List of metric value after an edge have been removed
    tested_step = []  # List of corresponding edge removed
    for edge in edgelist:
        temp_edges = actual_edges.copy()
        temp_edges.append(edge)
        # Make subgraph of the actual_edges + the edge that we try to add
        H = G.edge_subgraph(temp_edges).copy()
        if keep_connected is True:
            if (
                nx.number_connected_components(H)
                > nx.number_connected_components(G.edge_subgraph(actual_edges))
            ) and (len(sorted(nx.connected_components(H), key=len)[0]) > 1):
                continue
        # See directness_subtractive_step comment on this
        if metric == "directness":
            dm = metrics.get_directness_matrix(H)
            metric_val = metrics.directness_from_matrix(dm)
        elif metric == "relative_coverage":
            temp_g = geom.copy()
            temp_g[edge] = shapely.ops.transform(
                project.transform, G.edges[edge]["geometry"]
            ).buffer(buff_size)
            new_area = shapely.ops.unary_union(list(temp_g.values())).area
            metric_val = (new_area - area) / G.edges[edge]["length"]
        metric_vals.append(metric_val)
        tested_step.append(edge)
    return optimal_step(metric_val, tested_step)
