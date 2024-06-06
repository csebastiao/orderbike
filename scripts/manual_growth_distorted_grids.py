# -*- coding: utf-8 -*-
"""
Script to find growth order on the grid, with all growth strategies, dynamic and ranked, and random trials.
"""

import os
import json
import pathlib

from utg import utils as utgut
from orderbike import growth

if __name__ == "__main__":
    foldermanual = (
        "./data/processed/ignored_files/utg_grid_trials/manual_additive_connected"
    )
    manual_orders = []
    for order in [
        order
        for order in pathlib.Path(foldermanual).iterdir()
        if order.is_file() and "order_growth" in str(order) and ".json" in str(order)
    ]:
        with open(order, "r") as f:
            arr_ord = json.load(f)
        manual_orders.append([tuple(val) for val in arr_ord])
    for i in range(4, 5):
        folderoots = f"./data/processed/ignored_files/utg_distorted_grids/dg_{i}/"
        G = utgut.load_graph(folderoots + "graph.graphml")
        rootsman = folderoots + "manual_additive_connected/"
        if not os.path.exists(rootsman):
            os.makedirs(rootsman)
        for ids, order in enumerate(manual_orders):
            with open(rootsman + f"/order_growth_{ids}.json", "w") as f:
                json.dump(order, f)
            met_dict = growth.compute_metrics(G, order, built=False, buff_size=152)
            with open(rootsman + f"/metrics_growth_{ids}.json", "w") as f:
                json.dump(met_dict, f)
