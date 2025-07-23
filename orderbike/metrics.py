# -*- coding: utf-8 -*-
"""
Functions to measure metrics of a graph.
"""

import random

import networkx as nx
import numpy as np
import shapely
import igraph as ig
import scipy
from haversine import haversine
import osmnx as ox

from .utils import get_node_positions, dist_vector, log, get_node_dict


def growth_random(G):
    """Return a list of all edges of G in a random order."""
    edgelist = list(G.edges)
    random.shuffle(edgelist)
    return edgelist


def growth_betweenness(G, weight="length"):
    """Return the list of all edges of G ranked in descending order of edge betweenness."""
    ebet = nx.edge_betweenness_centrality(G, weight=weight)
    return [
        [key, val]
        for key, val in sorted(ebet.items(), key=lambda x: x[1], reverse=True)
    ]


def growth_closeness(G, weight="length"):
    """Return the list of all edges of G ranked in descending order of edge closeness, as the mean of their closeness nodes."""
    nclo = nx.closeness_centrality(G, distance=weight)
    eclo = {e: (nclo[e[0]] + nclo[e[1]]) / 2 for e in G.edges}
    return [
        [key, val]
        for key, val in sorted(eclo.items(), key=lambda x: x[1], reverse=True)
    ]


# TODO Add if order is additive an update argument to stop looking when maximum buffer size is reached to optimize
def growth_coverage(
    G,
    edge,
    order,
    pregraph=None,
    geom={},
    actual_area=0,
    buff_size=200,
    min_buff=25,
    max_buff=400,
    threshold_min_change=0.1,
    threshold_max_change=0.9,
    keep_searching=True,
    max_area=0,
):
    """Get coverage of the graph G. Works with growth.dynamic_growth function. Use prefunc_growth_coverage and upfunc_growth_coverage for classic coverage, use prefunc_growth_adaptive_coverage and upfunc_growth_adaptive_coverage for adaptive coverage."""
    geom_new = geom.copy()
    # If subtractive, since new_area - actual_area <= 0 the max is one changing less the area
    if order == "subtractive":
        geom_new.pop(edge)
        new_area = shapely.ops.unary_union(list(geom_new.values())).area
        return (new_area - actual_area) / pregraph.edges[edge]["length"]
    # If additive, the max is one increasing the most the area
    elif order == "additive":
        if keep_searching:
            geom_new[edge] = G.edges[edge]["geometry"].buffer(buff_size)
            new_area = shapely.ops.unary_union(list(geom_new.values())).area
            return (new_area - actual_area) / G.edges[edge]["length"]
        else:
            return 0


def prefunc_growth_coverage(G_actual, G_final, order, buff_size=200):
    """Pre-compute the dictionary of buffered geometries of the edges and the actual area for the coverage growth optimization."""
    gdf = ox.graph_to_gdfs(G_actual, nodes=False, edges=True)
    geom = gdf.geometry.buffer(buff_size)
    gdf = ox.graph_to_gdfs(G_actual, nodes=False, edges=True)
    max_area = gdf.geometry.buffer(buff_size).union_all().area
    return {
        "pregraph": G_actual,
        "order": order,
        "geom": geom.to_dict(),
        "actual_area": geom.union_all().area,
        "max_area": max_area,
        "buff_size": buff_size,
        "keep_searching": True,
    }


def upfunc_growth_coverage(
    G,
    G_actual,
    step,
    order,
    buff_size=200,
    geom=None,
    actual_area=0,
    pregraph=None,
    keep_searching=True,
    max_area=0,
):
    if order == "subtractive":
        geom.pop(step)
    elif order == "additive":
        geom[step] = G.edges[step]["geometry"].buffer(buff_size)
        actual_area = shapely.ops.unary_union(list(geom.values())).area
        if actual_area == max_area:
            keep_searching = False
        else:
            keep_searching = True
    return {
        "pregraph": G_actual,
        "order": order,
        "geom": geom,
        "actual_area": actual_area,
        "buff_size": buff_size,
        "keep_searching": keep_searching,
        "max_area": max_area,
    }


def prefunc_growth_adaptive_coverage(
    G_actual,
    G_final,
    order,
    min_buff=25,
    max_buff=400,
    threshold_min_change=0.1,
    threshold_max_change=0.9,
):
    """Pre-compute the dictionary of buffered geometries of the edges and the actual area for the coverage growth optimization."""
    if order == "additive":
        buff_size = max_buff
    elif order == "subtractive":
        buff_size = min_buff
    log.info(f"Starting buffer size for {order} adapative coverage is {buff_size}.")
    gdf = ox.graph_to_gdfs(G_actual, nodes=False, edges=True)
    geom = gdf.geometry.buffer(buff_size)
    return {
        "pregraph": G_actual,
        "order": order,
        "geom": geom.to_dict(),
        "actual_area": geom.union_all().area,
        "buff_size": buff_size,
        "min_buff": min_buff,
        "max_buff": max_buff,
        "threshold_min_change": threshold_min_change,
        "threshold_max_change": threshold_max_change,
    }


def upfunc_growth_adaptive_coverage(
    G,
    G_actual,
    step,
    order,
    buff_size=200,
    max_buff=400,
    min_buff=25,
    threshold_min_change=0.1,
    threshold_max_change=0.9,
    geom=None,
    actual_area=0,
    pregraph=None,
):
    """Pre-compute the dictionary of buffered geometries of the edges and the actual area for the coverage growth optimization, and in additive (resp. subtractive) order reduce (resp. increase) the buffer size if too big (resp. small)."""
    step_geom = G.edges[step]["geometry"].buffer(buff_size)
    if order == "subtractive":
        geom.pop(step)
    elif order == "additive":
        geom[step] = step_geom
    new_area = shapely.ops.unary_union(list(geom.values())).area
    if order == "subtractive":
        if buff_size < max_buff:
            change = (actual_area - new_area) / (step_geom.area - np.pi * buff_size**2)
            if change > threshold_max_change:
                log.debug(
                    f"Change is {change}, higher than threshold {threshold_max_change}, increasing buffer size."
                )
                buff_size = buff_size * 2
                if buff_size >= max_buff:
                    buff_size = max_buff
                log.debug(f"New buffer size is {buff_size}.")
                geom = {
                    edge: G_actual.edges[edge]["geometry"].buffer(buff_size)
                    for edge in G_actual.edges
                }
                new_area = shapely.ops.unary_union(list(geom.values())).area
    elif order == "additive":
        if buff_size > min_buff:
            change = (new_area - actual_area) / (step_geom.area - np.pi * buff_size**2)
            if change < threshold_min_change:
                log.debug(
                    f"Change is {change}, lower than threshold {threshold_min_change}, reducing buffer size."
                )
                buff_size = buff_size / 2
                if buff_size <= min_buff:
                    buff_size = min_buff
                log.debug(f"New buffer size is {buff_size}.")
                geom = {
                    edge: G_actual.edges[edge]["geometry"].buffer(buff_size)
                    for edge in G_actual.edges
                }
                new_area = shapely.ops.unary_union(list(geom.values())).area
    return {
        "pregraph": G,
        "order": order,
        "geom": geom,
        "actual_area": new_area,
        "buff_size": buff_size,
        "max_buff": max_buff,
        "min_buff": min_buff,
        "threshold_min_change": threshold_min_change,
        "threshold_max_change": threshold_max_change,
    }


def growth_relative_directness(G, edge, sm_final=[], G_final=None, order=None):
    """Get relative directness of the graph G. Works with growth.dynamic_growth."""
    sm = get_shortest_network_path_length_matrix(G)
    ids_to_delete = [ids for ids, node in enumerate(G_final.nodes) if node not in G]
    sm_final_trimmed = np.delete(
        np.delete(sm_final, ids_to_delete, 0), ids_to_delete, 1
    )
    mat = _avoid_zerodiv_matrix(sm_final_trimmed, sm)
    # Mean directness on all non-null value, a null value means in different components or same node
    return np.sum(mat) / np.count_nonzero(mat)


def prefunc_growth_relative_directness(G, G_final, order):
    """Pre-compute the final shortesth network path length matrix of the graph."""
    sm_final = get_shortest_network_path_length_matrix(G_final)
    return {"sm_final": sm_final, "G_final": G_final, "order": order}


# def growth_directness(G, edge, em=[]):
#     sm = get_shortest_network_path_length_matrix(G)
#     mat = _avoid_zerodiv_matrix(em, sm)
#     # Mean directness on all non-null value, a null value means in different components or same node
#     return np.sum(mat) / np.count_nonzero(mat)
#
# def prefunc_growth_directness(G_actual, G, order):
#     pass
#     # return {"em":get_euclidean_distance_matrix(G_actual)}
#
# def upfunc_growth_directness(G, G_final, step, order):
#     pass


# TODO
def growth_perceived_directness(
    G, edge, em=[], spm=[], sm=[], G_final=None, order=None, factor=4, node_dict={}
):
    H = G_final.copy()
    if order == "subtractive":
        H.edges[edge]["perceived_length"] = factor * H.edges[edge]["length"]
        sm_temp = sm.copy()
        for id_or, arr in enumerate(spm):
            for id_dest, path in enumerate(arr):
                if edge in path:
                    sm_temp[id_or][id_dest] = nx.shortest_path_length(
                        H,
                        node_dict[id_or],
                        node_dict[id_dest],
                        weight="perceived_length",
                        method="dijkstra",
                    )
    elif order == "additive":
        H.edges[edge]["perceived_length"] = H.edges[edge]["length"]
        sm = get_shortest_network_path_length_matrix(G, weight="perceived_length")
    mat = _avoid_zerodiv_matrix(em, sm)
    return np.sum(mat) / np.count_nonzero(mat)


def prefunc_growth_overall_directness(G, G_final, order, factor=4):
    if order == "subtractive":
        edge_built = [e for e in G.edges]
        for edge in G_final.edges:
            G_final.edges[edge]["perceived_length"] = G_final.edges[edge]["length"]
            if edge not in edge_built:
                G_final.edges[edge]["perceived_length"] *= factor
        node_list = list(G.nodes)
        spm = []
        for ids, dic in sorted(
            dict(nx.all_pairs_dijkstra_path(G, weight="perceived_length")).items()
        ):
            spm.append([val for key, val in sorted(_fill_dict(dic, node_list).items())])
        sm = sm_from_spm(G_final, spm, weight="perceived_length")
    elif order == "additive":
        spm = []
        sm = []
    em = get_euclidean_distance_matrix(G_final)
    node_dict = get_node_dict(G)
    return {
        "G_final": G_final,
        "order": order,
        "factor": factor,
        "node_dict": node_dict,
        "em": em,
        "sm": sm,
        "spm": spm,
    }


def upfunc_growth_overall_directness(
    G, G_actual, step, order, factor=0, node_dict={}, em=[], sm=[], spm=[]
):
    if order == "subtractive":
        G.edges[step]["perceived_length"] = factor * G.edges[step]["length"]
        new_spm = spm.copy()
        for id_or, arr in enumerate(spm):
            for id_dest, path in enumerate(arr):
                if step in path:
                    new_shortest_path = nx.shortest_path(
                        G,
                        node_dict[id_or],
                        node_dict[id_dest],
                        weight="perceived_length",
                        method="dijkstra",
                    )
                    new_spm[id_or][id_dest] = new_shortest_path
                    sm[id_or][id_dest] = nx.path_weight(
                        G, new_shortest_path, weight="perceived_length"
                    )
    return {
        "G_final": G,
        "order": order,
        "factor": factor,
        "node_dict": node_dict,
        "em": em,
        "sm": sm,
        "spm": new_spm,
    }


def growth_directness(G, edge):
    """Get directness of the graph G, works with growth.dynamic_growth."""
    mat = get_directness_matrix(G)
    # Mean directness on all non-null value, a null value means in different components or same node
    return np.sum(mat) / np.count_nonzero(mat)


def directness(G):
    """Get directness of the graph G."""
    mat = get_directness_matrix(G)
    # Mean directness on all non-null value, a null value means in different components or same node
    return np.sum(mat) / np.count_nonzero(mat)


def global_efficiency(G, weight="length"):
    """Get the global efficiency of the graph G if the distance $l_{ij}$ is the network path length $d_G(i,j)$."""
    if len(G.edges) == 0:  # For local efficiency since ego graph can be isolated nodes
        return 0
    else:
        em = get_euclidean_distance_matrix(G, lonlat=False)
        em_vals = em[np.triu_indices(em.shape[0], k=1)]
        sm = get_shortest_network_path_length_matrix(G, weight=weight)
        sm_vals = sm[np.triu_indices(sm.shape[0], k=1)]
        return sum(1 / sm_vals) / sum(1 / em_vals)


def local_efficiency(G, weight="length", center=False):
    """Get the local efficiency of the graph G if the distance $l_{ij}$ is the network path length $d_G(i,j)$. Original definition of efficiency is for center=False."""
    return (1 / len(G.nodes)) * sum(
        [
            global_efficiency(
                nx.ego_graph(G, n, radius=1, center=center), weight=weight
            )
            for n in G.nodes
        ]
    )


def sm_from_spm(G, spm, weight="length"):
    """Get the shortest network path length for each shortest network path."""
    return [[nx.path_weight(G, path, weight=weight) for path in arr] for arr in spm]


def get_directness_matrix(G, lonlat=False, weight="length"):
    """Get the symmetrical directness matrix of a graph G. If lonlat is True, node positions are in geographic CRS."""
    return _avoid_zerodiv_matrix(
        get_euclidean_distance_matrix(G, lonlat=lonlat),
        get_shortest_network_path_length_matrix(G, weight=weight),
    )


def get_shortest_network_path_length_matrix(G, weight="length"):
    """
    Get the symmetric matrix of shortest network path length of a graph G, with weight being called "length". The shortest network path length between the node i and j are in [i, j] and [j, i]. All diagonal values are 0. Value for pairs of nodes from different components is 0.

    Args:
        G (networkx.Graph): Graph on which we want to find shortest network path length for all pairs of nodes.
        weight (str, optional): Weight used in Dijkstra algorithm. Defaults to length.

    Returns:
        numpy.array: Matrix of shortest network path length for all pairs of nodes of G. Matrix with a shape (N, N), with N being the number of nodes in G
    """
    return np.array(
        ig.Graph.from_networkx(G).distances(
            source=None, target=None, weights=weight, mode="all"
        )
    )


def get_shortest_network_path_length_matrix_deprecated(G, weight="length"):
    """
    Deprecated

    Get the symmetric matrix of shortest network path length of a graph G, with weight being called "length". The shortest network path length between the node i and j are in [i, j] and [j, i]. All diagonal values are 0. Value for pairs of nodes from different components is 0.

    Args:
        G (networkx.Graph): Graph on which we want to find shortest network path length for all pairs of nodes.
        weight (str, optional): Weight used in Dijkstra algorithm. Defaults to length.

    Returns:
        numpy.array: Matrix of shortest network path length for all pairs of nodes of G. Matrix with a shape (N, N), with N being the number of nodes in G
    """
    node_list = list(G.nodes)
    shortest_matrix = []
    # Sort the nodes in both loops
    for ids, dic in sorted(
        dict(nx.all_pairs_dijkstra_path_length(G, weight=weight)).items()
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
    points = get_node_positions(G)
    if lonlat:
        dist = scipy.spatial.distance.cdist(points, points, metric=haversine)
    else:
        dist = scipy.spatial.distance.cdist(points, points, metric="euclidean")
    return np.array(dist)


def get_euclidean_distance_matrix_deprecated(G, lonlat=False):
    """
    Deprecated

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
