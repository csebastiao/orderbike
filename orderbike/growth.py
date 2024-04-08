# -*- coding: utf-8 -*-
"""
Functions to make subtractive or additive growth of a graph.
"""

import tqdm

import networkx as nx

from . import metrics


# TODO: Add logging to make sure to always understand what in ranked and dynamic network growth
def order_ranked_network_growth(
    G,
    built=True,
    keep_connected=True,
    order="subtractive",
    ranking_func=metrics.growth_random,
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
            testing_ranking = absolute_ranking.copy()
            # In subtractive order, choose the edge with the lowest ranking, in additive the highest
            if order == "subtractive":
                testing_ranking.reverse()
            for edge in testing_ranking:
                if edge in valid_edges:
                    step = edge
                    break
            G_actual = _update_actual_graph(G, G_actual, step, order)
            absolute_ranking.remove(step)
            order_growth.append(step)
        if order == "subtractive":
            order_growth.reverse()
    else:
        order_growth = [step for step in absolute_ranking if step not in init_edges]
        # Since in subtractive order without a built part we don't initialize edges, we need to remove the first edge of the ranking
        if order == "subtractive" and built is False:
            order_growth = order_growth[1:]
    return order_growth


def order_dynamic_network_growth(
    G,
    built=True,
    keep_connected=True,
    order="subtractive",
    metric_func=metrics.growth_coverage,
    precomp_func=metrics.prefunc_growth_coverage,
    progress_bar=True,
    **kwargs,
):
    """
    Find the optimal order of growth for a network based on the greedy optimization of a metric.

    Args:
        G (networkx.Graph): Final graph. The initial graph from where we grow is based on the built attribute.
        built (bool, optional): If True, the graph will be initialized with all edges having as an attribute "built" = 1. Else it will be initialized with an arbitrary edge of the node with the highest closeness value. Defaults to True.
        keep_connected (bool, optional): If True, the number of components of G will be as small as possible for all the growth, restricting the list of edges that can be added. Defaults to True.
        order (str, optional): Either subtractive or additive. Gives the order for the greedy optimization. The subtractive (resp. additive) start from the final (resp. initial) graph and remove (resp. add) edges until reaching the initial graph (resp. final). Defaults to "subtractive".
        metric_func (function, optional): The function computing the metric on G. Defaults to metrics.get_coverage.
        precomp_func (function, optional): A sister function to metric_func to compute values before the loop on all valid edges. Defaults to metrics.prefunc_coverage.

    Returns:
        list: Ordered list of edges. For subtractive (resp. additive) order, the first edge in the list is the last (resp. first) to add. If built is True, will only have edges with "built" != 1. Else, will have all edges of G except the seed.
    """
    order_growth = []
    init_edges = _init_edges(G, built, order)
    G_actual = _init_graph(G, order, init_edges)
    num_step = len(G.edges) - len(init_edges)
    if progress_bar:
        total_step = tqdm.tqdm(range(num_step))
    else:
        total_step = range(num_step)
    for i in total_step:
        if precomp_func is not None:
            precomp_kwargs = precomp_func(G_actual, order=order, **kwargs)
        else:
            precomp_kwargs = kwargs
        valid_edges = _valid_edges(
            G, G_actual, init_edges, built, keep_connected, order
        )
        metric_vals = []
        # Remove/add an edge to the actual graph and compute the metric on it
        for edge in valid_edges:
            H = _update_tested_graph(G_actual, G, edge, order)
            temp_m = metric_func(H, edge, **precomp_kwargs)
            metric_vals.append(temp_m)
        # Choose the edge that gives the maximum value for the metric
        step = max(zip(metric_vals, valid_edges))[1]
        G_actual = _update_actual_graph(G, G_actual, step, order)
        order_growth.append(step)
    if order == "subtractive":
        order_growth.reverse()
    return order_growth


def _init_edges(G, built, order):
    """Return the initial edges for the first step of the growth of G."""
    if built:
        return [edge for edge in G.edges if G.edges[edge]["built"] == 1]
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
    # Find all bridges and remove bridges that when remove leave an isolated node
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
