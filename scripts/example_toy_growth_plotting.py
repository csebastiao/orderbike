# -*- coding: utf-8 -*-
"""
Example script to plot of a basic example of a bridge graph that we want to grow from a single square of built network, with connectedness constraint, in a subtractive order fro the greedy optimization.
"""

import json

from matplotlib import pyplot as plt

from orderbike import plot
from utg import utils

if __name__ == "__main__":
    foldername = "./data/processed/example_toy_growth/adaptative_coverage_additive_connected_built"
    with open(foldername + "/order_growth.json", "r") as f:
        growth_steps = json.load(f)
    G = utils.load_graph(foldername + "/toy_graph.graphml")
    fig, ax = plot.plot_adaptative_coverage(G, growth_steps, plot_change=False)
    plt.legend()
    plt.show()
