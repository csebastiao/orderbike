# -*- coding: utf-8 -*-
"""
Script to find growth order on the toy graphs, with all growth strategies, dynamic and ranked, and random trials.
"""

import os
import json
from orderbike import growth, metrics, plot
from orderbike.utils import log
import osmnx as ox


if __name__ == "__main__":
    BUILT = True
    CONNECTED = True
    ranking_func = {}
    ranking_func["closeness"] = metrics.growth_closeness
    ranking_func["betweenness"] = metrics.growth_betweenness
    BUFF_SIZE = 350
    MAX_BUFF = 600
    MIN_BUFF = 200
    NUM_RAND_TRIAL = 50
    graph_name = "Paris"
    folderoots = "./data/processed/ignored_files/results_paris"
    G = ox.load_graphml(folderoots + "/paris_bikeplan_pruned_multigraph.graphml")
    for e in G.edges:
        G.edges[e]["built"] = int(G.edges[e]["built"])
    PAD = max(len(str(NUM_RAND_TRIAL - 1)), len(str(NUM_RAND_TRIAL - 1)))
    log.info(f"Start graph {graph_name}")
    plot.plot_graph(
        G,
        filepath=folderoots + "/picture.png",
        figsize=(10, 10),
        buffer=False,
        edge_color="black",
        edge_linewidth=4,
        node_color="black",
        node_size=200,
        show=False,
        save=True,
        close=True,
    )
    for ORDERNAME in [
        "additive",
        # "subtractive",
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
            with open(foldername + "/order_growth.json", "w") as f:
                json.dump(order_growth, f)
            with open(foldername + "/metrics_growth.json", "w") as f:
                json.dump(metrics_dict, f)
        for METRICNAME in ranking_func:
            log.info(f"Start computation for metric {METRICNAME}, order {ORDERNAME}")
            foldername = folderoots + "/" + METRICNAME + "_" + ORDERNAME
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
            with open(foldername + "/order_growth.json", "w") as f:
                json.dump(order_growth, f)
            with open(foldername + "/metrics_growth.json", "w") as f:
                json.dump(metrics_dict, f)
        log.info(f"Start random computation, order {ORDERNAME}")
        foldername = folderoots + "/" + "random_" + ORDERNAME
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
