# -*- coding: utf-8 -*-
"""
Script to find growth order on the diagonal grid, with all growth strategies, dynamic and ranked, and random trials.
"""

import os
import json

from utg import create_graph
from utg import utils as utgut
from orderbike import growth, metrics
from orderbike.utils import log
import pathlib


def find_last_trial(folder):
    """Return last trial number already computed"""
    existing_trials = sorted(
        [
            str(x.stem)
            for x in pathlib.Path(folder).glob("**/*")
            if "metrics_growth" in str(x)
        ]
    )
    trial = -1
    if len(existing_trials) > 0:
        trial = int(existing_trials[-1].split("_")[-1])
    return trial


if __name__ == "__main__":
    BUILT = False
    CONNECTED = True
    ranking_func = {}
    ranking_func["closeness"] = metrics.growth_closeness
    ranking_func["betweenness"] = metrics.growth_betweenness
    graph_list = {}
    graph_list["radio_concentric"] = create_graph.create_concentric_graph(
        radial=10, zones=9, center=True, radius=100
    )
    graph_list["three_bridges"] = create_graph.create_bridge_graph(
        outrows=3, sscols=4, bridges=3, blength=300, block_side=100
    )
    graph_list["grid"] = create_graph.create_grid_graph(
        rows=10, cols=10, width=100, diagonal=False
    )
    graph_list["grid_with_diagonal"] = create_graph.create_grid_graph(
        rows=10, cols=10, width=100, diagonal=False
    )
    # Put slightly more than 150 to avoid rounding wizardry
    BUFF_SIZE = 152
    NUM_TRIAL = 50
    NUM_RAND_TRIAL = 1000
    PAD = max(len(str(NUM_RAND_TRIAL - 1)), len(str(NUM_RAND_TRIAL - 1)))
    for graph_name, G in graph_list.items():
        log.info(f"Start graph {graph_name}")
        folderoots = f"./data/processed/ignored_files/paper/{graph_name}/"
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
                "coverage",
                "adaptive_coverage",
                "directness",
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
                foldername = folderoots + "/" + METRICNAME + "_" + ORDERNAME
                if CONNECTED:
                    foldername += "_connected"
                if BUILT:
                    foldername += "_built"
                if not os.path.exists(foldername):
                    os.makedirs(foldername)
                for i in range(find_last_trial(foldername) + 1, NUM_TRIAL):
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
                foldername = folderoots + METRICNAME + "_" + ORDERNAME
                if CONNECTED:
                    foldername += "_connected"
                if BUILT:
                    foldername += "_built"
                if not os.path.exists(foldername):
                    os.makedirs(foldername)
                for i in range(find_last_trial(foldername) + 1, NUM_TRIAL):
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
                    with open(
                        foldername + f"/metrics_growth_{i:0{PAD}}.json", "w"
                    ) as f:
                        json.dump(metrics_dict, f)
            log.info(f"Start random computation, order {ORDERNAME}")
            foldername = folderoots + "random_" + ORDERNAME
            if CONNECTED:
                foldername += "_connected"
            if BUILT:
                foldername += "_built"
            if not os.path.exists(foldername):
                os.makedirs(foldername)
            for i in range(find_last_trial(foldername) + 1, NUM_RAND_TRIAL):
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
