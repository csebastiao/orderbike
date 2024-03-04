# -*- coding: utf-8 -*-
"""
New functions and original and modified functions from OSMnx in order to
simplify the graph by removing interstitial nodes and by going from a
multidigraph to a graph.
"""

import numpy as np
from haversine import haversine, haversine_vector
from networkx import Graph, get_node_attributes
from osmnx import get_undirected
from shapely.geometry import LineString
from sklearn.metrics import auc


def dist(v1, v2):
    """
    From https://github.com/mszell/bikenwgrowth
    Return the haversine distance in meters between the points v1 and v2,
    where v1 and v2 are dictionary written like
    v = {'x': longitude, 'y': latitude}.
    """
    return haversine((v1["y"], v1["x"]), (v2["y"], v2["x"]), unit="m")


def dist_vector(v1_list, v2_list):
    """
    From https://github.com/mszell/bikenwgrowth
    Return a list of haversine distance in meters between two list
    of points written like
    v_list = [[latitude, longitude], [latitude, longitude], ...]. The
    function will compare the points of each list, so if we have
    v1_list = [A, B], v2_list = [C, D], we will have as a result
    the haversine distance between A and C and between B and D.
    """
    return haversine_vector(v1_list, v2_list, unit="m")


def create_node_index(G, revert=False):
    """
    Make a dictionary translating node's ID of ascending order into
    integers starting from 0 and incremeting by 1. By default node's
    ID are the key, but we can revert it as the value.

    Parameters
    ----------
    G : networkx.classes.graph.Graph
        Graph for which we create the index.
    revert : bool, optional
        If False, node's ID are the keys, the count are the values.
        If True, node's ID are the values, the count are the keys.
        The default is False.

    Returns
    -------
    index_table : dict
        Dictionary translating node's ID into integers starting from 0.

    """
    index_table = dict()
    count = 0
    if revert is False:
        for node in sorted(G.nodes):
            index_table[node] = count
            count += 1
    else:
        for node in sorted(G.nodes):
            index_table[count] = node
            count += 1
    return index_table


def create_edge_index(G, revert=False):
    """
    Make a dictionary translating edge's ID of ascending order into
    integers starting from 0 and incremeting by 1. By default edge's
    ID are the key, but we can revert it as the value.

    Parameters
    ----------
    G : networkx.classes.graph.Graph
        Graph for which we create the index.
    revert : bool, optional
        If False, node's ID are the keys, the count are the values.
        If True, node's ID are the values, the count are the keys.
        The default is False.

    Returns
    -------
    index_table : dict
        Dictionary translating edge's ID into integers starting from 0.

    """
    index_table = dict()
    count = 0
    if revert is False:
        for edge in sorted(G.edges):
            index_table[edge] = count
            count += 1
    else:
        for edge in sorted(G.edges):
            index_table[count] = edge
            count += 1
    return index_table


def clean_isolated_node(G):
    """Remove every node that has no link to any other node"""
    H = G.copy()
    for node in G.nodes:
        if H.degree(node) == 0:
            H.remove_node(node)
    return H


def get_area_under_curve(curve, xx=None, normalize_y=False, normalize_x=False):
    """Get area under the curve to compare the efficiency of a curve"""
    if xx is None:
        xx = range(len(curve))
    if normalize_y is True:
        curve = (curve - np.min(curve)) / (np.max(curve) - np.min(curve))
    if normalize_x is True:
        return (auc(xx, curve) - np.min(xx)) / (np.max(xx) - np.min(xx))
    return auc(xx, curve)


# TODO make find all edges attributes values except for list of keys, to avoid like speed limit width name osmid those kind of useless ones


def add_edge_attr_from_dict(G, attr_dict, name):
    """
    Add an attribute from a dictionary.
    """
    G = G.copy()
    for edge in G.edges:
        if name in G.edges[edge]:
            err = f"{name} already in edge {edge}, use a new name"
            raise NameError(err)
        for key in list(attr_dict.keys()):
            if key in list(G.edges[edge].keys()):
                if G.edges[edge][key] in attr_dict[key]:
                    G.edges[edge][name] = 1
                    break
                G.edges[edge][name] = 0
    return G


def get_node_positions(G):
    """Find all node longitude and latitude from the graph G and put them into a numpy array."""
    lon = [val for key, val in sorted(get_node_attributes(G, "x").items())]
    lat = [val for key, val in sorted(get_node_attributes(G, "y").items())]
    return np.transpose(np.array([lat, lon]))


def multidigraph_to_graph(G):
    """
    Transform a MultiDiGraph into an undirected Graph by first removing the direction, making a MultiGraph, and then making it a Graph by making sure that there is no multiple edges : for self-loop we create two nodes within the geometry of the edge, for node with multiple edges we create one node within each geometry of the edge. We avoid to merge directed edges without the same arbitrary attributes.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        MultiDiGraph we want to transform.

    Returns
    -------
    G : networkx.Graph
        Undirected graph made from the initial MultiDiGraph.
    """
    G = G.copy()
    G = get_undirected(G)
    initial_node_list = list(G.nodes())  # to avoid issue with changes
    for node in initial_node_list:
        neighbors = np.transpose(list(G.edges(node)))[1]
        if node in neighbors:  # then self_loop, need 2 artifical nodes
            for k in list(G.get_edge_data(node, node).keys()):
                G = _solve_self_loop(G, node, k)
        for neigh in neighbors:
            if (
                G.number_of_edges(node, neigh) > 1
            ):  # t hen multiple path, need 1 artifical nodes per additional paths
                G = _solve_multiple_path(G, node, neigh)
    G = Graph(G)
    return G


def _solve_self_loop(G, node, key):
    """
    Transform a loop where a node is connected to itself by adding two nodes in the geometry of the loop.

    Parameters
    ----------
    G : networkx.MultiGraph
        MultiGraph we want to transform.
    node : int
        Node's ID where there is a self-loop.
    key : int
        Key of the edge, needed because the graph is a MultiGraph

    Returns
    -------
    G : networkx.MultiGraph
        MultiGraph with the self-loop resolved.

    """
    edge_attributes = dict(G.edges[node, node, key])  # take attributes
    geom = list(edge_attributes["geometry"].coords[:])
    edge_attributes.pop("geometry")  # remove geometry
    edge_attributes.pop("length")  # remove length
    G.remove_edge(node, node, key)
    f_num = node + 1  # find unique ID not already in the graph
    while f_num in G.nodes():
        f_num += 1
    s_num = f_num + 1
    while s_num in G.nodes():
        s_num += 1
    # Add nodes as the first and last point in the LineString geometry
    # if we don't count the original node of the self-loop
    G.add_node(f_num, x=geom[1][0], y=geom[1][1])
    G.add_node(s_num, x=geom[-2][0], y=geom[-2][1])
    # Connect them with edges keeping the attributes and having in total
    # the same geometry as before
    fp = LineString(geom[:2])
    sp = LineString(geom[-2:])
    tp = LineString(geom[1:-1])
    G.add_edge(node, f_num, key=0, **edge_attributes, geometry=fp, length=fp.length)
    G.add_edge(node, s_num, key=0, **edge_attributes, geometry=sp, length=sp.length)
    G.add_edge(f_num, s_num, key=0, **edge_attributes, geometry=tp, length=tp.length)
    return G


def _solve_multiple_path(G, node, other_node):
    """
    Transform multiple paths between nodes by adding artifical nodes on every path but one.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        MultiDiGraph we want to transform.
    node : int
        First node's ID.
    other_node : int
        Second node's ID.

    Returns
    -------
    G : networkx.MultiDiGraph
        MultiDiGraph with the multiple path issue solved.

    """
    # for every path but one, to add as little number of node as needed
    count = 0
    straigth_key = []
    initial_n_edges = G.number_of_edges(node, other_node)
    initial_key_list = list(G.get_edge_data(node, other_node).keys())
    for i in initial_key_list:
        if count == initial_n_edges - 1:
            break
        elif len(list(G.edges[node, other_node, i]["geometry"].coords[:])) > 2:
            # take attributes
            edge_attributes = dict(G.edges[node, other_node, i])
            geom = list(edge_attributes["geometry"].coords[:])
            edge_attributes.pop("geometry")  # remove geometry
            edge_attributes.pop("length")  # remove length
            G.remove_edge(node, other_node, i)
            p_num = node + 1  # find ID that is not already in the graph
            while p_num in G.nodes():
                p_num += 1
            # add node as the first point of the geometry
            G.add_node(p_num, x=geom[1][0], y=geom[1][1])
            # Connect it with edges keeping the attributes and having in total
            # the same geometry as before
            fp = LineString(geom[:2])
            sp = LineString(geom[1:])
            G.add_edge(
                node, p_num, key=0, **edge_attributes, geometry=fp, length=sp.length
            )
            G.add_edge(
                p_num,
                other_node,
                key=0,
                **edge_attributes,
                geometry=sp,
                length=sp.length,
            )
            count += 1
        else:  # if straight line
            straigth_key.append(i)
    if count < G.number_of_edges(node, other_node) - 1:
        while count < G.number_of_edges(node, other_node) - 1:
            f_key = straigth_key[0]
            edge_attributes = dict(G.edges[node, other_node, f_key])
            geom = list(edge_attributes["geometry"].coords[:])
            edge_attributes.pop("geometry")  # remove geometry
            edge_attributes.pop("length")  # remove length
            mid_x = (geom[0][0] + geom[1][0]) / 2.0  # take middle coordinates
            mid_y = (geom[0][1] + geom[1][1]) / 2.0
            geom.insert(1, (mid_x, mid_y))  # insert it into the geometry
            G.remove_edge(node, other_node, f_key)
            p_num = node + 1  # find ID that is not already in the graph
            while p_num in G.nodes():
                p_num += 1
            # add node as the first point of the geometry
            G.add_node(p_num, x=geom[1][0], y=geom[1][1])
            # Connect it with edges keeping the attributes and having in total
            # the same geometry as before
            fp = LineString(geom[:2])
            sp = LineString(geom[1:])
            G.add_edge(
                node, p_num, key=0, **edge_attributes, geometry=fp, length=sp.length
            )
            G.add_edge(
                p_num,
                other_node,
                key=0,
                **edge_attributes,
                geometry=sp,
                length=sp.length,
            )
            straigth_key.remove(f_key)
            count += 1
    return G
