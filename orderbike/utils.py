# -*- coding: utf-8 -*-
"""
New functions and original and modified functions from OSMnx in order to
simplify the graph by removing interstitial nodes and by going from a
multidigraph to a graph.
"""

import logging

import numpy as np
from haversine import haversine, haversine_vector
from networkx import Graph, get_node_attributes, set_edge_attributes
from osmnx import get_undirected
from shapely.geometry import LineString
from sklearn.metrics import auc

# Root logger that is then used in functions in growth and metrics. Comment filename to avoid saving results, change level to keep only some messages.
logging.basicConfig(
    filename="growth.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
log = logging.getLogger()


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


def clean_isolated_node(G):
    """Remove every node of G that has no link to any other node"""
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


# TODO give level of bikeability instead of boolean as an option
def OSM_bicycle_tag():
    biketags = {}
    biketags["sidewalk:left:bicycle"] = "yes"
    biketags["sidewalk:left:right"] = "yes"
    biketags["cycleway:left"] = ["shared_lane", "shared_busway", "track"]
    biketags["cycleway:right"] = ["shared_lane", "shared_busway", "track"]
    biketags["cycleway:both"] = "lane"
    biketags["cycleway"] = ["shared_lane", "shared_busway", "opposite_lane", "opposite"]
    biketags["bicycle"] = ["designated", "yes", "official", "use_sidepath"]
    biketags["highway"] = ["cycleway", "bridleway"]
    biketags["cyclestreet"] = "yes"
    biketags["bicycle_road"] = "yes"
    return biketags


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
    """Find all node positions x (longitude) and y (latitude) from the graph G and put them into a numpy array."""
    lon = [val for key, val in sorted(get_node_attributes(G, "x").items())]
    lat = [val for key, val in sorted(get_node_attributes(G, "y").items())]
    return np.transpose(np.array([lat, lon]))


def multidigraph_to_graph(G):
    """
    Transform a spatial networkx.MultiDiGraph into a networkx.Graph, keeping all edges by adding artificial nodes. We need to add two  nodes inside a self-loop, and one node for each parallel paths between two nodes.
    """
    G = G.copy()
    # Make compatible with osmnx function
    if "osmid" not in list(G.edges(data=True))[0][2].keys():
        set_edge_attributes(G, 0, "osmid")
    # Use osmnx function that keep all edges that have different geometries
    G = get_undirected(G)
    # Put list of node as independent variable to make changes on the graph in the loop
    initial_node_list = list(G.nodes())
    for node in initial_node_list:
        neighbors = np.transpose(list(G.edges(node)))[1]
        # Node in its neighbors mean that there is a self-loop
        if node in neighbors:
            for k in list(G.get_edge_data(node, node).keys()):
                G = _solve_self_loop(G, node, k)
        for neigh in neighbors:
            # More than 2 edges between the same nodes means there are multiple paths
            if G.number_of_edges(node, neigh) > 1:
                G = _solve_multiple_path(G, node, neigh)
    G = Graph(G)
    return G


def _solve_self_loop(G, node, key):
    """
    Remove a self-loop where a node is connected to itself by adding two nodes in the geometry of the loop.

    Args:
        G (networkx.MultiGraph): MultiGraph where there is a self-loop that we want to remove.
        node (int): ID of the node where there is a self-loop.
        key (int): Key of the self-loop edge as we are in a MultiDiGraph.

    Returns:
        networkx.MultiGraph : MultiGraph with the self-loop removed.
    """
    edge_attributes = dict(G.edges[node, node, key])
    geom = list(G.edges[node, node, key]["geometry"].coords[:])
    edge_attributes.pop("geometry")
    edge_attributes.pop("length")
    G.remove_edge(node, node, key)
    # Find unique ID not already in the graph
    f_num = max(G.nodes) + 1
    s_num = f_num + 1
    # Add nodes as the first and last point in the LineString geometry
    G.add_node(f_num, x=geom[1][0], y=geom[1][1])
    G.add_node(s_num, x=geom[-2][0], y=geom[-2][1])
    # Connect them with edges keeping the attributes, with the sum of all geometries being the original loop
    fp = LineString(geom[:2])
    sp = LineString(geom[-2:])
    tp = LineString(geom[1:-1])
    G.add_edge(node, f_num, key=0, **edge_attributes, geometry=fp, length=fp.length)
    G.add_edge(node, s_num, key=0, **edge_attributes, geometry=sp, length=sp.length)
    G.add_edge(f_num, s_num, key=0, **edge_attributes, geometry=tp, length=tp.length)
    return G


def _solve_multiple_path(G, node, other_node):
    """
    Remove multiple paths between two nodes by adding a node for each path but one.

    Args:
        G (networkx.MultiGraph): MultiGraph where there are multiple paths that we want to remove.
        node (int): ID of the first node
        other_node (int): ID of the second node

    Returns:
        networkx.MultiGraph : MultiGraph with the multiple paths removed.
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
