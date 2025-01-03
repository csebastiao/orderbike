# -*- coding: utf-8 -*-
"""
Script to plot the ranking of the edges.
"""

import pathlib
import json
import pandas as pd
import seaborn as sns
import networkx as nx
import numpy as np
from matplotlib import pyplot as plt
from utg import utils as utgut

# TODO Fix all arrays must be of the same length thing
if __name__ == "__main__":
    folderoots = "./data/processed/ignored_files/utg"
    sns.set_theme(style="whitegrid")
    # Open for all toy graphs
    for toy_graph_folder in [
        fold
        for fold in pathlib.Path(folderoots).iterdir()
        if ".DS_Store" not in str(fold)
    ]:
        G = utgut.load_graph(str(toy_graph_folder) + "/graph.graphml")
        random_add = []
        random_sub = []
        arr_add_graph = []
        arr_sub_graph = []
        # Open for all growth strategies for a toy graph
        for growth_f in [
            fold
            for fold in pathlib.Path(toy_graph_folder).iterdir()
            if not fold.is_file()
            and "plot" not in str(fold)
            and ".DS_Store" not in str(fold)
        ]:
            # For random trials, open all trials
            if "random_trials" in str(growth_f):
                for random_trial in list(pathlib.Path(growth_f).iterdir()):
                    # Open only the metrics growth not the order growth
                    if "order" in str(random_trial):
                        with open(random_trial, "r") as f:
                            # Divide between additive and subtractive growth
                            if "random_trials_additive" in str(random_trial):
                                random_add.append(json.load(f))
                            else:
                                random_sub.append(json.load(f))
            else:
                if "additive" in str(growth_f):
                    with open(str(growth_f) + "/order_growth.json", "r") as f:
                        arr_add_graph.append(json.load(f))
                elif "subtractive" in str(growth_f):
                    with open(str(growth_f) + "/order_growth.json", "r") as f:
                        arr_sub_graph.append(json.load(f))
        # Create plot folder if not existing
        plotpath = str(toy_graph_folder) + "/plots"
        pathlib.Path(plotpath).mkdir(parents=True, exist_ok=True)
        pos = {}
        # Do ranking for subtractive orders
        # Different than additive as with additive always start with the same one
        for val in G.edges:
            pos[str(val)] = np.array([])
        for arr in arr_sub_graph:
            for idx, val in enumerate(arr):
                pos[str(tuple(val))] = np.append(pos[str(tuple(val))], [idx])
        max_len = max([len(pos[val]) for val in pos])
        for val in pos:
            if len(pos[val]) < max_len:
                a = np.empty(max_len - len(pos[val]))
                a[:] = np.nan
                pos[val] = np.concatenate([pos[val], a])
        df = pd.DataFrame.from_dict(pos)
        order = df.median().sort_values().index
        # Start plotting order
        # Large figsize for police
        fig, ax = plt.subplots(figsize=(32, 18))
        ax.set_title(
            f"{str(toy_graph_folder).split("/")[-1]}, ranking of the edges, subtractive order"
        )
        sns.boxplot(pos, ax=ax, order=order)
        ax.set_xlabel("Edge ID")
        ax.set_ylabel("Ranking")
        ax.tick_params(axis="x", labelrotation=90)
        plt.tight_layout()
        plt.savefig(plotpath + "/ranking_edges_sub.png", dpi=200)
        plt.close()
        # Do ranking for additive orders
        pos = {}
        for arr in arr_add_graph:
            for idx, val in enumerate(arr):
                val = str(val)
                if val in pos:
                    pos[val] = np.append(pos[val], [idx])
                else:
                    pos[val] = np.array([idx])
        # Find init edge with highest closeness
        # Could also find the one not in the dict
        closeness = nx.closeness_centrality(G, distance="length")
        edge_closeness = {}
        for edge in G.edges:
            edge_closeness[edge] = (closeness[edge[0]] + closeness[edge[1]]) / 2
        e_init = tuple(max(edge_closeness, key=edge_closeness.get))
        df = pd.DataFrame.from_dict(pos)
        order = df.median().sort_values().index
        # Start plotting order
        fig, ax = plt.subplots(figsize=(32, 18))
        ax.set_title(
            f"{str(toy_graph_folder).split("/")[-1]}, ranking of the edges, additive order, initialized with {e_init}"
        )
        sns.boxplot(pos, ax=ax, order=order)
        ax.set_xlabel("Edge ID")
        ax.set_ylabel("Ranking")
        ax.tick_params(axis="x", labelrotation=90)
        plt.tight_layout()
        plt.savefig(plotpath + "/ranking_edges_add.png", dpi=200)
        plt.close()
