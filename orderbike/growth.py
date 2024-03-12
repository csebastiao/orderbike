# -*- coding: utf-8 -*-
"""
Functions to make subtractive or additive growth of a graph.
"""

import networkx as nx
from . import metrics


# TODO: Find common structure with precomp func and func only with kwargs or something, see coverage
# TODO: Make kwargs for precomp func and for func or find smarter way to pick one
# TODO: Add logging or verbose to make sur to always understand what happens here ?
def order_network_growth(
    G,
    built=True,
    keep_connected=True,
    order="subtractive",
    metric_func=metrics.growth_coverage,
    precomp_func=metrics.prefunc_growth_coverage,
    **kwargs,
):
    """
    Find the optimal order of growth for a network based on the greedy optimization of a metric.

     For the greedy optimization, an order can

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
    if built:
        init_edges = [edge for edge in G.edges if G.edges[edge]["built"] == 1]
    # If no built part, start from a seed being a random edge from the node with the highest closeness
    else:
        # If subtractive, don't care about finding an initial edge because will be found through optimization, dummy variable
        if order == "subtractive":
            init_edges = [0]
        # If additive, use as initial edge if none given the one with the highest average closeness of its nodes
        elif order == "additive":
            closeness = nx.closeness_centrality(G, distance="length")
            edge_closeness = {}
            for edge in G.edges:
                u, v = edge
                edge_closeness[edge] = (closeness[u] + closeness[v]) / 2
            init_edges = [tuple(max(edge_closeness, key=edge_closeness.get))]
    if order == "subtractive":
        G_actual = G.copy()
    elif order == "additive":
        actual_edges = init_edges.copy()
        G_actual = G.edge_subgraph(actual_edges)
    num_step = len(G.edges) - len(init_edges)
    for i in range(num_step):
        if precomp_func is not None:
            precomp_kwargs = precomp_func(G_actual, order=order, **kwargs)
        else:
            precomp_kwargs = kwargs
        # If connectedness constraint remove invalid edges that would add unacceptable new component
        if keep_connected:
            if order == "subtractive":
                invalid_edges = get_subtractive_invalid_edges(G_actual, built=built)
                valid_edges = [
                    edge for edge in G_actual.edges if edge not in invalid_edges
                ]
            elif order == "additive":
                invalid_edges = get_additive_invalid_edges(G_actual, G)
                valid_edges = [edge for edge in G.edges if edge not in invalid_edges]
        else:
            if order == "subtractive":
                valid_edges = [
                    edge for edge in G_actual.edges if edge not in init_edges
                ]
            elif order == "additive":
                valid_edges = [edge for edge in G.edges if edge not in G_actual.edges]
        metric_vals = []
        # Remove/add an edge to the actual graph and compute the metric on it
        for edge in valid_edges:
            if order == "subtractive":
                H = G_actual.copy()
                H.remove_edge(*edge)
            elif order == "additive":
                temp_edges = actual_edges.copy()
                temp_edges.append(edge)
                H = G.edge_subgraph(temp_edges)
            temp_m = metric_func(H, edge, **precomp_kwargs)
            metric_vals.append(temp_m)
        # Choose the edge that gives the maximum value for the metric
        step = optimal_step(metric_vals, valid_edges)
        if order == "subtractive":
            G_actual.remove_edge(*step)
        elif order == "additive":
            actual_edges.append(step)
            G_actual = G.edge_subgraph(actual_edges)
        order_growth.append(step)
    if order == "subtractive":
        order_growth.reverse()
    return order_growth


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


# TODO: Solve issue of having an edge
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


def optimal_step(vals, steps):
    """Return the step giving the maximal value."""
    return max(zip(vals, steps))[1]
