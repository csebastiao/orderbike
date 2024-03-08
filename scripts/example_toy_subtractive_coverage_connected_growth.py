# -*- coding: utf-8 -*-
"""
Example script to test the growth of a basic example of a bridge graph that we want to grow from a single square of built network, with connectedness constraint, in a subtractive order fro the greedy optimization.
"""

# import os

import osmnx as ox

from orderbike import growth, metrics
from utg import create_graph
from utg import utils as utgut

if __name__ == "__main__":
    G = create_graph.create_bridge_graph()
    for edge in G.edges:
        G.edges[edge]["built"] = 0
    for edge in [[5, 6], [5, 10], [6, 11], [10, 11]]:
        G.edges[edge]["built"] = 1
    G_plot = utgut.make_osmnx_compatible(G)
    ec = ox.plot.get_edge_colors_by_attr(G_plot, "built", cmap="copper")
    ox.plot_graph(G_plot, bgcolor="white", node_color="black", edge_color=ec)
    order_growth = growth.order_network_growth(
        G,
        built=True,
        keep_connected=True,
        order="additive",
        metric_func=metrics.get_coverage,
        precomp_func=metrics.prefunc_coverage,
    )
    # order_growth.reverse()
    G_built = G.edge_subgraph([edge for edge in G.edges if G.edges[edge]["built"] == 1])
    actual_edges = [edge for edge in G_built.edges]
    foldername = "./plots/example_toy_subtractive_coverage_connected_growth"
    # if not os.path.exists(foldername):
    #     os.makedirs(foldername)
    for ids, edge in enumerate(order_growth):
        actual_edges.append(edge)
        G_actual = G.edge_subgraph(actual_edges)
        utgut.plot_graph(G_actual)
        # utgut.plot_graph(G_actual, show=False, save=True, filepath=foldername + f"/{ids:02}.png")
