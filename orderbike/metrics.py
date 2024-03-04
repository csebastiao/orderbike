# -*- coding: utf-8 -*-
"""
Functions to measure metrics of a graph.
"""

import networkx as nx
import numpy as np

from orderbike.utils import dist_vector, get_node_positions


def get_directness_matrix(G, lonlat=True):
    """
    Make a matrix of the ratio between the shortest network distance and
    the euclidean distance between every pair of nodes. When nodes are
    from separate components, this ratio is equal to 0. Take advantage
    of the speed of networkx.all_pairs_dijkstra_path_length that we
    sort in order to have a matrix order by node's ID in ascending order.
    We can use utils.create_node_index in order to have a dictionary
    between the index and the node's ID.

    Parameters
    ----------
    G : networkx.Graph
        Networkx Graph on which we want to measure directness
    lonlat : bool, optional
        If True, find the haversine distance between the nodes, else take the positions of the nodes in meters. Defaults to True.

    Returns
    -------
    numpy.ndarray
        2D Array of the ratio between the shortest network distance and
        the euclidean distance between every pair of nodes if separate
        is False. Else, separate 2D Arrays for the shortest network
        distance and the euclidean distance

    """
    shortest_matrix = get_shortest_network_path_matrix(G)
    euclidean_matrix = get_euclidean_distance_matrix(G, lonlat=lonlat)
    return avoid_zerodiv_matrix(euclidean_matrix, shortest_matrix)


def get_shortest_network_path_matrix(G):
    """
    Return a matrix of the shortest path on the network between every
    pairs of nodes in the graph G. The matrix is a square matrix (N,N),
    N being the number of nodes in G. The matrix is symmetrical and
    the diagonal values are null. The index of the rows and columns
    are sorted by nodes' ID in ascending order.

    Parameters
    ----------
    G : networkx.Graph
        Networkx Graph on which we want to measure shortest network
        path.

    Returns
    -------
    shortest_matrix : numpy.ndarray
        2D Array of the shortest path on the network between every
        pairs of nodes.

    """
    node_list = list(G.nodes)
    shortest_matrix = []
    for ids, dic in sorted(
        dict(  # sort the dict then keys of each dict
            nx.all_pairs_dijkstra_path_length(G, weight="length")
        ).items()
    ):
        shortest_matrix.append(  # add 0 values for nodes not in the same components
            [val for key, val in sorted(_fill_dict(dic, node_list).items())]
        )
    return np.array(shortest_matrix)


def _fill_dict(dictionary, n_list):
    """Fill dictionary with 0 for node without a value."""
    for node in n_list:
        if node not in dictionary:
            dictionary[node] = 0.0
    return dictionary


def get_euclidean_distance_matrix(G, lonlat=True):
    """
    Return a matrix of the euclidean distance between every
    pairs of nodes in the graph G. The matrix is a square matrix (N,N),
    N being the number of nodes in G. The matrix is symmetrical and
    the diagonal values are null. The index of the rows and columns
    are sorted by nodes' ID in ascending order.

    Parameters
    ----------
    G : networkx.Graph
        Networkx Graph on which we want to measure euclidean distance.
    lonlat : bool, optional
        If True, find the haversine distance between the nodes, else take the positions of the nodes in meters. Defaults to True.

    Returns
    -------
    euclidean_matrix : numpy.ndarray
        2D Array of the euclidean distance on the network between every
        pairs of nodes.

    """
    pos_list = get_node_positions(G)
    if lonlat:
        euclidean_matrix = [
            dist_vector([pos] * len(pos_list), pos_list) for pos in pos_list
        ]
    else:
        euclidean_matrix = [
            [np.linalg.norm(pos - other_pos) for other_pos in pos_list]
            for pos in pos_list
        ]
    return np.array(euclidean_matrix)


def avoid_zerodiv_matrix(num_mat, den_mat, separate=False):
    """
    Adapt two matrix to be able to divise (value per value) the
    numerator matrix to the denominator matrix by avoiding division
    by 0. In order to do so, the zero in the denominator are
    replaced by a constant value, and for the same index the numerator
    values are replaced by 0. As such, division by 0 are replaced by
    a 0. Using
    https://stackoverflow.com/questions/26248654/how-to-return-0-with-divide-by-zero

    Parameters
    ----------
    num_mat : numpy.ndarray
        Matrix on the numerator.
    den_mat : numpy.ndarray
        Matrix on the denominator.
    separate : bool, optional
        If True, return the adapted matrix separately, else return the
        division of the two matrix. The default is False.

    Returns
    -------
    numpy.ndarray
        If separate is True, return separately both matrix with values
        adapted, else return the division of the numerator by the
        denominator.

    """
    if separate is True:
        nmat = num_mat.copy()
        dmat = den_mat.copy()
        nmat[dmat == 0.0] = 0.0  # avoid division by 0
        dmat[dmat == 0.0] = 1.0
        return nmat, dmat
    else:
        return np.divide(
            num_mat, den_mat, out=np.zeros_like(num_mat), where=den_mat != 0
        )


def directness_from_matrix(mat):
    """
    Return the directness from a matrix (N, N), N being the number of
    nodes in a given graph. We can't do a simple mean as every diagonal
    values, and every values between nodes from different components are
    equal to 0 and should be discarded, so we divide by the number of
    nonzero value.

    Parameters
    ----------
    mat : numpy.ndarray
        2D Array of the ratio between the shortest network distance and
        the euclidean distance between every pair of nodes.

    Returns
    -------
    float
        Linkwise directness of the graph corresponding to mat.

    """
    return np.sum(mat) / np.count_nonzero(mat)
