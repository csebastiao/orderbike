# -*- coding: utf-8 -*-
"""
Functions to make subtractive or additive growth of a graph.
"""

import networkx as nx
import numpy as np
import pyproj
import shapely

from orderbike import metrics, utils


def update_em(G, node_removed, em):
    """Update the euclidean distance matrix by removing the nodes removed with the subtractive step."""
    for n in node_removed:
        node_index = utils.create_node_index(G)
        em = np.delete(em, node_index[n], 0)  # delete row
        em = np.delete(em, node_index[n], 1)  # delete column
    return em


def _is_disconnected(G, elected_nodes):
    "Test to make sure that the increasing number of components is not because of an isolated node"
    pass


# TODO see if it's really useful
def optimal_step(metric_vals, tested_step):
    """Find for a list of choices with an associated value the most optimal one."""
    max_m = max(
        metric_vals
    )  # Using max on zip will not work for very close/equal values
    choice = tested_step[max(range(len(max_m)), key=max_m.__getitem__)]
    return choice


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
