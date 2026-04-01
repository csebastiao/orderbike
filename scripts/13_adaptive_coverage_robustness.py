# -*- coding: utf-8 -*-
"""
Script to find growth order on the toy graphs, with all growth strategies, dynamic and ranked, and random trials.
"""

import os
import json

from utg import create_graph
from orderbike import growth
from orderbike.utils import log


if __name__ == "__main__":
    BUILT = False
    CONNECTED = True
    graph_list = {}
    # graph_list["grid"] = create_graph.create_grid_graph(
    #     rows=10, cols=10, width=100, diagonal=False
    # )
    graph_list["radio_concentric"] = create_graph.create_concentric_graph(
        radial=10, zones=9, center=True, radius=100
    )
    graph_list["three_bridges"] = create_graph.create_bridge_graph(
        outrows=3, sscols=4, bridges=3, blength=300, block_side=100
    )
    graph_list["grid_with_diagonal"] = create_graph.create_grid_graph(
        rows=10, cols=10, width=100, diagonal=True
    )
    # Put slightly more than 150 to avoid rounding wizardry
    BUFF_SIZE = 152
    NUM_TRIAL = 50
    PAD = 3
    for graph_name, G in graph_list.items():
        folderoots = f"./data/processed/ignored_files/paper/{graph_name}/"
        METRICNAME = "adaptive_coverage"
        if not os.path.exists(folderoots):
            os.makedirs(folderoots)
        for threshold in [
            0.2,
            0.05,
        ]:
            log.info(f"Start threshold of {threshold * 100}%")
            for ORDERNAME in [
                "additive",
                # "subtractive",
            ]:
                log.info(
                    f"Start computation for metric {METRICNAME}, order {ORDERNAME}"
                )
                kwargs = {
                    "max_buff": BUFF_SIZE * 2,
                    "min_buff": BUFF_SIZE / 2,
                    "threshold_min_change": 0 + threshold,
                    "threshold_max_change": 1 - threshold,
                }
                foldername = folderoots + "/" + METRICNAME + "_" + ORDERNAME
                if CONNECTED:
                    foldername += "_connected"
                if BUILT:
                    foldername += "_built"
                foldername += "_" + str(int(threshold * 100))
                if not os.path.exists(foldername):
                    os.makedirs(foldername)
                for i in range(NUM_TRIAL):
                    log.info(f"Start trial {i}")
                    metrics_dict, order_growth = growth.order_dynamic_network_growth(
                        G,
                        built=BUILT,
                        keep_connected=CONNECTED,
                        order=ORDERNAME,
                        metric=METRICNAME,
                        progress_bar=False,
                        save_metrics=True,
                        buff_size_metrics=BUFF_SIZE,
                        **kwargs,
                    )
                    with open(foldername + f"/order_growth_{i:0{PAD}}.json", "w") as f:
                        json.dump(order_growth, f)
                    with open(
                        foldername + f"/metrics_growth_{i:0{PAD}}.json", "w"
                    ) as f:
                        json.dump(metrics_dict, f)
