# -*- coding: utf-8 -*-
"""
Useful functions
"""


import numpy as np
import networkx as nx
from sklearn.metrics import auc
from haversine import haversine, haversine_vector


def dist(v1, v2):
    """
    From https://github.com/mszell/bikenwgrowth
    Return the haversine distance in meters between the points v1 and v2,
    where v1 and v2 are dictionary written like
    v = {'x': longitude, 'y': latitude}.
    """
    return haversine((v1['y'], v1['x']), (v2['y'], v2['x']), unit="m")


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


# TODO: Make pandas DataFrame so we can have both in same object,
# just having to change index filter to revert it ?
def create_node_index(G, revert = False):
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


def create_edge_index(G, revert = False):
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


def make_summary(G):
    """Print a summary of useful information on the graph G."""
    lcc_G = G.subgraph(max(nx.connected_components(G), key=len)).copy()
    print("""
          Number of nodes: {} \n
          Number of edges: {} \n
          Number of connected components: {} \n
          Size of the largest connected components: {} nodes and {} edges
          """.format(
          len(G.nodes), len(G.edges), len(list(nx.connected_components(G))),
          len(lcc_G.nodes), len(lcc_G.edges)
          ))


def get_node_positions(G, package = 'networkx'):
    """
    Get sorted array of coordinates of every node of the graph G. We can
    get nodes' positions for networkx graph or igraph graph. The nodes 
    are sorted either by their ID on networkx or by the index on igraph.

    Parameters
    ----------
    G : networkx.classes.graph.Graph or igraph.Graph
        Graph, type need to correspond to the package argument.
    package : str, optional
        Either networkx or igraph, specify the type of graph we use.
        The default is 'networkx'.

    Raises
    ------
    ValueError
        Argument for the argument package is not networkx nor igraph.

    Returns
    -------
    pos_list : list
        List of coordinates of every nodes.

    """
    if package == 'networkx': # sorted by node's ID
        lon = [val for key, val in
               sorted(nx.get_node_attributes(G, 'x').items())]
        lat = [val for key, val in
               sorted(nx.get_node_attributes(G, 'y').items())]
    elif package == 'igraph': # sorted by node's index
        lon = G.vs.get_attribute_values('x')
        lat = G.vs.get_attribute_values('y')
    else:
        raise ValueError("package need to be networkx or igraph")
    pos_list = np.transpose(np.array([lat, lon]))
    return pos_list


def clean_isolated_node(G):
    """Remove every node that has no link to any other node"""
    H = G.copy()
    for node in  G.nodes:
        if H.degree(node) == 0:
            H.remove_node(node)
    return H


def find_isolated_node(G):
    """Find every node that has no link to any other node"""
    islist = []
    for node in  G.nodes:
        if G.degree(node) == 0:
            islist.append(node)
    return islist


def create_bicycle_subgraph(G, attr_name = 'protected_bicycling'):
    """
    Make a subgraph of the graph G as to create a bicycle network
    from a road network with a boolean attribute for bikeable street.

    Parameters
    ----------
    G : networkx.classes.graph.Graph
        Road network with an attribute for bikeable street.
    attr_name : str, optional
        Name of the boolean attribute saying whether or not there are 
        protected bicycling infrastructure.
        The default is 'protected_bicycling'.

    Returns
    -------
    bicycle_subgraph : networkx.classes.graph.Graph
        Protected bicycling infrastructure subgraph.

    """
    df = nx.to_pandas_edgelist(G)
    filtered_df = df[df[attr_name] == True]
    edgelist = filtered_df.loc[:, ['source', 'target']].values.tolist()
    edgelist = [tuple(x) for x in edgelist] # In order to make it hashable
    bicycle_subgraph = G.edge_subgraph(edgelist).copy()
    # crs = G.graph['crs'] # Alt, as quick but more attribute manip
    # bicycle_subgraph = nx.from_pandas_edgelist(filtered_df, edge_attr=True) 
    # bicycle_subgraph.graph['crs'] = crs
    # for node in bicycle_subgraph.nodes():
    #     for attr in G.nodes[node]:
    #         bicycle_subgraph.nodes[node][attr] = G.nodes[node][attr]
    return bicycle_subgraph

def add_edge_index(G):
    """Add a unique index to every edge to get a quick access"""
    H = G.copy()
    count = 0
    for edge in G.edges:
        H.edges[edge]['index'] = count
        count += 1
    return H


def get_area_under_curve(curve, xx = None,
                         normalize_y=False, normalize_x=False):
    """Get area under the curve to compare the efficiency of a curve"""
    if xx is None:
        xx = range(len(curve))
    if normalize_y is True:
        curve = (curve - np.min(curve)) / (np.max(curve) - np.min(curve))
    if normalize_x is True:
        return (auc(xx, curve) - np.min(xx))/(
            np.max(xx) - np.min(xx))
    else:
        return auc(xx, curve)