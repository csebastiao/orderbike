# -*- coding: utf-8 -*-
"""
Example script to plot of a basic example of a bridge graph that we want to grow from a single square of built network, with connectedness constraint, in a subtractive order fro the greedy optimization.
"""

import os

import json

from orderbike import plot
from utg import utils

if __name__ == "__main__":
    init_dir = "./data/processed/ignored_files/example_toy_growth/"
    for foldername in os.listdir(init_dir):
        folderpath = init_dir + foldername
        with open(folderpath + "/order_growth.json", "r") as f:
            growth_steps = json.load(f)
        G = utils.load_graph(folderpath + "/toy_graph.graphml")
        if "adaptative_coverage" in foldername:
            fig, ax = plot.plot_adaptative_coverage(
                G,
                growth_steps,
                show=False,
                save=True,
                close=True,
                filepath=folderpath + "/adaptative_coverage_change.png",
                x_meter=True,
                buff_size=200,
                min_buff=25,
                plot_change=True,
            )
        fig, ax = plot.plot_coverage(
            G,
            growth_steps,
            show=False,
            save=True,
            close=True,
            filepath=folderpath + "/coverage.png",
        )
        fig, ax = plot.plot_directness(
            G,
            growth_steps,
            show=False,
            save=True,
            close=True,
            filepath=folderpath + "/directness.png",
            x_meter=True,
        )
        fig, ax = plot.plot_relative_directness(
            G,
            growth_steps,
            show=False,
            save=True,
            close=True,
            filepath=folderpath + "/relative_directness.png",
            x_meter=True,
        )
