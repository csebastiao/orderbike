# -*- coding: utf-8 -*-
"""
Functions to make subtractive or additive growth of a graph.
"""

import tqdm

import networkx as nx
import numpy as np
import shapely

from . import metrics
from .utils import log


def order_ranked_network_growth(
    G,
    built=True,
    keep_connected=True,
    order="subtractive",
    ranking_func=metrics.growth_random,
    save_metrics=True,
    buff_size_metrics=200,
    **kwargs,
):
    """
    Find the order of growth for a network based on the ranking given by a function. Since the ranking is independent of the state of the network at a specific stage, it is much faster to compute than order_dynamic_network_growth.

    Args:
        G (networkx.Graph): Final graph. The initial graph from where we grow is based on the built attribute.
        built (bool, optional): If True, the graph will be initialized with all edges having as an attribute "built" = 1. Else it will be initialized with an arbitrary edge of the node with the highest closeness value. Defaults to True.
        keep_connected (bool, optional): If True, the number of components of G will be as small as possible for all the growth, restricting the list of edges that can be added. Defaults to True.
        order (str, optional): Either subtractive or additive. Gives the order for the greedy optimization. The subtractive (resp. additive) start from the final (resp. initial) graph and remove (resp. add) edges until reaching the initial graph (resp. final). Defaults to "subtractive".
        ranking_func (function, optional): The function computing the ranking on G, in descending order. Defaults to metrics.growth_random.
        save_metrics (bool, optional): If True, compute all the metrics on the graph for the growth and return it as a dictionary. Defaults to True.
        buff_size_metrics (int, optional): Size of the buffer in the computation of the metric for the growth. Defaults to 200.

    Returns:
        list: Ordered list of edges. For subtractive (resp. additive) order, the first edge in the list is the last (resp. first) to add. If built is True, will only have edges with "built" != 1. Else, will have all edges of G except the seed.
    """
    init_edges = _init_edges(G, built, order)
    absolute_ranking = ranking_func(G, **kwargs)
    # If keeping connected need to choose for the order the one with the highest/smallest ranking to add/remove
    if keep_connected:
        order_growth = []
        G_actual = _init_graph(G, order, init_edges)
        num_step = len(G.edges) - len(init_edges)
        for i in range(num_step):
            valid_edges = _valid_edges(
                G, G_actual, init_edges, built, keep_connected, order
            )
            log.debug(f"Step {i}: {len(valid_edges)} valid edges to choose from.")
            testing_ranking = absolute_ranking.copy()
            # In subtractive order, choose the edge with the lowest ranking, in additive the highest
            if order == "subtractive":
                testing_ranking.reverse()
            if ranking_func == metrics.growth_random:
                for edge in testing_ranking:
                    if edge in valid_edges:
                        step = edge
                        absolute_ranking.remove(step)
                        break
            else:
                valid_cases = [
                    [edge, met]
                    for edge, met in testing_ranking
                    if edge
                    in _valid_edges(
                        G, G_actual, init_edges, built, keep_connected, order
                    )
                ]
                valid_edges = [val[0] for val in valid_cases]
                valid_mets = [val[1] for val in valid_cases]
                step = _find_optimal_edge(valid_mets, valid_edges)
                step_met = valid_mets[
                    [idx for idx, i in enumerate(valid_edges) if i == step][0]
                ]
                absolute_ranking.remove([step, step_met])
            log.debug(f"Step {i}: optimal edge chosen is {step}.")
            G_actual = _update_actual_graph(G, G_actual, step, order)
            order_growth.append(step)
        if order == "subtractive":
            order_growth.reverse()
    else:
        if ranking_func == metrics.growth_random:
            order_growth = [step for step in absolute_ranking if step not in init_edges]
        else:
            order_growth = [
                step for met, step in absolute_ranking if step not in init_edges
            ]
        # Since in subtractive order without a built part we don't initialize edges, we need to remove the first edge of the ranking
        if order == "subtractive" and built is False:
            order_growth = order_growth[1:]
    if save_metrics:
        metrics_dict = compute_metrics(
            G, order_growth, built=built, x_meter=True, buff_size=buff_size_metrics
        )
        return metrics_dict, order_growth
    return order_growth


def order_dynamic_network_growth(
    G,
    built=True,
    keep_connected=True,
    order="subtractive",
    metric="coverage",
    metric_func=None,
    precomp_func=None,
    update_func=None,
    progress_bar=True,
    save_metrics=True,
    buff_size_metrics=200,
    **kwargs,
):
    """
    Find the optimal order of growth for a network based on the greedy optimization of a metric.

    Args:
        G (networkx.Graph): Final graph. The initial graph from where we grow is based on the built attribute.
        built (bool, optional): If True, the graph will be initialized with all edges having as an attribute "built" = 1. Else it will be initialized with an arbitrary edge of the node with the highest closeness value. Defaults to True.
        keep_connected (bool, optional): If True, the number of components of G will be as small as possible for all the growth, restricting the list of edges that can be added. Defaults to True.
        order (str, optional): Either subtractive or additive. Gives the order for the greedy optimization. The subtractive (resp. additive) start from the final (resp. initial) graph and remove (resp. add) edges until reaching the initial graph (resp. final). Defaults to "subtractive".
        metric (str, optional): The name of the metric used, automatically fill metric_func, precomp_func, and update_func. See _metric_dictionaries.
        metric_func (function, optional): The function computing the metric on G. Defaults to None.
        precomp_func (function, optional): A sister function to metric_func to compute values before the growth steps. Defaults to None.
        update_func (function, optional): A sister function to metric_func to update values at each steps. Defaults to None.
        save_metrics (bool, optional): If True, compute all the metrics on the graph for the growth and return it as a dictionary. Defaults to True.
        buff_size_metrics (int, optional): Size of the buffer in the computation of the metric for the growth. Defaults to 200.

    Returns:
        list: Ordered list of edges. For subtractive (resp. additive) order, the first edge in the list is the last (resp. first) to add. If built is True, will only have edges with "built" != 1. Else, will have all edges of G except the seed.
    """
    if metric is not None:
        metric_dict = _metric_dictionaries()[metric]
        metric_func = metric_dict["metric_func"]
        precomp_func = metric_dict["precomp_func"]
        update_func = metric_dict["update_func"]
    else:
        if metric_func is None:
            raise ValueError(
                "Plaise enter either a metric name or functions to compute growth"
            )
    order_growth = []
    init_edges = _init_edges(G, built, order)
    G_actual = _init_graph(G, order, init_edges)
    num_step = len(G.edges) - len(init_edges)
    total_step = range(num_step)
    if progress_bar:
        total_step = tqdm.tqdm(total_step)
    if precomp_func is not None:
        precomp_kwargs = precomp_func(G_actual, G, order, **kwargs)
    else:
        precomp_kwargs = kwargs
    for i in total_step:
        valid_edges = _valid_edges(
            G, G_actual, init_edges, built, keep_connected, order
        )
        log.debug(f"Step {i}: {len(valid_edges)} valid edges to choose from.")
        metric_vals = []
        # Remove/add an edge to the actual graph and compute the metric on it
        for edge in valid_edges:
            H = _update_tested_graph(G_actual, G, edge, order)
            temp_m = metric_func(H, edge, **precomp_kwargs)
            metric_vals.append(temp_m)
        # Choose the edge that gives the maximum value for the metric
        step = _find_optimal_edge(metric_vals, valid_edges)
        log.debug(f"Step {i}: optimal edge chosen is {step}.")
        G_actual = _update_actual_graph(G, G_actual, step, order)
        order_growth.append(step)
        if update_func is not None:
            precomp_kwargs = update_func(G, G_actual, step, **precomp_kwargs)
    if order == "subtractive":
        order_growth.reverse()
    if save_metrics:
        metrics_dict = compute_metrics(
            G, order_growth, built=built, x_meter=True, buff_size=buff_size_metrics
        )
        return metrics_dict, order_growth
    return order_growth


def _find_optimal_edge(vals, edges):
    """Get the edge with the maximal value, if there are multiple ones with maximal value pick one of them at random."""
    m = max(vals)
    log.debug(f"The maximum value is {m}, the minimum value is {min(vals)}")
    optimum = [edge for edge, val in zip(edges, vals) if val == m]
    # When more than one optimal value, return a random value from all the optimal ones
    if len(optimum) > 1:
        log.debug(f"{len(optimum)} steps are optimal, choosing one randomly")
        rng = np.random.default_rng()
        # Need to change to list with built-in function to avoid numpy int type for values, and then to tuple for the list
        return tuple(rng.choice(optimum).tolist())
    return optimum[0]


def _metric_dictionaries():
    metrics_dict = {}
    metrics_dict["relative_directness"] = {
        "metric_func": metrics.growth_relative_directness,
        "precomp_func": metrics.prefunc_growth_relative_directness,
        "update_func": None,
    }
    metrics_dict["directness"] = {
        "metric_func": metrics.directness,
        "precomp_func": None,
        "update_func": None,
    }
    metrics_dict["coverage"] = {
        "metric_func": metrics.growth_coverage,
        "precomp_func": metrics.prefunc_growth_coverage,
        "update_func": metrics.upfunc_growth_coverage,
    }
    metrics_dict["adaptive_coverage"] = {
        "metric_func": metrics.growth_coverage,
        "precomp_func": metrics.prefunc_growth_adaptive_coverage,
        "update_func": metrics.upfunc_growth_adaptive_coverage,
    }
    return metrics_dict


def compute_metrics(G, order_growth, built=False, x_meter=True, buff_size=200):
    """
    Compute all relevant metrics for the growth of a graph

    Args:
        G (networkx.Graph): Final graph. The initial graph from where we grow is based on the built attribute.
        order_growth (list): List of ordered edges as tuple to add to the inital graph to go to the final graph G.
        built (bool, optional): If True, the graph will be initialized with all edges having as an attribute "built" = 1. Else it will be initialized with an arbitrary edge of the node with the highest closeness value. Defaults to True.
        x_meter (bool, optional): To add the total length at each step as a metric. Defaults to True.
        buff_size (int, optional): Size of the buffer used to compute the coverage. Defaults to 200.

    Returns:
        dict: Dictionary with name of the metric as keys and values in order of growth as values.
    """
    if built:
        G_actual = G.edge_subgraph(
            [edge for edge in G.edges if G.edges[edge]["built"] == 1]
        )
    else:
        # Edges need to be tuple in order growth in order to work !!!
        for edge in G.edges:
            if edge not in order_growth:
                if len(edge) == 3:
                    reverse = [edge[1], edge[0], edge[2]]
                else:
                    reverse = tuple(reversed(edge))
                if reverse not in order_growth:
                    G_actual = G.edge_subgraph([edge])
                    break
    actual_edges = [edge for edge in G_actual.edges]
    xx = []
    if x_meter:
        total_length = sum([G_actual.edges[edge]["length"] for edge in G_actual.edges])
        xx.append(total_length)
        for step in order_growth:
            total_length += G.edges[step]["length"]
            xx.append(total_length)
    else:
        xx = range(len(order_growth))
    geom = [G.edges[edge]["geometry"].buffer(buff_size) for edge in G_actual.edges]
    coverage = []
    directness = []
    relative_directness = []
    # Should add computation of global and local efficiency to compare with GrowBike
    num_cc = []
    length_lcc = []
    fsm = metrics.get_shortest_network_path_length_matrix(G)
    coverage.append(shapely.ops.unary_union(geom).area)
    directness.append(metrics.directness(G_actual, 1))
    ids_to_delete = [ids for ids, node in enumerate(G.nodes) if node not in G_actual]
    fsmt = np.delete(np.delete(fsm, ids_to_delete, 0), ids_to_delete, 1)
    mat = metrics._avoid_zerodiv_matrix(
        fsmt, metrics.get_shortest_network_path_length_matrix(G_actual)
    )
    relative_directness.append(np.sum(mat) / np.count_nonzero(mat))
    cc = list(nx.connected_components(G_actual))
    num_cc.append(len(cc))
    length_lcc.append(
        max(
            [
                sum(
                    [G_actual.edges[e]["length"] for e in G_actual.subgraph(comp).edges]
                )
                for comp in cc
            ]
        )
    )
    for edge in order_growth:
        actual_edges.append(edge)
        G_actual = G.edge_subgraph(actual_edges)
        geom.append(G.edges[edge]["geometry"].buffer(buff_size))
        coverage.append(shapely.ops.unary_union(geom).area)
        directness.append(metrics.directness(G_actual, 1))
        ids_to_delete = [
            ids for ids, node in enumerate(G.nodes) if node not in G_actual
        ]
        fsmt = np.delete(np.delete(fsm, ids_to_delete, 0), ids_to_delete, 1)
        mat = metrics._avoid_zerodiv_matrix(
            fsmt, metrics.get_shortest_network_path_length_matrix(G_actual)
        )
        relative_directness.append(np.sum(mat) / np.count_nonzero(mat))
        cc = list(nx.connected_components(G_actual))
        num_cc.append(len(cc))
        length_lcc.append(
            max(
                [
                    sum(
                        [
                            G_actual.edges[e]["length"]
                            for e in G_actual.subgraph(comp).edges
                        ]
                    )
                    for comp in cc
                ]
            )
        )
    metrics_dict = {}
    metrics_dict["xx"] = xx
    metrics_dict["coverage"] = coverage
    metrics_dict["directness"] = directness
    metrics_dict["relative_directness"] = relative_directness
    metrics_dict["num_cc"] = num_cc
    metrics_dict["length_lcc"] = length_lcc
    return metrics_dict


def _init_edges(G, built, order):
    """Return the initial edges for the first step of the growth of G."""
    if built:
        init_edges = [edge for edge in G.edges if G.edges[edge]["built"] == 1]
        return init_edges
    # If no built part, start from a seed being a random edge from the node with the highest closeness
    else:
        # If subtractive, don't care about finding an initial edge because will be found through optimization, dummy variable
        if order == "subtractive":
            return [0]
        # If additive, use as initial edge if none given the one with the highest average closeness of its nodes
        elif order == "additive":
            closeness = nx.closeness_centrality(G, distance="length")
            edge_closeness = {}
            for edge in G.edges:
                edge_closeness[edge] = (closeness[edge[0]] + closeness[edge[1]]) / 2
            return [tuple(max(edge_closeness, key=edge_closeness.get))]


def _init_graph(G, order, init_edges):
    """Return the initial graph for the growth depending on the order."""
    if order == "subtractive":
        return G.copy()
    elif order == "additive":
        return G.edge_subgraph(init_edges)


def _valid_edges(G, G_actual, init_edges, built, keep_connected, order):
    """Return the valid edges to add or remove for the next step of the growth of G from G_actual."""
    # If connectedness constraint remove invalid edges that would add unacceptable new component
    if keep_connected:
        if order == "subtractive":
            invalid_edges = get_subtractive_invalid_edges(G_actual, built=built)
            return [edge for edge in G_actual.edges if edge not in invalid_edges]
        elif order == "additive":
            invalid_edges = get_additive_invalid_edges(G_actual, G)
            return [edge for edge in G.edges if edge not in invalid_edges]
    else:
        if order == "subtractive":
            return [edge for edge in G_actual.edges if edge not in init_edges]
        elif order == "additive":
            return [edge for edge in G.edges if edge not in G_actual.edges]


def _update_tested_graph(G_actual, G, edge, order):
    """Update the tested graph by removing/adding the tested edge to the actual graph."""
    if order == "subtractive":
        H = G_actual.copy()
        H.remove_edge(*edge)
    elif order == "additive":
        temp_edges = list(G_actual.edges)
        temp_edges.append(edge)
        H = G.edge_subgraph(temp_edges)
    return H


def _update_actual_graph(G, G_actual, step, order):
    """Remove or add the chosen step to the actual graph."""
    if order == "subtractive":
        G_actual.remove_edge(*step)
        # Remove isolated node from the graph
        for n in step[:2]:
            if nx.degree(G_actual, n) == 0:
                G_actual.remove_node(n)
    elif order == "additive":
        actual_edges = list(G_actual.edges)
        actual_edges.append(step)
        G_actual = G.edge_subgraph(actual_edges)
    return G_actual


def get_subtractive_invalid_edges(G, built=True):
    """
    Find all invalid edges that if removed would create a new, unacceptable component to the graph. A new component is unacceptable if it's not a subgraph of a component that is part of the built graph but not of the actual graph.

    Args:
        G (networkx.Graph): Graph on which we want to remove edges.
        built (bool, optional): If True, there is a built component to the graph to take into account. This is represented by an edge attribute on all edges, that is 1 if it's built, 0 if it's not built. Defaults to True.

    Returns:
        list: List of tuple, each tuple being an invalid edge to remove from G.
    """
    # Find all bridges and remove bridges that when removed leave an isolated node
    invalid_edges = [
        edge
        for edge in nx.bridges(G)
        if not any(nx.degree(G, node) == 1 for node in edge)
    ]
    # If there are elected nodes there are built edges that we can't remove
    if built:
        built_edges = [edge for edge in G.edges if G.edges[edge]["built"] == 1]
        invalid_edges += built_edges
        invalid_edges = set(invalid_edges)
        elected_nodes = elect_nodes(G.edge_subgraph(built_edges))
    # If built is False work stops before checking elected_nodes, if built is True elected_nodes is created so it works
    if built is False or nx.number_connected_components(G) == len(elected_nodes):
        return invalid_edges
    # New component can be created only if part of a new component with a built part
    else:
        updated_invalid_edges = invalid_edges.copy()
        for edge in invalid_edges:
            if edge not in built_edges:
                H = G.copy()
                H.remove_edge(*edge)
                # Accept edges (remove from invalid edges) that if removed from the graph create a new component with a built part
                if not any(
                    not any(node in cc for node in elected_nodes)
                    for cc in list(nx.connected_components(H))
                ):
                    updated_invalid_edges.remove(edge)
        return updated_invalid_edges


def get_additive_invalid_edges(G_actual, G_final):
    """
    Find all invalid edges that if added would create a new, unacceptable component to the graph. A new component is unacceptable if it's not a subgraph of a component that is part of the final graph but not of the actual graph.

    Args:
        G_actual (networkx.Graph): Graph on which we want to add edges.
        G_final (networkx.Graph): Final graph, from where we find potential edges that can be added to the actual graph.

    Returns:
        list: List of tuple, each tuple being an invalid edge to add to G_actual from G_final.
    """
    invalid_edges = [
        edge
        for edge in G_final.edges
        if (not any(node in G_actual for node in edge)) or edge in G_actual.edges
    ]
    # If already the final number of cc or will connect in the future give list of adjacent edge only
    if nx.number_connected_components(G_actual) >= nx.number_connected_components(
        G_final
    ):
        return invalid_edges
    # Else a new component can be created, but need to be within a final component not already on the graph
    else:
        updated_invalid_edges = invalid_edges.copy()
        for edge in invalid_edges:
            new_edges = list(G_actual.edges)
            # Graph.edge_subgraph can only use list of tuple, not list of list
            new_edges.append(tuple(edge))
            H = G_final.edge_subgraph(new_edges)
            # Accept edges (remove from invalid edges) that if added to the graph create a new component that is a subgraph of a component of the final graph
            if not any(
                not any(node in cc for node in elect_nodes(H))
                for cc in list(nx.connected_components(G_final))
            ):
                updated_invalid_edges.remove(edge)
        return updated_invalid_edges


def elect_nodes(G):
    """Take one node from each components of G to represent them."""
    return [next(iter(cc)) for cc in list(nx.connected_components(G))]
