# -*- coding: utf-8 -*-
"""
Functions to measure metrics of a graph.
"""

import random

import networkx as nx
import numpy as np
import shapely

from .utils import dist_vector, get_node_positions


def growth_random(G):
    """Return a list of all edges of G in a random order."""
    edgelist = list(G.edges)
    random.shuffle(edgelist)
    return edgelist


def growth_betweenness(G, weight="length"):
    """Return the list of all edges of G ranked in descending order of edge betweenness."""
    ebet = nx.edge_betweenness_centrality(G, weight=weight)
    return [key for key, val in sorted(ebet.items(), key=lambda x: x[1], reverse=True)]


def growth_coverage(
    G, edge, pregraph=None, order="subtractive", geom={}, actual_area=0, buff_size=200
):
    """Get coverage of the graph G. Works with growth.dynamic_growth function. See prefunc_growth_coverage."""
    geom_new = geom.copy()
    if order == "subtractive":
        geom_new.pop(edge)
    if order == "additive":
        geom_new[edge] = G.edges[edge]["geometry"].buffer(buff_size)
    new_area = shapely.ops.unary_union(list(geom_new.values())).area
    if order == "subtractive":
        return (actual_area - new_area) / pregraph.edges[edge]["length"]
    elif order == "additive":
        return (new_area - actual_area) / G.edges[edge]["length"]
    else:
        raise ValueError(
            f"Incorrect value {order} for order, please choose subtractive or additive."
        )


def prefunc_growth_coverage(G, order="subtractive", buff_size=200):
    """Pre-compute the dictionary of buffered geometries of the edges and the actual area for the coverage growth optimization."""
    geom = {edge: G.edges[edge]["geometry"].buffer(buff_size) for edge in G.edges}
    return {
        "pregraph": G,
        "order": order,
        "geom": geom,
        "actual_area": shapely.ops.unary_union(list(geom.values())).area,
        "buff_size": buff_size,
    }


# TODO: Add minimal buffer as plateau so replace buffer smaller than min_buff by min_buff ?
def prefunc_growth_adaptative_coverage(
    G,
    order="subtractive",
    buff_size=500,
    G_final=None,
    order_growth=[],
    threshold_change=0.01,
    min_buff=20,
):
    """Pre-compute the dictionary of buffered geometries of the edges and the actual area for the coverage growth optimization, and reduce the buffer size if too big."""
    if len(order_growth) > 1:
        if order == "subtractive":
            edges_bef = list(G.edges)
            edges_bef.append(tuple([order_growth[-1]]))
            G_bef = G_final.edge_subgraph(edges_bef)
        elif order == "additive":
            G_bef = G.copy()
            G_bef.remove_edge(*order_growth[-1])
        geom = {edge: G.edges[edge]["geometry"].buffer(buff_size) for edge in G.edges}
        geom_bef = {
            edge: G_bef.edges[edge]["geometry"].buffer(buff_size)
            for edge in G_bef.edges
        }
        change = (
            shapely.ops.unary_union(list(geom.values())).area
            - shapely.ops.unary_union(list(geom_bef.values())).area
        ) / shapely.ops.unary_union(list(geom_bef.values())).area
        # Since there is no memory in the precomp function we need to always recompute the actual buffer size
        while change < threshold_change:
            buff_size = buff_size / 2
            geom = {
                edge: G.edges[edge]["geometry"].buffer(buff_size) for edge in G.edges
            }
            # To avoid infinite loop for very large graph where single edge cannot give more than threshold change anymore
            if buff_size <= min_buff:
                break
            geom_bef = {
                edge: G_bef.edges[edge]["geometry"].buffer(buff_size)
                for edge in G_bef.edges
            }
            change = (
                shapely.ops.unary_union(list(geom.values())).area
                - shapely.ops.unary_union(list(geom_bef.values())).area
            ) / shapely.ops.unary_union(list(geom_bef.values())).area
    else:
        geom = {edge: G.edges[edge]["geometry"].buffer(buff_size) for edge in G.edges}
    return {
        "pregraph": G,
        "order": order,
        "geom": geom,
        "actual_area": shapely.ops.unary_union(list(geom.values())).area,
        "buff_size": buff_size,
    }


def growth_relative_directness(G, edge, sm_final=[], G_final=None):
    """Get relative directness of the graph G. Works with growth.dynamic_growth."""
    sm = get_shortest_network_path_length_matrix(G)
    ids_to_delete = [ids for ids, node in enumerate(G_final.nodes) if node not in G]
    sm_final_trimmed = np.delete(
        np.delete(sm_final, ids_to_delete, 0), ids_to_delete, 1
    )
    mat = _avoid_zerodiv_matrix(sm_final_trimmed, sm)
    # Mean directness on all non-null value, a null value means in different components or same node
    return np.sum(mat) / np.count_nonzero(mat)


def prefunc_growth_relative_directness(G, order="subtractive", G_final=None):
    """Pre-compute the final shortesth network path length matrix of the graph."""
    sm_final = get_shortest_network_path_length_matrix(G_final)
    return {"sm_final": sm_final, "G_final": G_final}


def directness(G, edge):
    """Get directness of the graph G. Works with growth.dynamic_growth."""
    mat = get_directness_matrix(G)
    # Mean directness on all non-null value, a null value means in different components or same node
    return np.sum(mat) / np.count_nonzero(mat)


def get_directness_matrix(G, lonlat=False):
    """Get the symmetrical directness matrix of a graph G. If lonlat is True, node positions are in geographic CRS."""
    shortest_matrix = get_shortest_network_path_length_matrix(G)
    euclidean_matrix = get_euclidean_distance_matrix(G, lonlat=lonlat)
    return _avoid_zerodiv_matrix(euclidean_matrix, shortest_matrix)


def get_shortest_network_path_length_matrix(G):
    """
    Get the symmetric matrix of shortest network path length of a graph G, with weight being called "length". The shortest network path length between the node i and j are in [i, j] and [j, i]. All diagonal values are 0. Value for pairs of nodes from different components is 0.

    Args:
        G (networkx.Graph): Graph on which we want to find shortest network path length for all pairs of nodes.

    Returns:
        numpy.array: Matrix of shortest network path length for all pairs of nodes of G. Matrix with a shape (N, N), with N being the number of nodes in G
    """
    node_list = list(G.nodes)
    shortest_matrix = []
    # Sort the nodes in both loops
    for ids, dic in sorted(
        dict(nx.all_pairs_dijkstra_path_length(G, weight="length")).items()
    ):
        # Add 0 values for nodes not in the same components to get symmetrical matrix
        shortest_matrix.append(
            [val for key, val in sorted(_fill_dict(dic, node_list).items())]
        )
    return np.array(shortest_matrix)


def _fill_dict(dictionary, n_list):
    """Fill dictionary with 0 for node without a value."""
    for n in n_list:
        if n not in dictionary:
            dictionary[n] = 0.0
    return dictionary


def get_euclidean_distance_matrix(G, lonlat=False):
    """
    Get the symmetric matrix of euclidean distance for nodes on a spatial graph G. The euclidean distance between the node i and j are in [i, j] and [j, i]. All diagonal values are 0.

    Args:
        G (networkx.Graph): Graph on which we want to find the euclidean distance for all pairs of nodes.
        lonlat (bool, optional): If True, node positions are in longitude and latitude, else they are values in meters in a projection. Defaults to False.

    Returns:
        numpy.array: Matrix of euclidean distance for all pairs of nodes of G. Matrix with a shape (N, N), with N being the number of nodes in G
    """
    pos_list = get_node_positions(G)
    # If in longitude and latitude, use haversine distance
    if lonlat:
        euclidean_matrix = [
            dist_vector([pos] * len(pos_list), pos_list) for pos in pos_list
        ]
    # Else use the vector norm of the difference
    else:
        euclidean_matrix = [
            [np.linalg.norm(pos - other_pos) for other_pos in pos_list]
            for pos in pos_list
        ]
    return np.array(euclidean_matrix)


def _avoid_zerodiv_matrix(num_mat, den_mat):
    """
    Divide one matrix by another while replacing numerator divided by 0 by 0.
    Example: [[1, 2],   divided by [[1, 0],    will give out [[1, 0],
              [3, 4]]               [6, 0]]                   [0.5, 0]]
    """
    return np.divide(num_mat, den_mat, out=np.zeros_like(num_mat), where=den_mat != 0)
