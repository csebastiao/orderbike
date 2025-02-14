# -*- coding: utf-8 -*-
"""
Script to find growth order on the diagonal grid, with all growth strategies, dynamic and ranked, and random trials.
"""

import os
import json

from utg import create_graph
import networkx as nx
from orderbike import growth, metrics
import utg.utils as utgut
from orderbike.utils import log


if __name__ == "__main__":
    BUILT = True
    CONNECTED = True
    ranking_func = {}
    ranking_func["closeness"] = metrics.growth_closeness
    ranking_func["betweenness"] = metrics.growth_betweenness
    G = create_graph.create_grid_graph(rows=10, cols=10, width=100, diagonal=False)
    nx.set_edge_attributes(G, 0, "built")
    G.edges[43, 53]["built"] = 1
    # Put slightly more than 150 to avoid rounding wizardry
    BUFF_SIZE = 152
    NUM_TRIAL = 50
    NUM_RAND_TRIAL = 1000
    PAD = max(len(str(NUM_RAND_TRIAL - 1)), len(str(NUM_RAND_TRIAL - 1)))
    log.info("Start grid2")
    folderoots = "./data/processed/ignored_files/paper/grid_2/"
    if not os.path.exists(folderoots):
        os.makedirs(folderoots)
    utgut.save_graph(G, folderoots + "graph.graphml")
    utgut.plot_graph(
        G,
        save=True,
        show=False,
        close=True,
        filepath=folderoots + "picture.png",
    )
    for ORDERNAME in [
        "additive",
        "subtractive",
    ]:
        for METRICNAME in [
            "adaptive_coverage",
            "coverage",
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
            foldername = folderoots + "/" + METRICNAME + "_" + ORDERNAME
            if CONNECTED:
                foldername += "_connected"
            if BUILT:
                foldername += "_built"
            if not os.path.exists(foldername):
                os.makedirs(foldername)
            # for i in range(find_last_trial(foldername) + 1, NUM_TRIAL):
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
                with open(foldername + f"/metrics_growth_{i:0{PAD}}.json", "w") as f:
                    json.dump(metrics_dict, f)
        for METRICNAME in ranking_func:
            log.info(f"Start computation for metric {METRICNAME}, order {ORDERNAME}")
            foldername = folderoots + METRICNAME + "_" + ORDERNAME
            if CONNECTED:
                foldername += "_connected"
            if BUILT:
                foldername += "_built"
            if not os.path.exists(foldername):
                os.makedirs(foldername)
            for i in range(NUM_TRIAL):
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
        log.info(f"Start random computation, order {ORDERNAME}")
        foldername = folderoots + "random_" + ORDERNAME
        if CONNECTED:
            foldername += "_connected"
        if BUILT:
            foldername += "_built"
        if not os.path.exists(foldername):
            os.makedirs(foldername)
        for i in range(NUM_RAND_TRIAL):
            log.info(f"Start trial {i}")
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
