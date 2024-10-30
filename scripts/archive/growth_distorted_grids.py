# -*- coding: utf-8 -*-
"""
Script to find growth order on randomly distorted grids, with all growth strategies, dynamic and ranked, and random trials.
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
    TESTED_GRAPH = 5
    for i in range(TESTED_GRAPH):
        log.info(f"Test on distorted grid number {i}")
        G = create_graph.create_distorted_grid_graph(
            rows=10, cols=10, width=100, spacing=0.9
        )
        # Put slightly more than 150 to avoid rounding wizardry
        BUFF_SIZE = 152
        NUM_TRIAL = 10
        NUM_RAND_TRIAL = 100
        PAD = len(str(max(NUM_TRIAL, NUM_RAND_TRIAL) - 1))
        foldergraph = f"./data/processed/ignored_files/utg_distorted_grids/dg_{i}/"
        if not os.path.exists(foldergraph):
            os.makedirs(foldergraph)
        utgut.save_graph(G, foldergraph + "/graph.graphml")
        utgut.plot_graph(
            G,
            save=True,
            show=False,
            close=True,
            filepath=foldergraph + "/picture.png",
        )
        for ORDERNAME in [
            "additive",
            "subtractive",
        ]:
            for METRICNAME in [
                "directness",
                "coverage",
                "adaptive_coverage",
                "relative_directness",
            ]:
                log.info(
                    f"Start computation for metric {METRICNAME}, order {ORDERNAME}"
                )
                if METRICNAME == "coverage":
                    kwargs = {"buff_size": BUFF_SIZE}
                elif METRICNAME == "adaptive_coverage":
                    kwargs = {"max_buff": BUFF_SIZE * 2, "min_buff": BUFF_SIZE / 2}
                else:
                    kwargs = {}
                foldername = foldergraph + METRICNAME + "_" + ORDERNAME
                if CONNECTED:
                    foldername += "_connected"
                if BUILT:
                    foldername += "_built"
                if not os.path.exists(foldername):
                    os.makedirs(foldername)
                if METRICNAME == "directness" and ORDERNAME == "additive":
                    realtrial = 1
                else:
                    realtrial = NUM_TRIAL
                for i in range(realtrial):
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
            for METRICNAME in ranking_func:
                log.info(
                    f"Start computation for metric {METRICNAME}, order {ORDERNAME}"
                )
                foldername = foldergraph + METRICNAME + "_" + ORDERNAME
                if CONNECTED:
                    foldername += "_connected"
                if BUILT:
                    foldername += "_built"
                if not os.path.exists(foldername):
                    os.makedirs(foldername)
                metrics_dict, order_growth = growth.order_ranked_network_growth(
                    G,
                    built=BUILT,
                    keep_connected=CONNECTED,
                    order=ORDERNAME,
                    ranking_func=ranking_func[METRICNAME],
                    save_metrics=True,
                    buff_size_metrics=BUFF_SIZE,
                )
                with open(foldername + f"/order_growth_{0:0{PAD}}.json", "w") as f:
                    json.dump(order_growth, f)
                with open(foldername + f"/metrics_growth_{0:0{PAD}}.json", "w") as f:
                    json.dump(metrics_dict, f)
            for i in range(NUM_RAND_TRIAL):
                log.info(f"Random computation, order {ORDERNAME}, trial {i}")
                foldername = foldergraph + "random_" + ORDERNAME
                if CONNECTED:
                    foldername += "_connected"
                if BUILT:
                    foldername += "_built"
                if not os.path.exists(foldername):
                    os.makedirs(foldername)
                metrics_dict, order_growth = growth.order_ranked_network_growth(
                    G,
                    built=BUILT,
                    keep_connected=CONNECTED,
                    order=ORDERNAME,
                    ranking_func=metrics.growth_random,
                    save_metrics=True,
                    buff_size_metrics=BUFF_SIZE,
                )
                with open(foldername + f"/order_growth_{i:0{PAD}}.json", "w") as f:
                    json.dump(order_growth, f)
                with open(foldername + f"/metrics_growth_{i:0{PAD}}.json", "w") as f:
                    json.dump(metrics_dict, f)
    log.info("Finished !")
