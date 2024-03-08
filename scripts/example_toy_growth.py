# -*- coding: utf-8 -*-
"""
Example script to test the growth of a basic example of a bridge graph that we want to grow from a single square of built network, with connectedness constraint, in a subtractive order fro the greedy optimization.
"""

import os

from orderbike import growth, metrics, plot
from utg import create_graph


if __name__ == "__main__":
    G = create_graph.create_bridge_graph()
    for edge in G.edges:
        G.edges[edge]["built"] = 0
    for edge in [[5, 6], [5, 10], [6, 11], [10, 11]]:
        G.edges[edge]["built"] = 1
    order_growth = growth.order_network_growth(
        G,
        built=True,
        keep_connected=True,
        order="additive",
        metric_func=metrics.get_coverage,
        precomp_func=metrics.prefunc_coverage,
    )
    foldername = "./plots/example_toy_additive_coverage_connected_growth"
    if not os.path.exists(foldername):
        os.makedirs(foldername)
    # Necessary as long as using osmnx for plotting function
    G.graph["crs"] = "epsg:2154"
    plot.plot_growth(G, order_growth, foldername)
