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
    metrics_dict = {}
    metrics_dict["relative_directness"] = {
        "metric_func": metrics.growth_relative_directness,
        "precomp_func": metrics.prefunc_growth_relative_directness,
        "kwargs": {"G_final": G},
    }
    metrics_dict["directness"] = {
        "metric_func": metrics.directness,
        "precomp_func": None,
        "kwargs": None,
    }
    metrics_dict["coverage"] = {
        "metric_func": metrics.growth_coverage,
        "precomp_func": metrics.prefunc_growth_coverage,
        "kwargs": {"buff_size": 200},
    }
    metrics_dict["adaptative_coverage"] = {
        "metric_func": metrics.growth_coverage,
        "precomp_func": metrics.prefunc_growth_adaptative_coverage,
        "kwargs": {"buff_size": 200, "G_final": G, "min_buff": 25},
    }
    for m in metrics_dict:
        for ORDERNAME in ["additive", "subtractive"]:
            for CONNECTED in [True, False]:
                for BUILT in [True, False]:
                    # ORDERNAME = "subtractive"
                    # CONNECTED = False
                    if metrics_dict[m]["kwargs"] is not None:
                        kwargs = metrics_dict[m]["kwargs"]
                    else:
                        kwargs = {}
                    order_growth = growth.order_dynamic_network_growth(
                        G,
                        built=BUILT,
                        keep_connected=CONNECTED,
                        order=ORDERNAME,
                        metric_func=metrics_dict[m]["metric_func"],
                        precomp_func=metrics_dict[m]["precomp_func"],
                        progress_bar=True,
                        **kwargs,
                    )
                    foldername = (
                        "./data/processed/ignored_files/example_toy_growth/"
                        + m
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
                    plot.plot_growth(
                        G,
                        order_growth,
                        foldername,
                        built=BUILT,
                        color_built="firebrick",
                        color_added="steelblue",
                        color_newest="darkgreen",
                        node_size=8,
                    )
                    plot.make_growth_video(
                        foldername, foldername + "/growth_video.mp4", fps=3
                    )
