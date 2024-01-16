# -*- coding: utf-8 -*-
"""
Functions to measure metrics of a graph.
"""


import networkx as nx
import random
import itertools
import numpy as np
from blp.utils import get_node_positions, dist, dist_vector


def get_edgelist_shortest_path(G):
    """
    Make a dictionary where keys are edge being part of a shortest path
    between at least one pair of node in the graph G, and values are the
    list of pairs of nodes where the edge is part of the shortest path
    between the two. Edges are represented by their index, so we have
    {edge_a:[[node_1, node_2], [node_1, node_3], ...],
     edge_b:..., 
     ...}

    Parameters
    ----------
    G : networkx.classes.graph.Graph
        Networkx Graph .

    Returns
    -------
    edgelist : dict
        Dictionary of the edges part of shortest paths on the graph G.

    """
    edgelist = dict()
    for path in dict(nx.all_pairs_dijkstra(G, weight='length')).values():
        for sp in path[1].values():
            for f_node, s_node in zip(sp[:-1], sp[1:]):
                edge_id = G.edges[f_node, s_node]['index']
                if edge_id in edgelist:
                    edgelist[edge_id].append([sp[0], sp[-1]])
                else:
                    edgelist[edge_id] = [[sp[0], sp[-1]]]
    return edgelist


def get_directness_matrix_networkx(G):
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
    G : networkx.classes.graph.Graph
        Networkx Graph on which we want to measure directness

    Returns
    -------
    numpy.ndarray
        2D Array of the ratio between the shortest network distance and
        the euclidean distance between every pair of nodes if separate
        is False. Else, separate 2D Arrays for the shortest network
        distance and the euclidean distance

    """
    shortest_matrix = get_shortest_network_path_matrix(G)
    euclidean_matrix = get_euclidean_distance_matrix(G)
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
    G : networkx.classes.graph.Graph
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
    for ids, dic in sorted(dict( # sort the dict then keys of each dict
            nx.all_pairs_dijkstra_path_length(G, weight='length')).items()):
        shortest_matrix.append([val for key, val in 
                                sorted(_fill_dict(dic, node_list).items())])
    shortest_matrix = np.array(shortest_matrix)
    return shortest_matrix

def _fill_dict(dictionary, n_list):
    """Fill dictionary with 0 for node without a value."""
    for node in n_list:
        if node not in dictionary:
            dictionary[node] = 0.0
    return dictionary


def get_euclidean_distance_matrix(G):
    """
    Return a matrix of the euclidean distance between every
    pairs of nodes in the graph G. The matrix is a square matrix (N,N),
    N being the number of nodes in G. The matrix is symmetrical and
    the diagonal values are null. The index of the rows and columns
    are sorted by nodes' ID in ascending order.

    Parameters
    ----------
    G : networkx.classes.graph.Graph
        Networkx Graph on which we want to measure euclidean distance.

    Returns
    -------
    euclidean_matrix : numpy.ndarray
        2D Array of the euclidean distance on the network between every 
        pairs of nodes.

    """
    pos_list = get_node_positions(G, package='networkx')
    euclidean_matrix = []
    for pos in pos_list:
        euclidean_matrix.append(dist_vector([pos]*len(pos_list), pos_list))
    euclidean_matrix = np.array(euclidean_matrix)
    return euclidean_matrix


def avoid_zerodiv_matrix(num_mat, den_mat, separate = False):
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
        nmat[dmat == 0.0] = 0.0 # avoid division by 0
        dmat[dmat == 0.0] = 1.0
        return nmat, dmat
    else:
        return np.divide(num_mat, den_mat,
                         out=np.zeros_like(num_mat), where=den_mat!=0)


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
    if np.count_nonzero(mat) == 0:
        print("Issue here:", mat)
        return 0
    return np.sum(mat)/np.count_nonzero(mat)


def remove_matrix_node(mat, ind):
    """Return directness matrix where we removed one node (row and column)"""
    # Equivalent in pandas : df.loc[df.columns != ind, df.columns != ind]
    return np.delete(np.delete(mat, ind, 0), ind, 1)


def get_sampled_directness_networkx(G, n = 500):
    """
    Return the sampled directness of the networkx connected graph G.
    The directness is the ratio between the sum of the euclidean distance
    and the shortest path length of all pairs of nodes in the network.
    To make it quicker, we can only take a sample of nodes n. Note that 
    if we want to take  every node or even a large share of the nodes,
    using get_directness_networkx will be substantially quicker. Since
    we sample a number of node, the value is an approximation, the bigger
    n is compared to the number of nodes of the network, the better this
    approximation is. Since we do every combinations of pairs of sampled
    nodes, there will be n(n-1)/2 iterations. Much slower than using
    get_sampled_directness_igraph (49s against 8s on 100 node
    for 8000 node graph)

    Parameters
    ----------
    G : networkx.classes.graph.Graph
        Connected graph.
    n : int, optional
        Number of nodes we will sample of the graph to measure the
        directness. The default is 500.

    Raises
    ------
    TypeError
        Return this error if G is not a connected graph.

    Returns
    -------
    float
        Value of the sampled directness of the graph.

    """
    if nx.number_connected_components(G) > 1:
        raise TypeError("Graph should be a connected component")
    else:
        shortest_dist = []
        euclidean_dist = []
        node_list = random.sample(list(G.nodes()), # Take sample of node
                                  min(n, len(G.nodes())))
        for i, j in itertools.combinations(node_list, 2): # For all pairs
                shortest_dist.append(nx.shortest_path_length(G, source=i,
                                                 target=j, weight='length'))
                euclidean_dist.append(dist(G.nodes[i], G.nodes[j]))
        return sum(euclidean_dist) / sum(shortest_dist)


def get_directness_networkx(G):
    """
    Return the directness of the networkx connected graph G.
    The directness is the ratio between the sum of the euclidean distance
    and the shortest path length of all pairs of nodes in the network. 
    Since we make a dictionary of dictionaries for every node, with keys
    for every node with as the value the length of the shortest path,
    this will take memory with N dictionaries of size N, N being the
    number of nodes in G.

    Parameters
    ----------
    G : networkx.classes.graph.Graph
        Connected graph.

    Raises
    ------
    TypeError
        Return this error if G is not a connected graph.

    Returns
    -------
    float
        Directness of the graph.

    """
    if nx.number_connected_components(G) > 1:
        raise TypeError("Graph should be a connected component")
    else:
        dict_length = dict(nx.all_pairs_dijkstra_path_length(
            G, weight='length')) # Make dict of dict of every shortest
        shortest_dist = 0 # Shortest path length
        for dic in dict_length.keys(): # Counting twice here
            shortest_dist += sum(dict_length[dic].values())
        pos_list = get_node_positions(G, package='networkx')
        comb = np.array(list(itertools.combinations(pos_list, 2))) # All pairs
        comb = np.reshape(comb, [2, comb.shape[0], 2])
        euclidean_dist = dist_vector(comb[0], comb[1])
        shortest_dist /= 2 # Divide by 2 to avoid counting twice
        return sum(euclidean_dist) / shortest_dist


def get_sampled_directness_igraph(G, n = 500):
    """
    From https://github.com/mszell/bikenwgrowth 
    Return the sampled directness of the igraph connected graph G.
    The directness is the ratio between the sum of the euclidean distance
    and the shortest path length of all pairs of nodes in the network.
    To make it quicker, we can only take a sample of nodes n. Since
    we sample a number of node, the value is an approximation, the bigger
    n is compared to the number of nodes of the network, the better this
    approximation is. We store in poi_edges and do the measure of distance
    in the end, it takes a lot of memory and potentially too much if we 
    put a n too big, but makes it quicker. Much quicker than using
    get_sampled_directness_networkx (8s against 49s on 100 node
    for 8000 node graph)

    Parameters
    ----------
    G : igraph.Graph
        Connected graph.
    n : int, optional
        Number of nodes we will sample of the graph to measure the
        directness. The default is 500.

    Raises
    ------
    TypeError
        Return this error if G is not a connected graph.

    Returns
    -------
    float
        Value of the sampled directness of the graph.

    """
    if len(list(G.clusters())) > 1:
        raise TypeError("Graph should be a connected component")
    indices = random.sample(list(G.vs), min(n, len(G.vs)))
    poi_edges = [] 
    total_distance_direct = 0
    for c, v in enumerate(indices):
        poi_edges.append(G.get_shortest_paths( # Store shortest path
            v, indices[c:], weights = "length", output = "epath"))
        temp = G.get_shortest_paths(
            v, indices[c:], weights = "length", output = "vpath")
        total_distance_direct += sum(
            dist_vector([(G.vs[t[0]]["y"], G.vs[t[0]]["x"]) for t in temp],
                        [(G.vs[t[-1]]["y"], G.vs[t[-1]]["x"]) for t in temp])) 
    total_distance_network = 0
    for paths_e in poi_edges:
        for path_e in paths_e:
            # total_distance_network += sum([G.es[e]['length'] # Slower one
            #                                for e in path_e])
            total_distance_network += sum(
                G.es.select(path_e).get_attribute_values('length'))
    return total_distance_direct / total_distance_network


def get_directness_igraph(G, detailed = False):
    """
    Return the directness of the igraph connected graph G.
    The directness is the ratio between the sum of the euclidean distance
    and the shortest path length of all pairs of nodes in the network. 
    Since we make a dictionary of dictionaries for every node, with keys
    for every node with as the value the length of the shortest path,
    this will take memory with N dictionaries of size N, N being the
    number of nodes in G.

    Parameters
    ----------
    G : igraph.Graph
        Connected graph.

    Raises
    ------
    TypeError
        Return this error if G is not a connected graph.

    Returns
    -------
    float
        Directness of the graph.

    """
    if len(list(G.clusters())) > 1:
        raise TypeError("Graph should be a connected component")
    else:
        shortest_dist = 0
        for node in range(len(G.vs())):
            shortest_paths = G.get_shortest_paths( # Find every shortest path
                node, weights='length', output='epath') # from one node
            for path in shortest_paths: # Sum all of these path
                shortest_dist += sum( # Counting twice here
                    G.es.select(path).get_attribute_values('length'))
        pos_list = get_node_positions(G, package='igraph')
        comb = np.array(list(itertools.combinations(pos_list, 2))) # All pairs
        comb = np.reshape(comb, [2, comb.shape[0], 2])
        euclidean_dist = dist_vector(comb[0], comb[1])
        shortest_dist /= 2 # Divide by 2 to avoid counting twice
        return sum(euclidean_dist) / shortest_dist


# TODO: Understand how this one works
def get_directness_linkwise_igraph(G, n = 500):
    """
    From https://github.com/mszell/bikenwgrowth
    Calculate directness on G over all connected node pairs in indices.
    This is maybe the common calculation method: It takes the average
    of linkwise euclidean distances divided by network distances.
    If G has multiple components, node pairs in different components
    are discarded.
    
    Parameters
    ----------
    G : igraph.Graph
        Graph.
    n : int, optional
        Number of nodes we will sample of the graph to measure the
        directness. The default is 500.

    Returns
    -------
    float
        Value of the sampled directness of the graph.

    """
    indices = random.sample(list(G.vs), min(n, len(G.vs)))

    directness_links = np.zeros(int((len(indices)*(len(indices)-1))/2))
    ind = 0
    for c, v in enumerate(indices):
        poi_edges = G.get_shortest_paths(
            v, indices[c:], weights = "length", output = "epath")
        # Discard first empty list because it is the node to itself
        for c_delta, path_e in enumerate(poi_edges[1:]): 
        # if path is non-empty, meaning the node pair is in the same component
            if path_e: 
                # sum over all edges of path
                distance_network = sum([G.es[e]['length'] for e in path_e]) 
                # dist first to last node, must be in format lat,lon = y, x
                distance_direct = dist(v, indices[c+c_delta+1]) 

                directness_links[ind] = distance_direct / distance_network
                ind += 1
    directness_links = directness_links[:ind] # discard disconnected node pairs

    return np.mean(directness_links)

