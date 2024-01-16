# -*- coding: utf-8 -*-
"""
Functions to make subtractive or additive growth of a graph.
"""

import os
import cProfile
import pstats
import io
import tqdm
import pickle
import numpy as np
import random
import networkx as nx
import pyproj
import shapely
from blp import metrics
from blp import utils

# TODO: Add automatic projected crs with osmnx
# TODO: Track length history at every step, add as another metric

def optimize_subtractive_growth(
        G, folder_name, metric_optimized, local_proj, buff_size = 500,
        override_naming = False, built = True,
        keep_connected = True, profiling = True, 
        save_network = True, save_metrics = True):
    """
    Optimize the subtractive growth of a network G based on a metric that
    we want to optimize.

    Parameters
    ----------
    G : networkx.classes.graph.Graph
        Final network.
    folder_name : str
        Name of the folder. If override_naming is True, then full name
        of the folder, otherwise standardized suffixe are added based on
        the options of the functions.
    metric_optimized : str
        Name of the metric optimized. Can be directness,
        relative_directness, coverage, relative_coverage and 
        global_efficiency.
    local_proj : str
        Projected crs of the graph. If None, tries to find it based on the
        latitude and longitude position of a node in the graph.
    buff_size : float, optional
        Size of the buffer used to measure the coverage.
        The default is 500.
    override_naming : bool, optional
        If True, then the folder_name is the full name and nothing is
        added. The default is False.
    built : bool, optional
        If True, make a difference between the built part of the network
        and the planned part. The default is True.
    keep_connected : bool, optional
        If True, the number of components of the graph can never exceed 1
        if there is not a built network, or the number of components
        of the built network. The default is True.
    profiling : bool, optional
        If True, make a profile of the time spent by the function on 
        various functions. The default is True.
    save_network : bool, optional
        If True, save G as final_network.gpickle in the result's folder.
        The default is True.
    save_metrics : bool, optional
        If True, save the metrics coverage and directness as arrays
        in the result's folder, under the name
        arrcov.pickle and arrdir.pickle.
        The default is True.

    Raises
    ------
    ValueError
        Raised if the value of the input metric_optimized is not a 
        possible value. metric_optimized can be directness,
        relative_directness, coverage, relative_coverage and 
        global_efficiency.

    Returns
    -------
    folder_name : str
        Final name of the folder where the results are stored. If 
        override_naming is true, same as the input folder_name.

    """
    # Verify that input is valid
    if metric_optimized not in ['directness', 'relative_directness',
                                'coverage', 'relative_coverage', 
                                'global_efficiency']:
        raise ValueError("""
                         Wrong value for metric_optimized, see
                         documentation for valid metric name.
                         """)
    if profiling is True:
        pr = cProfile.Profile()
        pr.enable()
    # If override_naming is False, then create a standardized name
    # based on the options used for the optimization
    if override_naming is False:
        if built is True:
            folder_name += "_built"
        if keep_connected is True:
            folder_name += "_connected"
        folder_name += f"_subtractive_bf{buff_size}_{metric_optimized}"
    # Make a new folder with the name where every results will be stored
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    if save_network is True:
        nx.write_gpickle(G, folder_name + "/final_network.gpickle")

    G = G.copy() # Create a copy to not mutate input
    if built is True:
        edgelist = [edge for edge in G.edges 
                    if G.edges[edge]['built'] == 0]
    else:
        edgelist = [edge for edge in G.edges]
    # Coverage
    geom = dict()
    project = pyproj.Transformer.from_proj(
            pyproj.Proj(init=pyproj.CRS('epsg:4326')),
            pyproj.Proj(init=pyproj.CRS(local_proj)))
    for edge in G.edges:
        geom[edge] = shapely.ops.transform(
            project.transform,
            G.edges[edge]['geometry']).buffer(buff_size)
    bef_area = shapely.ops.unary_union(list(geom.values())).area
    cov_hist = [bef_area]
    # Directness
    sm = metrics.get_shortest_network_path_matrix(G)
    em = metrics.get_euclidean_distance_matrix(G)
    dm = metrics.avoid_zerodiv_matrix(em, sm)
    d = metrics.directness_from_matrix(dm)
    dir_hist = [d]
    c_hist = []
    # Optimize based on metric_optimized. First we find the edge to remove
    # that is optimizing the metric that we want, then we make the changes
    # to the graph and to the history of choices and metrics values
    if built is True:
        n_iter = range(len(edgelist))
    else:
        n_iter = range(len(edgelist) - 1)
    if keep_connected is True and built is True:
        built_components = list(nx.connected_components(G.edge_subgraph(
            [edge for edge in G.edges if G.edges[edge]['built'] == 1])))
        elected_nodes = []
        for cc in built_components:
            elected_nodes.append(list(G.subgraph(cc).nodes)[0])
    else:
        elected_nodes = None
    if metric_optimized == 'directness':
        for i in tqdm.tqdm(n_iter):
            new_m, choice = directness_subtractive_step(
                G, edgelist, em, elected_nodes, keep_connected=keep_connected)
            edgelist, em, sm, geom, c_hist, dir_hist, cov_hist = (
                _make_subtractive_changes(G, choice, edgelist, em, sm, geom,
                                          c_hist, dir_hist, cov_hist))
    elif metric_optimized == 'relative_directness':
        for i in tqdm.tqdm(n_iter):
            new_m, choice = relative_directness_subtractive_step(
                G, edgelist, sm, elected_nodes, keep_connected=keep_connected)
            edgelist, em, sm, geom, c_hist, dir_hist, cov_hist = (
                _make_subtractive_changes(G, choice, edgelist, em, sm, geom,
                                          c_hist, dir_hist, cov_hist))
    elif metric_optimized == 'coverage':
        for i in tqdm.tqdm(n_iter):
            new_m, choice = coverage_subtractive_step(
                G, edgelist, geom, elected_nodes, keep_connected=keep_connected)
            edgelist, em, sm, geom, c_hist, dir_hist, cov_hist = (
                _make_subtractive_changes(G, choice, edgelist, em, sm, geom,
                              c_hist, dir_hist, cov_hist))
    elif metric_optimized == 'relative_coverage':
        for i in tqdm.tqdm(n_iter):
            new_m, choice = relative_coverage_subtractive_step(
                G, edgelist, cov_hist[-1], geom, elected_nodes,
                keep_connected=keep_connected)
            edgelist, em, sm, geom, c_hist, dir_hist, cov_hist = (
                _make_subtractive_changes(G, choice, edgelist, em, sm, geom,
                                          c_hist, dir_hist, cov_hist))
    elif metric_optimized == 'global_efficiency':
        for i in tqdm.tqdm(n_iter):
            new_m, choice = global_efficiency_subtractive_step(
                G, edgelist, em, elected_nodes, keep_connected=keep_connected)
            edgelist, em, sm, geom, c_hist, dir_hist, cov_hist = (
                _make_subtractive_changes(G, choice, edgelist, em, sm, geom,
                                          c_hist, dir_hist, cov_hist))
    # Save directness, coverage and choice of edge as pickle file
    if save_metrics is True:
        with open(folder_name + "/arrdir.pickle", "wb") as fp:
            pickle.dump(dir_hist, fp)
        with open(folder_name + "/arrcov.pickle", "wb") as fp:
            pickle.dump(cov_hist, fp)
    with open(folder_name + "/arrchoice.pickle", "wb") as fp:
        pickle.dump(c_hist, fp)
    if profiling is True:
        pr.disable()
        s = io.StringIO() # get results of profiler in a text file
        ps = pstats.Stats(pr, stream=s).sort_stats('tottime')
        ps.print_stats()
        with open(folder_name + '/profile.txt', 'w+') as f:
            f.write(s.getvalue())
    return folder_name

def _make_subtractive_changes(
        G, choice, edgelist, em, sm, geom,
        c_hist, dir_hist, cov_hist):
    """
    Append values to their history list, modify arrays and graph based
    on edge and nodes removed for the optimize_subtractive_growth 
    function at every step.

    Parameters
    ----------
    G : networkx.classes.graph.Graph
        Network on which we do our analysis.
    choice : list
        Edge that we removed defined by the node that are connected,
        as (u, v), u and v being the nodes' ID connected by the edge.
    edgelist : list
        List of all the edges considered to be removed of G. Edges are
        defined like choice.
    em : numpy.ndarray
        Euclidian matrix, see metrics.get_euclidean_distance_matrix.
    sm : numpy.ndarray
        Shortest path matrix, see metrics.get_shortest_network_path_matrix.
    geom : dict
        Dictionary of the buffered geometry of the edges of G, see
        optimize_subtractive_growth.
    c_hist : list
        History of the edges removed.
    dir_hist : list
        History of the directness value, defined as the mean of the sum
        of the ratio of euclidian and shortest network path distance 
        between every pairs of nodes in the same component.
    cov_hist : list
        History of the coverage value, defined as the area of the union
        of all the buffered geometry of the edges of G.

    """
    c_hist.append(choice)
    G.remove_edge(*choice) # G mutated outside, don't need to return
    edgelist.remove(choice)
    node_removed = utils.find_isolated_node(G) # find node without edge
    for n in node_removed:
        node_index = utils.create_node_index(G)
        em = np.delete(em, node_index[n], 0) # delete row
        em = np.delete(em, node_index[n], 1) # delete column
        sm = np.delete(sm, node_index[n], 0) # delete row
        sm = np.delete(sm, node_index[n], 1) # delete column
        G.remove_node(n) # remove the isolated node
    # Directness
    dir_hist.append(metrics.directness_from_matrix(
        metrics.avoid_zerodiv_matrix(
            em, metrics.get_shortest_network_path_matrix(G))))
    # Coverage
    geom.pop(choice)
    bef_area = shapely.ops.unary_union(list(geom.values())).area
    cov_hist.append(bef_area)
    # We return updated value
    return edgelist, em, sm, geom, c_hist, dir_hist, cov_hist

def _is_disconnected(G, elected_nodes):
    # In some cases, removing an edge can create an isolated node
    # that we will discard but increases the number of components,
    # so we need to make sure to pass only the edges that create
    # an additional components larger than 1 node.
    if elected_nodes is None:
        if (nx.number_connected_components(G) > 1) and (
                len(sorted(nx.connected_components(G), key=len)[0]) > 1):
            return True
        else:
            return False
    else:
        res = False
        for cc in list(nx.connected_components(G)):
            if len(cc) > 1:
                test = False
                for n in elected_nodes:
                    if n in cc:
                        test = True
                if test is False:
                    res = True
        return res
            


# TODO: Optimize by finding minimum cut set of size 1 and remove these of the
# edgelist we try instead of passing edges that disconnect the network
def directness_subtractive_step(
        G, edgelist, euclid_mat, elected_nodes, keep_connected = False):
    """
    Find the edge to remove on the graph G that optimizes the directness, 
    and that doesn't create an additional component if keep_connected is
    True. The directness is defined here as the linkwise directness 
    which is the sum of the ratio of the euclidean distance and the
    shortest network distance between every pairs of nodes that are on
    the same component.

    Parameters
    ----------
    G : networkx.classes.graph.Graph
        Graph on which we want to remove an edge.
    edgelist : list
        List of the edges that we can remove.
    euclid_mat : numpy.ndarray
        Array of the euclidean distance between every pairs of nodes of
        the graph G, see metrics.get_euclidean_distance_matrix().
    keep_connected : bool, optional
        If True, edges that can be removed are not creating a new 
        component. The default is False.
    elected_nodes : None or list
        If None, we don't have at the same time a built part with the
        connectedness constraint. Else, the elected nodes are one
        node of each built components, that we use to test if the
        network is connected or not.

    Returns
    -------
    new_m : float
        Value of the directness if the edge chosen is removed from G.
    choice : tuple
        Edge chosen that optimizes the directness if removed,
        defined as the 2 nodes' ID (u,v).

    """
    batch_m = [] # List of metric value after an edge have been removed
    batch_choice = [] # List of corresponding edge removed
    if keep_connected is True:
        for edge in edgelist:
            H = G.copy()
            H.remove_edge(*edge)
            if _is_disconnected(H, elected_nodes) is True:
                pass
            else:
                new_sm = metrics.get_shortest_network_path_matrix(H)
                sdm = metrics.avoid_zerodiv_matrix(euclid_mat, new_sm)
                batch_m.append(metrics.directness_from_matrix(sdm))
                batch_choice.append(edge)
    else:
        for edge in edgelist:
            H = G.copy()
            H.remove_edge(*edge)
            new_sm = metrics.get_shortest_network_path_matrix(H)
            sdm = metrics.avoid_zerodiv_matrix(euclid_mat, new_sm)
            batch_m.append(metrics.directness_from_matrix(sdm))
            batch_choice.append(edge)
    try:
        new_m, choice = max(zip(batch_m, batch_choice))
    except:
        print('batch_m =', batch_m)
        new_m = max(batch_m)
        index_max = max(range(len(batch_m)), key=batch_m.__getitem__)
        choice = batch_choice[index_max]
    return new_m, choice


def relative_directness_subtractive_step(
        G, edgelist, shortest_mat, elected_nodes, keep_connected = False):
    """
    Find the edge to remove on the graph G that optimizes the relative
    directness, and that doesn't create an additional component if
    keep_connected is True. The relative directness is defined here as
    the sum of the ratio of the final shortest network distance and the
    actual shortest network distance between every pairs of nodes that are
    on the same component.

    Parameters
    ----------
    G : networkx.classes.graph.Graph
        Graph on which we want to remove an edge.
    edgelist : list
        List of the edges that we can remove.
    shortest_mat : numpy.ndarray
        Array of the shortest network distance between every pairs of
        nodes of the graph G, see 
        metrics.get_shortest_network_path_matrix().
    keep_connected : bool, optional
        If True, edges that can be removed are not creating a new 
        component. The default is False.
    elected_nodes : None or list
        If None, we don't have at the same time a built part with the
        connectedness constraint. Else, the elected nodes are one
        node of each built components, that we use to test if the
        network is connected or not.

    Returns
    -------
    new_m : float
        Value of the relative directness if the edge chosen is removed from G.
    choice : tuple
        Edge chosen that optimizes the relative directness if removed,
        defined as the 2 nodes' ID (u,v).

    """
    batch_m = [] # List of metric value after an edge have been removed
    batch_choice = [] # List of corresponding edge removed
    if keep_connected is True:
        for edge in edgelist:
            H = G.copy()
            H.remove_edge(*edge)
            if _is_disconnected(H, elected_nodes) is True:
                pass
            else:
                new_sm = metrics.get_shortest_network_path_matrix(H)
                sdm = metrics.avoid_zerodiv_matrix(shortest_mat, new_sm)
                batch_m.append(metrics.directness_from_matrix(sdm))
                batch_choice.append(edge)
    else:
        for edge in edgelist:
            H = G.copy()
            H.remove_edge(*edge)
            new_sm = metrics.get_shortest_network_path_matrix(H)
            sdm = metrics.avoid_zerodiv_matrix(shortest_mat, new_sm)
            batch_m.append(metrics.directness_from_matrix(sdm))
            batch_choice.append(edge)
    try:
        new_m, choice = max(zip(batch_m, batch_choice))
    except:
        new_m = max(batch_m)
        index_max = max(range(len(batch_m)), key=batch_m.__getitem__)
        choice = batch_choice[index_max]
    return new_m, choice


def global_efficiency_subtractive_step(
        G, edgelist, em, elected_nodes, keep_connected = False):
    """
    Find the edge to remove on the graph G that optimizes the global
    efficiency, and that doesn't create an additional component if
    keep_connected is True. The global efficiency is defined here as
    the ratio of the sum of the inverse of the shortest network distance
    and the sum of the inverse of the euclidean distance between every
    pairs of nodes that are on the same component.

    Parameters
    ----------
    G : networkx.classes.graph.Graph
        Graph on which we want to remove an edge.
    edgelist : list
        List of the edges that we can remove.
    em : numpy.ndarray
        Array of the euclidean distance between every pairs of nodes of
        the graph G, see metrics.get_euclidean_distance_matrix().
    keep_connected : bool, optional
        If True, edges that can be removed are not creating a new 
        component. The default is False.
    elected_nodes : None or list
        If None, we don't have at the same time a built part with the
        connectedness constraint. Else, the elected nodes are one
        node of each built components, that we use to test if the
        network is connected or not.

    Returns
    -------
    new_m : float
        Value of the global efficiency if the edge chosen is removed from G.
    choice : tuple
        Edge chosen that optimizes the global efficiency if removed,
        defined as the 2 nodes' ID (u,v).

    """
    batch_m = [] # List of metric value after an edge have been removed
    batch_choice = [] # List of corresponding edge removed
    iem = np.divide(np.ones(em.shape), em,
                    out=np.zeros_like(np.ones(em.shape)), where=em!=0)
    if keep_connected is True:
        for edge in edgelist:
            H = G.copy()
            H.remove_edge(*edge)
            if _is_disconnected(H, elected_nodes) is True:
                pass
            else:
                new_em = iem.copy()
                new_sm = metrics.get_shortest_network_path_matrix(H)
                # Need to inverse values but avoiding division by 0
                # Inverted 0 gives 0 here
                new_sm = np.divide(
                    np.ones(new_sm.shape), new_sm,
                    out=np.zeros_like(np.ones(new_sm.shape)),
                    where=new_sm!=0)
                # Avoid again division by 0, see metrics.avoid_zerodiv_matrix
                new_em[new_sm == 0.] = 0.
                nge = np.sum(new_sm) / np.sum(new_em)
                batch_m.append(nge)
                batch_choice.append(edge)
    else:
        for edge in edgelist:
            H = G.copy()
            H.remove_edge(*edge)
            new_em = iem.copy()
            new_sm = metrics.get_shortest_network_path_matrix(H)
            new_sm = np.divide( # See above
                np.ones(new_sm.shape), new_sm,
                out=np.zeros_like(np.ones(new_sm.shape)),
                where=new_sm!=0)
            new_em[new_sm == 0.] = 0. # See above
            nge = np.sum(new_sm) / np.sum(new_em)
            batch_m.append(nge)
            batch_choice.append(edge)
    try:
        new_m, choice = max(zip(batch_m, batch_choice))
    except:
        new_m = max(batch_m)
        index_max = max(range(len(batch_m)), key=batch_m.__getitem__)
        choice = batch_choice[index_max]
    return new_m, choice


def coverage_subtractive_step(
        G, edgelist, geom, elected_nodes, keep_connected = False):
    """
    Find the edge to remove on the graph G that optimizes the coverage, 
    and that doesn't create an additional component if keep_connected is
    True. The coverage is defined here as the area of the buffered edges.
    The buffer size is determined before, as buffered geometries are 
    kept in the geom dict.

    Parameters
    ----------
    G : networkx.classes.graph.Graph
        Graph on which we want to remove an edge.
    edgelist : list
        List of the edges that we can remove.
    geom : dict
        Dictionary with edges of G as keys and the corresponding
        buffered geometry as values.
    keep_connected : bool, optional
        If True, edges that can be removed are not creating a new 
        component. The default is False.
    elected_nodes : None or list
        If None, we don't have at the same time a built part with the
        connectedness constraint. Else, the elected nodes are one
        node of each built components, that we use to test if the
        network is connected or not.

    Returns
    -------
    new_m : float
        Value of the coverage if the edge chosen is removed from G.
    choice : tuple
        Edge chosen that optimizes the coverage if removed,
        defined as the 2 nodes' ID (u,v).

    """
    batch_m = [] # List of metric value after an edge have been removed
    batch_choice = [] # List of corresponding edge removed
    if keep_connected is True:
        for edge in edgelist:
            H = G.copy()
            H.remove_edge(*edge)
            if _is_disconnected(H, elected_nodes) is True:
                pass
            else:
                temp_g = geom.copy()
                temp_g.pop(edge)
                # We find the area by taking every values of the dict,
                # use shapely.ops.unary_union to merge every geometry
                # into one, then find the area of that geometry
                batch_m.append(shapely.ops.unary_union(
                    list(temp_g.values())).area)
                batch_choice.append(edge)
    else:
        for edge in edgelist:
            H = G.copy()
            H.remove_edge(*edge)
            temp_g = geom.copy()
            temp_g.pop(edge)
            batch_m.append(shapely.ops.unary_union( # See above
                list(temp_g.values())).area)
            batch_choice.append(edge)
    try:
        new_m, choice = max(zip(batch_m, batch_choice))
    except:
        new_m = max(batch_m)
        index_max = max(range(len(batch_m)), key=batch_m.__getitem__)
        choice = batch_choice[index_max]
    return new_m, choice


def relative_coverage_subtractive_step(
        G, edgelist, bef_area, geom, elected_nodes, keep_connected = False):
    """
    Find the edge to remove on the graph G that optimizes the relative
    coverage, and that doesn't create an additional component if
    keep_connected is True. The relative coverage is defined here as the
    difference in the area before and after removing the edge, divided by
    the length of the removed edge. The buffer size is determined before,
    as buffered geometries are kept in the geom dict.

    Parameters
    ----------
    G : networkx.classes.graph.Graph
        Graph on which we want to remove an edge.
    edgelist : list
        List of the edges that we can remove.
    bef_area : float
        Area of the buffered edges of G.
    geom : dict
        Dictionary with edges of G as keys and the corresponding
        buffered geometry as values.
    keep_connected : bool, optional
        If True, edges that can be removed are not creating a new 
        component. The default is False.
    elected_nodes : None or list
        If None, we don't have at the same time a built part with the
        connectedness constraint. Else, the elected nodes are one
        node of each built components, that we use to test if the
        network is connected or not.

    Returns
    -------
    new_m : float
        Value of the coverage if the edge chosen is removed from G.
    choice : tuple
        Edge chosen that optimizes the coverage if removed,
        defined as the 2 nodes' ID (u,v).

    """
    batch_m = [] # List of metric value after an edge have been removed
    batch_choice = [] # List of corresponding edge removed
    if keep_connected is True:
        for edge in edgelist:
            H = G.copy()
            H.remove_edge(*edge)
            if _is_disconnected(H, elected_nodes) is True:
                pass
            else:
                temp_g = geom.copy()
                temp_g.pop(edge)
                # See coverage_subtractive_step comment on this
                area = shapely.ops.unary_union(list(temp_g.values())).area
                # We find the relative coverage by comparing the actual area
                # to the area before removing an edge, divided by the length
                # of the edge removed
                batch_m.append((bef_area - area) 
                               / G.edges[edge]['length'])
                batch_choice.append(edge)
    else:
        for edge in edgelist:
            H = G.copy()
            H.remove_edge(*edge)
            temp_g = geom.copy()
            temp_g.pop(edge)
            area = shapely.ops.unary_union( # See above
                list(temp_g.values())).area
            batch_m.append((bef_area - area) # See above
                           / G.edges[edge]['length'])
            batch_choice.append(edge)
    try:
        new_m, choice = max(zip(batch_m, batch_choice))
    except:
        new_m = max(batch_m)
        index_max = max(range(len(batch_m)), key=batch_m.__getitem__)
        choice = batch_choice[index_max]
    return new_m, choice


# TODO: Add relative_directness
def optimize_additive_growth(
        G, folder_name, metric_optimized, local_proj, buff_size = 500,
        override_naming = False, built = True,
        keep_connected = True, profiling = True, 
        save_network = True, save_metrics = True):
    """
    Optimize the additive growth of a network G based on a metric that
    we want to optimize.

    Parameters
    ----------
    G : networkx.classes.graph.Graph
        Final network.
    folder_name : str
        Name of the folder. If override_naming is True, then full name
        of the folder, otherwise standardized suffixe are added based on
        the options of the functions.
    metric_optimized : str
        Name of the metric optimized. Can be directness and 
        relative_coverage.
    local_proj : str
        Projected crs of the graph. If None, tries to find it based on the
        latitude and longitude position of a node in the graph.
    buff_size : float, optional
        Size of the buffer used to measure the coverage.
        The default is 500.
    override_naming : bool, optional
        If True, then the folder_name is the full name and nothing is
        added. The default is False.
    built : bool, optional
        If True, make a difference between the built part of the network
        and the planned part. The default is True.
    keep_connected : bool, optional
        If True, the number of components of the graph can never exceed 1
        if there is not a built network, or the number of components
        of the built network. The default is True.
    profiling : bool, optional
        If True, make a profile of the time spent by the function on 
        various functions. The default is True.
    save_network : bool, optional
        If True, save G as final_network.gpickle in the result's folder.
        The default is True.
    save_metrics : bool, optional
        If True, save the metrics coverage and directness as arrays
        in the result's folder, under the name
        arrcov.pickle and arrdir.pickle.
        The default is True.

    Raises
    ------
    ValueError
        Raised if the value of the input metric_optimized is not a 
        possible value. metric_optimized can be directness and 
        relative_coverage.

    Returns
    -------
    folder_name : str
        Final name of the folder where the results are stored. If 
        override_naming is true, same as the input folder_name.


    """
    if metric_optimized not in ['directness', 'relative_coverage', 'coverage']:
        raise ValueError("""
                         Wrong value for metric_optimized, see
                         documentation for valid metric name.
                         """)
    if profiling is True:
        pr = cProfile.Profile()
        pr.enable()
    # If override_naming is False, then create a standardized name
    # based on the options used for the optimization
    if override_naming is False:
        if built is True:
            folder_name += "_built"
        if keep_connected is True:
            folder_name += "_connected"
        folder_name += f"_additive_bf{buff_size}_{metric_optimized}"
    # Make a new folder with the name where every results will be stored
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    if save_network is True:
        nx.write_gpickle(G, folder_name + "/final_network.gpickle")
    G = G.copy() # Create a copy to not mutate input
    if built is True:
        actual_edges = [edge for edge in G.edges 
                        if G.edges[edge]['built'] == 1]
        edgelist = [edge for edge in G.edges 
                    if G.edges[edge]['built'] == 0]
    else:
        actual_edges = []
        edgelist = [edge for edge in G.edges]
    c_hist = []
    # Coverage
    geom = dict()
    project = pyproj.Transformer.from_proj(
            pyproj.Proj(init=pyproj.CRS('epsg:4326')),
            pyproj.Proj(init=pyproj.CRS(local_proj)))
    for edge in actual_edges:
        geom[edge] = shapely.ops.transform(
            project.transform, G.edges[edge]['geometry']).buffer(buff_size)
    if built is True:
        bef_area = shapely.ops.unary_union(list(geom.values())).area
        cov_hist = [bef_area]
        # Directness
        dm = metrics.get_directness_matrix_networkx(
            G.edge_subgraph(actual_edges))
        dir_hist = [metrics.directness_from_matrix(dm)]
    else:
        # For now, build longest edge first
        # TODO: Build first based on metric optimized ? 
        max_len_edge = max(
            [[G.edges[edge]['length'], edge] for edge in G.edges])
        actual_edges.append(tuple(max_len_edge[1]))
        edgelist.remove(max_len_edge[1])
        c_hist.append(max_len_edge[1])
        geom[max_len_edge[1]] = shapely.ops.transform(
            project.transform,
            G.edges[max_len_edge[1]]['geometry']).buffer(buff_size)
        cov_hist = [shapely.ops.transform(
            project.transform,
            G.edges[max_len_edge[1]]['geometry']).buffer(buff_size).area]
        dm = metrics.get_directness_matrix_networkx(
            G.edge_subgraph(actual_edges))
        dir_hist = [metrics.directness_from_matrix(dm)]
    if metric_optimized == 'directness':
        for i in tqdm.tqdm(range(len(edgelist))):
            new_m, choice = directness_additive_step(
                G, actual_edges, edgelist,
                keep_connected=keep_connected)
            actual_edges, edgelist, geom, c_hist, cov_hist, dir_hist = (
                _make_additive_changes(
                    G, choice, buff_size, project, actual_edges, edgelist,
                    geom, c_hist, cov_hist, dir_hist))
    elif metric_optimized == 'relative_coverage':
        for i in tqdm.tqdm(range(len(edgelist))):
            new_m, choice = relative_coverage_additive_step(
                G, buff_size, project, actual_edges, edgelist,
                cov_hist[-1], geom, keep_connected=keep_connected)
            actual_edges, edgelist, geom, c_hist, cov_hist, dir_hist = (
                _make_additive_changes(
                    G, choice, buff_size, project, actual_edges, edgelist,
                    geom, c_hist, cov_hist, dir_hist))
    elif metric_optimized == 'coverage':
        for i in tqdm.tqdm(range(len(edgelist))):
            new_m, choice = coverage_additive_step(
                G, buff_size, project, actual_edges, edgelist,
                cov_hist[-1], geom, keep_connected=keep_connected)
            actual_edges, edgelist, geom, c_hist, cov_hist, dir_hist = (
                _make_additive_changes(
                    G, choice, buff_size, project, actual_edges, edgelist,
                    geom, c_hist, cov_hist, dir_hist))
    if save_metrics is True:
        with open(folder_name + "/arrdir.pickle", "wb") as fp:
            pickle.dump(dir_hist, fp)
        with open(folder_name + "/arrcov.pickle", "wb") as fp:
            pickle.dump(cov_hist, fp)
    with open(folder_name + "/arrchoice.pickle", "wb") as fp:
        pickle.dump(c_hist, fp)
    if profiling is True:
        pr.disable()
        s = io.StringIO() # get results of profiler in a text file
        ps = pstats.Stats(pr, stream=s).sort_stats('tottime')
        ps.print_stats()
    
        with open(folder_name + '/profile.txt', 'w+') as f:
            f.write(s.getvalue())
    return folder_name

def _make_additive_changes(
        G, choice, buff_size, project, actual_edges, edgelist,
        geom, c_hist, cov_hist, dir_hist):
    """
    Append values to their history list, modify arrays and graph based
    on edge and nodes added for the optimize_additive_growth 
    function at every step.

    Parameters
    ----------
     G : networkx.classes.graph.Graph
         Network on which we do our analysis.
     choice : list
         Edge that we removed defined by the node that are connected,
         as (u, v), u and v being the nodes' ID connected by the edge.
    buff_size : float
        Size of the buffer used to measure the coverage.
    project : pyproj.transformer.Transformer
        Tranformer modifying the geographic crs to the
        local projected crs of the graph.
    actual_edges : list
        List of the edges already grown either built and planned.
    edgelist : list
        List of all the edges considered to be removed of G. Edges are
        defined like choice.
    geom : dict
        Dictionary of the buffered geometry of the edges of G, see
        optimize_additive_growth.
    c_hist : list
        History of the edges removed.
    dir_hist : list
        History of the directness value, defined as the mean of the sum
        of the ratio of euclidian and shortest network path distance 
        between every pairs of nodes in the same component.
    cov_hist : list
        History of the coverage value, defined as the area of the union
        of all the buffered geometry of the edges of G.

    """
    c_hist.append(choice)
    actual_edges.append(tuple(choice))
    edgelist.remove(choice)
    # Coverage
    geom[choice] = shapely.ops.transform(
        project.transform, G.edges[choice]['geometry']).buffer(buff_size)
    bef_area = shapely.ops.unary_union(list(geom.values())).area
    cov_hist.append(bef_area)
    # Directness
    dir_hist.append(metrics.directness_from_matrix(
        metrics.get_directness_matrix_networkx(
            G.edge_subgraph(actual_edges))))
    return actual_edges, edgelist, geom, c_hist, cov_hist, dir_hist


def directness_additive_step(
        G, actual_edges, edgelist, keep_connected = False):
    """
    Find the edge to add to the actual_edges list from the final graph G
    that optimizes the directness, and that doesn't create an additional
    component if keep_connected is True. The directness is defined here as
    the linkwise directness which is the sum of the ratio of the euclidean
    distance and the shortest network distance between every pairs of nodes
    that are on the same component.

    For now, not using an already measured euclidean matrix, the gain
    is quite small in time and for addition instead of substraction that 
    would be a bit harder to do, better to redo everything again

    Parameters
    ----------
    G : networkx.classes.graph.Graph
        Final graph.
    actual_edges : list
        List of the edges that are already created from G.
    edgelist : list
        List of the edges that we can add from G to actual_edges
    keep_connected : bool, optional
        If True, edges that can be added are not creating a new 
        component. The default is False.

    Returns
    -------
    new_m : float
        Value of the directness if the edge chosen is added to actual_edges.
    choice : tuple
        Edge chosen that optimizes the directness if added,
        defined as the 2 nodes' ID (u,v).
    """
    batch_m = []
    batch_choice = []
    if keep_connected is True:
        for edge in edgelist:
            temp_edges = actual_edges.copy()
            temp_edges.append(edge)
            # Make subgraph of the actual_edges + the edge that we try to add
            H = G.edge_subgraph(temp_edges).copy()
            # See directness_subtractive_step comment on this
            if (nx.number_connected_components(H)
                > nx.number_connected_components(
                    G.edge_subgraph(actual_edges))) and (
                    len(sorted(nx.connected_components(H), key=len)[0]) > 1):
                pass
            else:
                dm = metrics.get_directness_matrix_networkx(H)
                batch_m.append(metrics.directness_from_matrix(dm))
                batch_choice.append(edge)
    else:
        for edge in edgelist:
            temp_edges = actual_edges.copy()
            temp_edges.append(edge)
            H = G.edge_subgraph(actual_edges).copy() # See above
            dm = metrics.get_directness_matrix_networkx(H)
            batch_m.append(metrics.directness_from_matrix(dm))
            batch_choice.append(edge)
    try:
        new_m, choice = max(zip(batch_m, batch_choice))
    except:
        new_m = max(batch_m)
        index_max = max(range(len(batch_m)), key=batch_m.__getitem__)
        choice = batch_choice[index_max]
    return new_m, choice


# TODO, adapt final_sm to the nodes of actual_sm only, use pandas filtering ?
def relative_directness_additive_step(
        G, actual_edges, edgelist, keep_connected = False):
    batch_m = []
    batch_choice = []
    if keep_connected is True:
        for edge in edgelist:
            temp_edges = actual_edges.copy()
            temp_edges.append(edge)
            H = G.edge_subgraph(temp_edges).copy()
            # See directness_subtractive_step comment on this
            if (nx.number_connected_components(H)
                > nx.number_connected_components(
                    G.edge_subgraph(actual_edges))) and (
                    len(sorted(nx.connected_components(H), key=len)[0]) > 1):
                pass
            else:
                final_sm = metrics.get_shortest_network_path_matrix(G)
                actual_sm = metrics.get_shortest_network_path_matrix(H)
                dm = metrics.avoid_zerodiv_matrix(final_sm, actual_sm)
                batch_m.append(metrics.directness_from_matrix(dm))
                batch_choice.append(edge)
    else:
        for edge in edgelist:
            temp_edges = actual_edges.copy()
            temp_edges.append(edge)
            H = G.edge_subgraph(actual_edges).copy()
            final_sm = metrics.get_shortest_network_path_matrix(G)
            actual_sm = metrics.get_shortest_network_path_matrix(H)
            dm = metrics.avoid_zerodiv_matrix(final_sm, actual_sm)
            batch_m.append(metrics.directness_from_matrix(dm))
            batch_choice.append(edge)
    batch = zip(batch_m, batch_choice)
    new_m, choice = max(batch)
    return new_m, choice


def relative_coverage_additive_step(
        G, buff_size, project, actual_edges, edgelist,
        bef_area, geom, keep_connected = False):
    """
    Find the edge to add to the actual_edges list from the final graph G
    that optimizes the relative coverage, and that doesn't create an
    additional component if keep_connected is True. The relative coverage
    is defined here as the difference in the area before and after adding
    the edge, divided by the length of the added edge. The buffer size
    is determined by the BUFF_SIZE constant.

    Parameters
    ----------
    G : networkx.classes.graph.Graph
        Graph on which we want to remove an edge.
    buff_size : float
        Constant that determines the buffer that we apply on the edge's
        geometry. For good results, the BUFFER_SIZE need to be the same
        that the one used for other values from the geom dict.
    project : pyproj.transformer.Transformer
        Tranformer modifying the geographic crs to the
        local projected crs of the graph.
    actual_edges : list
        List of the edges that are already created from G.
    edgelist : list
        List of the edges that we can add from G to actual_edges
    bef_area : float
        Area of the buffered edges of G.
    geom : dict
        Dictionary with edges of G as keys and the corresponding
        buffered geometry as values.
    keep_connected : bool, optional
        If True, edges that can be added are not creating a new 
        component. The default is False.

    Returns
    -------
    new_m : float
        Value of the relative coverage if the edge chosen is added
        to actual_edges.
    choice : tuple
        Edge chosen that optimizes the relative coverage if added,
        defined as the 2 nodes' ID (u,v).
    """
    batch_m = []
    batch_choice = []
    if keep_connected is True:
        for edge in edgelist:
            temp_edges = actual_edges.copy()
            temp_edges.append(edge)
            H = G.edge_subgraph(temp_edges).copy()
            # See directness_subtractive_step comment on this
            if (nx.number_connected_components(H)
                > nx.number_connected_components(
                    G.edge_subgraph(actual_edges))) and (
                    len(sorted(nx.connected_components(H), key=len)[0]) > 1):
                pass
            else:
                temp_g = geom.copy()
                temp_g[edge] = shapely.ops.transform(
                    project.transform,
                    G.edges[edge]['geometry']).buffer(buff_size)
                # See coverage_subtractive_step comment on this
                area = shapely.ops.unary_union(list(temp_g.values())).area
                # See relative_coverage_subtractive_step comment on this,
                # same principle but since we add and not remove, we take
                # the oppositve value
                batch_m.append((area - bef_area) / G.edges[edge]['length'])
                batch_choice.append(edge)
    else:
        for edge in edgelist:
            temp_g = geom.copy()
            temp_g[edge] = shapely.ops.transform(
                project.transform,
                G.edges[edge]['geometry']).buffer(buff_size)
            area = shapely.ops.unary_union(list(temp_g.values())).area
            batch_m.append((area - bef_area) / G.edges[edge]['length'])
            batch_choice.append(edge)
    # Need to try because sometimes the difference is so small that it 
    # can't find one so will look into the edge instead of the metric
    # to avoid this, we will find them individually
    # We also maximize and not minimize compared to 
    # relative_coverage_subtractive_step because here we want to grow as much
    # as possible and not shrink as less as possible
    try:
        new_m, choice = max(zip(batch_m, batch_choice))
    except:
        new_m = max(batch_m)
        index_max = max(range(len(batch_m)), key=batch_m.__getitem__)
        choice = batch_choice[index_max]
    return new_m, choice


def coverage_additive_step(
        G, buff_size, project, actual_edges, edgelist,
        bef_area, geom, keep_connected = False):
    """
    Find the edge to add to the actual_edges list from the final graph G
    that optimizes the coverage, and that doesn't create an
    additional component if keep_connected is True. The buffer size
    is determined by the BUFF_SIZE constant.

    Parameters
    ----------
    G : networkx.classes.graph.Graph
        Graph on which we want to remove an edge.
    buff_size : float
        Constant that determines the buffer that we apply on the edge's
        geometry. For good results, the BUFFER_SIZE need to be the same
        that the one used for other values from the geom dict.
    project : pyproj.transformer.Transformer
        Tranformer modifying the geographic crs to the
        local projected crs of the graph.
    actual_edges : list
        List of the edges that are already created from G.
    edgelist : list
        List of the edges that we can add from G to actual_edges
    bef_area : float
        Area of the buffered edges of G.
    geom : dict
        Dictionary with edges of G as keys and the corresponding
        buffered geometry as values.
    keep_connected : bool, optional
        If True, edges that can be added are not creating a new 
        component. The default is False.

    Returns
    -------
    new_m : float
        Value of the coverage if the edge chosen is added
        to actual_edges.
    choice : tuple
        Edge chosen that optimizes the relative coverage if added,
        defined as the 2 nodes' ID (u,v).
    """
    batch_m = []
    batch_choice = []
    if keep_connected is True:
        for edge in edgelist:
            temp_edges = actual_edges.copy()
            temp_edges.append(edge)
            H = G.edge_subgraph(temp_edges).copy()
            # See directness_subtractive_step comment on this
            if (nx.number_connected_components(H)
                > nx.number_connected_components(
                    G.edge_subgraph(actual_edges))) and (
                    len(sorted(nx.connected_components(H), key=len)[0]) > 1):
                pass
            else:
                temp_g = geom.copy()
                temp_g[edge] = shapely.ops.transform(
                    project.transform,
                    G.edges[edge]['geometry']).buffer(buff_size)
                # See coverage_subtractive_step comment on this
                batch_m.append(
                    shapely.ops.unary_union(list(temp_g.values())).area)
                batch_choice.append(edge)
    else:
        for edge in edgelist:
            temp_g = geom.copy()
            temp_g[edge] = shapely.ops.transform(
                project.transform,
                G.edges[edge]['geometry']).buffer(buff_size)
            batch_m.append(
                shapely.ops.unary_union(list(temp_g.values())).area)
            batch_choice.append(edge)
    # Need to try because sometimes the difference is so small that it 
    # can't find one so will look into the edge instead of the metric
    # to avoid this, we will find them individually
    # We also maximize and not minimize compared to 
    # relative_coverage_subtractive_step because here we want to grow as much
    # as possible and not shrink as less as possible
    try:
        new_m, choice = max(zip(batch_m, batch_choice))
    except:
        new_m = max(batch_m)
        index_max = max(range(len(batch_m)), key=batch_m.__getitem__)
        choice = batch_choice[index_max]
    return new_m, choice

# TODO : Adapt subtractive connected mulitple built part growth
def random_growth(
        G, folder_name, order, local_proj, buff_size = 500,
        override_naming = False, built = True,
        keep_connected = True, save_network = True, save_metrics = True):
    """
    Create the growth of a network G in a random manner, adding or 
    subtracting edges one by one randomly.

    Parameters
    ----------
    G : networkx.classes.graph.Graph
        Final network.
    folder_name : str
        Name of the folder. If override_naming is True, then full name
        of the folder, otherwise standardized suffixe are added based on
        the options of the functions.
    order : str
         Order of the random growth, can be either additive or subtractive.
    local_proj : str
        Projected crs of the graph. If None, tries to find it based on the
        latitude and longitude position of a node in the graph.
    buff_size : float, optional
        Size of the buffer used to measure the coverage.
        The default is 500.
    override_naming : bool, optional
        If True, then the folder_name is the full name and nothing is
        added. The default is False.
    built : bool, optional
        If True, make a difference between the built part of the network
        and the planned part. The default is True.
    keep_connected : bool, optional
        If True, the number of components of the graph can never exceed 1
        if there is not a built network, or the number of components
        of the built network. The default is True.
    save_network : bool, optional
        If True, save G as final_network.gpickle in the result's folder.
        The default is True.
    save_metrics : bool, optional
        If True, save the metrics coverage and directness as arrays
        in the result's folder, under the name
        arrcov.pickle and arrdir.pickle.
        The default is True.

    Raises
    ------
    ValueError
        Raised if the value of the input order is not a 
        possible value. order can be additive or subtractive.


    Returns
    -------
    folder_name : str
        Final name of the folder where the results are stored. If 
        override_naming is true, same as the input folder_name.

    """
    if order not in ['subtractive', 'additive']:
        raise ValueError("""
                         Value of the order is not valid, please put
                         either subtractive or additive.
                         """)
    if override_naming is False:
        if built is True:
            folder_name += "_built"
        if keep_connected is True:
            folder_name += "_connected"
        if order == 'subtractive':
            folder_name += f"_subtractive_bf{buff_size}_random"
        # Could just use else but allows to be clearer
        elif order == 'additive':
            folder_name += f"_additive_bf{buff_size}_random"
    # Make a new folder with the name where every results will be stored
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    if save_network is True:
        nx.write_gpickle(G, folder_name + "/final_network.gpickle")
    G = G.copy()
    c_hist = []
    dir_hist = []
    cov_hist = []
    # Coverage
    geom = dict()
    project = pyproj.Transformer.from_proj(
            pyproj.Proj(init=pyproj.CRS('epsg:4326')),
            pyproj.Proj(init=pyproj.CRS(local_proj)))
    if built is True:
        edgelist = [edge for edge in G.edges 
                    if G.edges[edge]['built'] == 0]
        if order == 'additive': # init for the subgraph
            actual_edges = [edge for edge in G.edges
                            if G.edges[edge]['built'] == 1]
            for edge in actual_edges:
                geom[edge] = shapely.ops.transform(
                    project.transform,
                    G.edges[edge]['geometry']).buffer(buff_size)
            cov_hist.append(shapely.ops.unary_union(
                list(geom.values())).area)
            dir_hist.append(metrics.directness_from_matrix(
                metrics.get_directness_matrix_networkx(
                    G.edge_subgraph(actual_edges))))
    else:
        edgelist = [edge for edge in G.edges]
        if order == 'additive': # init for the subgraph
            choice = random.choice(edgelist)
            actual_edges = [choice] # need to be non-empty, first random
            edgelist.remove(choice)
            geom[choice] = shapely.ops.transform(
                project.transform, G.edges[choice]['geometry']
                ).buffer(buff_size)
            c_hist.append(choice)
            cov_hist.append(shapely.ops.unary_union(
                list(geom.values())).area)
            dir_hist.append(metrics.directness_from_matrix(
                metrics.get_directness_matrix_networkx(
                    G.edge_subgraph(actual_edges))))
    if order == 'subtractive':
        for edge in G.edges:
            geom[edge] = shapely.ops.transform(
                project.transform, G.edges[edge]['geometry']).buffer(buff_size)
        cov_hist.append(shapely.ops.unary_union(
            list(geom.values())).area)
        dir_hist.append(metrics.directness_from_matrix(
            metrics.get_directness_matrix_networkx(G)))
    if built is True: # if something is built we can remove every other edges
        n_sub_iter = range(len(edgelist))
    else: # else we need to keep the last one
        n_sub_iter = range(len(edgelist) - 1)
    if keep_connected is True:
        if order == 'subtractive':
            if built is True:
                built_components = list(
                    nx.connected_components(
                        G.edge_subgraph(
                            [edge for edge in G.edges if
                             G.edges[edge]['built'] == 1])))
                elected_nodes = []
                for cc in built_components:
                    elected_nodes.append(list(G.subgraph(cc).nodes)[0])
            else:
                elected_nodes = None
            for i in tqdm.tqdm(n_sub_iter):
                edge_batch = []
                for edge in edgelist:
                    H = G.copy()
                    H.remove_edge(*edge)
                    if _is_disconnected(H, elected_nodes) is True:
                        pass
                    else:
                        edge_batch.append(edge)
                choice = random.choice(edge_batch) # random choice
                G.remove_edge(*choice)
                edgelist.remove(choice)
                G = utils.clean_isolated_node(G)
                c_hist.append(choice)
                geom.pop(choice)
                cov_hist.append(shapely.ops.unary_union(
                    list(geom.values())).area)
                dir_hist.append(metrics.directness_from_matrix(
                    metrics.get_directness_matrix_networkx(G)))
        elif order == 'additive':
            for i in tqdm.tqdm(range(len(edgelist))):
                edge_batch = []
                for edge in edgelist:
                    temp_edges = actual_edges.copy()
                    temp_edges.append(edge)
                    H = G.edge_subgraph(temp_edges).copy()
                    # See directness_subtractive_step comment on this
                    if (nx.number_connected_components(H)
                        > nx.number_connected_components(
                            G.edge_subgraph(actual_edges))) and (
                            len(sorted(
                                nx.connected_components(H), key=len)[0]) > 1):
                        pass
                    else:
                        edge_batch.append(edge)
                choice = random.choice(edge_batch) # random choice
                edgelist.remove(choice)
                actual_edges.append(choice)
                c_hist.append(choice)
                geom[choice] = shapely.ops.transform(
                    project.transform, G.edges[choice]['geometry']
                    ).buffer(buff_size)
                cov_hist.append(shapely.ops.unary_union(
                    list(geom.values())).area)
                dir_hist.append(metrics.directness_from_matrix(
                    metrics.get_directness_matrix_networkx(
                        G.edge_subgraph(actual_edges))))
    else:
        if order == 'subtractive':
            for i in tqdm.tqdm(n_sub_iter):
                choice = random.choice(edgelist) # random choice
                G.remove_edge(*choice)
                edgelist.remove(choice)
                G = utils.clean_isolated_node(G)
                c_hist.append(choice)
                geom.pop(choice)
                cov_hist.append(shapely.ops.unary_union(
                    list(geom.values())).area)
                dir_hist.append(metrics.directness_from_matrix(
                    metrics.get_directness_matrix_networkx(G)))
        elif order == 'additive':
            for i in tqdm.tqdm(range(len(edgelist))):
                choice = random.choice(edgelist) # random choice
                edgelist.remove(choice)
                actual_edges.append(choice)
                c_hist.append(choice)
                geom[choice] = shapely.ops.transform(
                    project.transform, G.edges[choice]['geometry']
                    ).buffer(buff_size)
                cov_hist.append(shapely.ops.unary_union(
                    list(geom.values())).area)
                dir_hist.append(metrics.directness_from_matrix(
                    metrics.get_directness_matrix_networkx(
                        G.edge_subgraph(actual_edges))))
    if save_metrics is True:
        with open(folder_name + "/arrdir.pickle", "wb") as fp:
            pickle.dump(dir_hist, fp)
        with open(folder_name + "/arrcov.pickle", "wb") as fp:
            pickle.dump(cov_hist, fp)
    with open(folder_name + "/arrchoice.pickle", "wb") as fp:
        pickle.dump(c_hist, fp)
    return folder_name


# TODO : Adapt subtractive connected mulitple built part growth
def betweenness_growth(
        G, folder_name, order, local_proj, buff_size = 500,
        override_naming = False, built = True,
        keep_connected = True, save_network = True, save_metrics = True):
    """
    Create the growth of a network G with the edges with the highest
    betweenness constructed first, in a subtractive or additive
    manner.

    Parameters
    ----------
    G : networkx.classes.graph.Graph
        Final network.
    folder_name : str
        Name of the folder. If override_naming is True, then full name
        of the folder, otherwise standardized suffixe are added based on
        the options of the functions.
    order : str
         Order of the betweenness growth,
         can be either additive or subtractive.
    local_proj : str
        Projected crs of the graph. If None, tries to find it based on the
        latitude and longitude position of a node in the graph.
    buff_size : float, optional
        Size of the buffer used to measure the coverage.
        The default is 500.
    override_naming : bool, optional
        If True, then the folder_name is the full name and nothing is
        added. The default is False.
    built : bool, optional
        If True, make a difference between the built part of the network
        and the planned part. The default is True.
    keep_connected : bool, optional
        If True, the number of components of the graph can never exceed 1
        if there is not a built network, or the number of components
        of the built network. The default is True.
    save_network : bool, optional
        If True, save G as final_network.gpickle in the result's folder.
        The default is True.
    save_metrics : bool, optional
        If True, save the metrics coverage and directness as arrays
        in the result's folder, under the name
        arrcov.pickle and arrdir.pickle.
        The default is True.

    Raises
    ------
    ValueError
        Raised if the value of the input order is not a 
        possible value. order can be additive or subtractive.


    Returns
    -------
    folder_name : str
        Final name of the folder where the results are stored. If 
        override_naming is true, same as the input folder_name.

    """
    if order not in ['subtractive', 'additive']:
        raise ValueError("""
                         Value of the order is not valid, please put
                         either subtractive or additive.
                         """)
    if override_naming is False:
        if built is True:
            folder_name += "_built"
        if keep_connected is True:
            folder_name += "_connected"
        if order == 'subtractive':
            folder_name += f"_subtractive_bf{buff_size}_betweenness"
        # Could just use else but allows to be clearer
        elif order == 'additive':
            folder_name += f"_additive_bf{buff_size}_betweenness"
    # Make a new folder with the name where every results will be stored
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    if save_network is True:
        nx.write_gpickle(G, folder_name + "/final_network.gpickle")
    G = G.copy()
    c_hist = []
    dir_hist = []
    cov_hist = []
    # Coverage
    geom = dict()
    project = pyproj.Transformer.from_proj(
            pyproj.Proj(init=pyproj.CRS('epsg:4326')),
            pyproj.Proj(init=pyproj.CRS(local_proj)))
    # Find ranking of edge betweenness
    edge_bet = nx.edge_betweenness_centrality(G, weight='length')
    sorted_edges = [k for k, v in sorted( # Sort edges by higher betweenness
        edge_bet.items(), key=lambda item: item[1])]
    if built is True:
        edgelist = [edge for edge in G.edges 
                    if G.edges[edge]['built'] == 0]
        edge_order = [edge for edge in sorted_edges if edge in edgelist]
        if order == 'additive': # init for the subgraph
            actual_edges = [edge for edge in G.edges
                            if G.edges[edge]['built'] == 1]
            for edge in actual_edges:
                geom[edge] = shapely.ops.transform(
                    project.transform,
                    G.edges[edge]['geometry']).buffer(buff_size)
            cov_hist.append(shapely.ops.unary_union(
                list(geom.values())).area)
            dir_hist.append(metrics.directness_from_matrix(
                metrics.get_directness_matrix_networkx(
                    G.edge_subgraph(actual_edges))))
    else:
        edgelist = [edge for edge in G.edges]
        edge_order = [edge for edge in sorted_edges if edge in edgelist]
        if order == 'additive': # init for the subgraph
            choice = edge_order[-1]
            actual_edges = [choice] # need to be non-empty, first random
            edge_order.remove(choice)
            geom[choice] = shapely.ops.transform(
                project.transform, G.edges[choice]['geometry']
                ).buffer(buff_size)
            c_hist.append(choice) # first choice for additive
            cov_hist.append(shapely.ops.unary_union(
                list(geom.values())).area)
            dir_hist.append(metrics.directness_from_matrix(
                metrics.get_directness_matrix_networkx(
                    G.edge_subgraph(actual_edges))))
    if order == 'subtractive':
        for edge in G.edges:
            geom[edge] = shapely.ops.transform(
                project.transform, G.edges[edge]['geometry']).buffer(buff_size)
        cov_hist.append(shapely.ops.unary_union(
            list(geom.values())).area)
        dir_hist.append(metrics.directness_from_matrix(
            metrics.get_directness_matrix_networkx(G)))
    else:
        edge_order.reverse()
    if built is True: # if something is built we can remove every other edges
        sub_n_last = 0
        sub_removed_edge = edge_order
    else: # else we need to keep the last one
        sub_n_last = 1
        sub_removed_edge = edge_order[:-1]
    if keep_connected is True:
        if order == 'subtractive':
            if built is True:
                built_components = list(
                    nx.connected_components(
                        G.edge_subgraph(
                            [edge for edge in G.edges if
                             G.edges[edge]['built'] == 1])))
                elected_nodes = []
                for cc in built_components:
                    elected_nodes.append(list(G.subgraph(cc).nodes)[0])
            else:
                elected_nodes = None
            while len(edge_order) > sub_n_last:
                edge = None
                count = 0
                while edge is None:
                    tested_edge = edge_order[count]
                    H = G.copy()
                    H.remove_edge(*tested_edge)
                    if _is_disconnected(H, elected_nodes) is True:
                        count += 1
                    else:
                        edge = tested_edge
                edge_order.remove(edge)
                G.remove_edge(*edge)
                G = utils.clean_isolated_node(G)
                c_hist.append(edge)
                geom.pop(edge)
                cov_hist.append(shapely.ops.unary_union(
                    list(geom.values())).area)
                dir_hist.append(metrics.directness_from_matrix(
                    metrics.get_directness_matrix_networkx(G)))
        elif order == 'additive':
            while len(edge_order) > 0:
                edge = None
                count = 0
                while edge is None:
                    tested_edge = edge_order[count]
                    temp_edges = actual_edges.copy()
                    temp_edges.append(tested_edge)
                    H = G.edge_subgraph(temp_edges).copy()
                    # See directness_subtractive_step comment on this
                    if (nx.number_connected_components(H)
                        > nx.number_connected_components(
                            G.edge_subgraph(actual_edges))) and (
                            len(sorted(
                                nx.connected_components(H), key=len)[0]) > 1):
                        count += 1
                    else:
                        edge = tested_edge
                edge_order.remove(edge)
                actual_edges.append(edge)
                c_hist.append(edge)
                geom[edge] = shapely.ops.transform(
                    project.transform, G.edges[edge]['geometry']
                    ).buffer(buff_size)
                cov_hist.append(shapely.ops.unary_union(
                    list(geom.values())).area)
                dir_hist.append(metrics.directness_from_matrix(
                    metrics.get_directness_matrix_networkx(
                        G.edge_subgraph(actual_edges))))
    else:
        if order == 'subtractive':
            for edge in tqdm.tqdm(sub_removed_edge):
                G.remove_edge(*edge)
                G = utils.clean_isolated_node(G)
                c_hist.append(edge)
                geom.pop(edge)
                cov_hist.append(shapely.ops.unary_union(
                    list(geom.values())).area)
                dir_hist.append(metrics.directness_from_matrix(
                    metrics.get_directness_matrix_networkx(G)))
        elif order == 'additive':
            for edge in tqdm.tqdm(edge_order):
                actual_edges.append(edge)
                c_hist.append(edge)
                geom[edge] = shapely.ops.transform(
                    project.transform, G.edges[edge]['geometry']
                    ).buffer(buff_size)
                cov_hist.append(shapely.ops.unary_union(
                    list(geom.values())).area)
                dir_hist.append(metrics.directness_from_matrix(
                    metrics.get_directness_matrix_networkx(
                        G.edge_subgraph(actual_edges))))
    if save_metrics is True:
        with open(folder_name + "/arrdir.pickle", "wb") as fp:
            pickle.dump(dir_hist, fp)
        with open(folder_name + "/arrcov.pickle", "wb") as fp:
            pickle.dump(cov_hist, fp)
    with open(folder_name + "/arrchoice.pickle", "wb") as fp:
        pickle.dump(c_hist, fp)
    return folder_name

