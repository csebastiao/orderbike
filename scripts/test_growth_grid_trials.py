# -*- coding: utf-8 -*-
"""
Script to find growth order on the grid, with all growth strategies, dynamic and ranked, and random trials.
"""

import os
import json

from utg import create_graph
from utg import utils as utgut
from orderbike import growth, metrics
from orderbike.utils import log

if __name__ == "__main__":
    BUILT = False
    CONNECTED = True
    ranking_func = {}
    ranking_func["closeness"] = metrics.growth_closeness
    ranking_func["betweenness"] = metrics.growth_betweenness
    G = create_graph.create_grid_graph(rows=10, cols=10, diagonal=False, width=100)
    # Put slightly more than 150 to avoid rounding wizardry
    BUFF_SIZE = 152
    BEGIN_TRIAL = 0
    END_TRIAL = 50
    PAD = len(str(END_TRIAL))
    foldername = "./data/processed/ignored_files/utg_grid_trials/"
    if not os.path.exists(foldername):
        os.makedirs(foldername)
    utgut.save_graph(G, foldername + "/graph.graphml")
    utgut.plot_graph(
        G,
        save=True,
        show=False,
        close=True,
        filepath=foldername + "/picture.png",
    )
    for ORDERNAME in [
        "additive",
        "subtractive",
    ]:
        for METRICNAME in [
            "coverage",
            "adaptive_coverage",
            "directness",
            "relative_directness",
        ]:
            log.info(f"Start computation for metric {METRICNAME}, order {ORDERNAME}")
            if METRICNAME == "coverage":
                kwargs = {"buff_size": BUFF_SIZE}
            elif METRICNAME == "adaptive_coverage":
                kwargs = {"max_buff": BUFF_SIZE * 2, "min_buff": BUFF_SIZE / 2}
            else:
                kwargs = {}
            foldername = (
                "./data/processed/ignored_files/utg_grid_trials/"
                + METRICNAME
                + "_"
                + ORDERNAME
            )
            if CONNECTED:
                foldername += "_connected"
            if BUILT:
                foldername += "_built"
            if not os.path.exists(foldername):
                os.makedirs(foldername)
            for i in range(BEGIN_TRIAL, END_TRIAL):
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
                with open(foldername + f"/metrics_growth_{i:0{PAD}}.json", "w") as f:
                    json.dump(metrics_dict, f)
        for METRICNAME in ranking_func:
            log.info(f"Start computation for metric {METRICNAME}, order {ORDERNAME}")
            foldername = (
                "./data/processed/ignored_files/utg_grid_trials/"
                + METRICNAME
                + "_"
                + ORDERNAME
            )
            if CONNECTED:
                foldername += "_connected"
            if BUILT:
                foldername += "_built"
            if not os.path.exists(foldername):
                os.makedirs(foldername)
            for i in range(BEGIN_TRIAL, END_TRIAL):
                log.info(f"Start trial {i}")
                metrics_dict, order_growth = growth.order_ranked_network_growth(
                    G,
                    built=BUILT,
                    keep_connected=CONNECTED,
                    order=ORDERNAME,
                    ranking_func=ranking_func[METRICNAME],
                    save_metrics=True,
                    buff_size_metrics=BUFF_SIZE,
                )
                with open(foldername + f"/order_growth_{i:0{PAD}}.json", "w") as f:
                    json.dump(order_growth, f)
                with open(foldername + f"/metrics_growth_{i:0{PAD}}.json", "w") as f:
                    json.dump(metrics_dict, f)
    log.info("Finished !")
