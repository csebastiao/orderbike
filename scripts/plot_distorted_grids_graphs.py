# -*- coding: utf-8 -*-
"""
Script plot distorted grids.
"""

from matplotlib import pyplot as plt
from utg import utils as utgut
from orderbike.plot import plot_graph


if __name__ == "__main__":
    fig, axs = plt.subplots(1, 5, figsize=(50, 10))
    for i in range(5):
        folderoots = f"data/processed/ignored_files/utg_distorted_grids/dg_{i}"
        G = utgut.load_graph(folderoots + "/graph.graphml")
        plot_graph(
            G,
            filepath=folderoots + "/picture.png",
            figsize=(10, 10),
            bbox=[-100, 1000, -100, 1000],
            buffer=False,
            edge_color="black",
            edge_linewidth=4,
            node_color="black",
            node_size=200,
            show=False,
            save=True,
            close=True,
        )
        plot_graph(
            G,
            ax=axs[i],
            figsize=(10, 10),
            bbox=[-100, 1000, -100, 1000],
            buffer=False,
            edge_color="black",
            edge_linewidth=4,
            node_color="black",
            node_size=200,
            show=False,
            save=False,
            close=False,
        )
    fig.tight_layout()
    fig.savefig("data/processed/ignored_files/utg_distorted_grids/all_graphs.png")
