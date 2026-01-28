# -*- coding: utf-8 -*-
"""
Script to computer orders on a small urban network, to give empirical example.
"""

import json
import pathlib
import os

import geopandas as gpd
import momepy

from orderbike import growth, metrics
from orderbike.plot import plot_graph
from orderbike.utils import log


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
    streets = gpd.read_file(
        "./data/processed/ignored_files/paper/smrainet/idf_metro.gpkg"
    )
    streets = streets.loc[streets.geometry.type == "LineString"]
    streets = streets.to_crs(streets.estimate_utm_crs())
    G = momepy.gdf_to_nx(streets, approach="primal", integer_labels=True)
    for e in G.edges:
        G.edges[e]["length"] = G.edges[e]["geometry"].length
    graph_name = "smrainet"
    BUFF_SIZE = 500
    NUM_TRIAL = 50
    NUM_RAND_TRIAL = 1000
    PAD = max(len(str(NUM_RAND_TRIAL - 1)), len(str(NUM_RAND_TRIAL - 1)))
    log.info(f"Start graph {graph_name}")
    folderoots = f"./data/processed/ignored_files/paper/{graph_name}/"
    if not os.path.exists(folderoots):
        os.makedirs(folderoots)
    plot_graph(
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
                NUM_TRIAL = 50
            elif METRICNAME == "adaptive_coverage":
                kwargs = {"max_buff": BUFF_SIZE * 2, "min_buff": BUFF_SIZE / 2}
                NUM_TRIAL = 50
            else:
                NUM_TRIAL = 1
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
            NUM_TRIAL = 1
            log.info(f"Start computation for metric {METRICNAME}, order {ORDERNAME}")
            foldername = folderoots + METRICNAME + "_" + ORDERNAME
            if CONNECTED:
                foldername += "_connected"
            if BUILT:
                foldername += "_built"
            if not os.path.exists(foldername):
                os.makedirs(foldername)
            # for i in range(find_last_trial(foldername) + 1, NUM_TRIAL):
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
        # for i in range(find_last_trial(foldername) + 1, NUM_RAND_TRIAL):
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
