# -*- coding: utf-8 -*-
"""
Functions to measure metrics of a graph.
"""

import networkx as nx
import numpy as np
import shapely

from orderbike.utils import dist_vector, get_node_positions


# TODO: Ugly writing but work, need to know what to put in kwargs and what not to put in kwargs for template metric func
def get_coverage(
    G, edge, geom={}, actual_area=0, buff_size=200, order="subtractive", pregraph=None
):
    """Get coverage of the graph G. Works with growth.dynamic_growth function. See prefunc_coverage."""
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


def prefunc_coverage(G, order=None, buff_size=200):
    """Pre-compute the dictionary of buffered geometries of the edges and the actual area for the coverage growth optimization."""
    geom = {edge: G.edges[edge]["geometry"].buffer(buff_size) for edge in G.edges}
    return {
        "pregraph": G,
        "geom": geom,
        "actual_area": shapely.ops.unary_union(list(geom.values())).area,
    }


def get_directness(G, edge):
    """Get directness of the graph G. Works with growth.dynamic_growth. See prefunc_directness."""
    mat = get_directness_matrix(G)
    # Mean directness on all non-null value, a null value means in different components or same node
    return np.sum(mat) / np.count_nonzero(mat)


# TODO: Make prefunc directness computing initial euclidean matrix and based on order will remove or add rows so not computing all at every step


def get_directness_matrix(G, lonlat=False):
    """Get the symmetrical directness matrix of a graph G. If lonlat is True, node positions are in geographic CRS."""
    shortest_matrix = get_shortest_network_path_length_matrix(G)
    euclidean_matrix = get_euclidean_distance_matrix(G, lonlat=lonlat)
    return avoid_zerodiv_matrix(euclidean_matrix, shortest_matrix)


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


def avoid_zerodiv_matrix(num_mat, den_mat):
    """
    Divide one matrix by another while replacing numerator divided by 0 by 0.
    Example: [[1, 2],   divided by [[1, 0],    will give out [[1, 0],
              [3, 4]]               [6, 0]]                   [0.5, 0]]
    """
    return np.divide(num_mat, den_mat, out=np.zeros_like(num_mat), where=den_mat != 0)
