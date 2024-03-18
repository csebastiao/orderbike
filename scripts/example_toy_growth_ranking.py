# -*- coding: utf-8 -*-
"""
Example script to test the growth of a basic example of a bridge graph that we want to grow from a single square of built network, with connectedness constraint, in a subtractive order fro the greedy optimization.
"""

import os

import json

from orderbike import growth, metrics, plot
from utg import create_graph, utils


if __name__ == "__main__":
    G = create_graph.create_bridge_graph()
    for edge in G.edges:
        G.edges[edge]["built"] = 0
    for edge in [[5, 6], [5, 10], [6, 11], [10, 11]]:
        G.edges[edge]["built"] = 1
    rankings = {}
    rankings["random"] = metrics.growth_random
    rankings["betweenness"] = metrics.growth_betweenness
    for r in rankings:
        for ORDERNAME in ["additive", "subtractive"]:
            for CONNECTED in [True, False]:
                for BUILT in [True, False]:
                    # ORDERNAME = "subtractive"
                    # CONNECTED = False
                    order_growth = growth.order_ranked_network_growth(
                        G,
                        built=BUILT,
                        keep_connected=CONNECTED,
                        order=ORDERNAME,
                        ranking_func=rankings[r],
                    )
                    foldername = (
                        "./data/processed/ignored_files/example_toy_growth/"
                        + r
                        + "_"
                        + ORDERNAME
                    )
                    if CONNECTED:
                        foldername += "_connected"
                    if BUILT:
                        foldername += "_built"
                    if not os.path.exists(foldername):
                        os.makedirs(foldername)
                    with open(foldername + "/order_growth.json", "w") as f:
                        json.dump(order_growth, f)
                    utils.save_graph(G, foldername + "/toy_graph.graphml")
                    plot.plot_growth(G, order_growth, foldername, built=BUILT)
                    plot.make_growth_video(
                        foldername, foldername + "/growth_video.mp4", fps=3
                    )
