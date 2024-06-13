# -*- coding: utf-8 -*-
"""
Script to find growth on Paris pruned bikeplan.
"""

import os
import json

import osmnx as ox

from orderbike import growth, metrics, plot
from orderbike.utils import log

if __name__ == "__main__":
    BUILT = True
    CONNECTED = True
    ranking_func = {}
    ranking_func["closeness"] = metrics.growth_closeness
    ranking_func["betweenness"] = metrics.growth_betweenness
    G = ox.load_graphml(
        "./data/processed/plan_paris/paris_bikeplan_pruned_multigraph.graphml"
    )
    for e in G.edges:
        G.edges[e]["built"] = int(G.edges[e]["built"])
    # Put slightly more than 150 to avoid rounding wizardry
    BUFF_SIZE = 350
    MAX_BUFF = 600
    MIN_BUFF = 200
    folderoots = "./data/processed/plan_paris/ignored_growth/pruned_paris_multigraph/"
    if not os.path.exists(folderoots):
        os.makedirs(folderoots)
    for ORDERNAME in [
        "additive",
        "subtractive",
    ]:
        for METRICNAME in ranking_func:
            log.info(f"Start computation for metric {METRICNAME}")
            foldername = folderoots + METRICNAME + "_" + ORDERNAME
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
            foldergrowth_buff = foldername + "/plots"
            if not os.path.exists(foldergrowth_buff):
                os.makedirs(foldergrowth_buff)
            plot.plot_growth(
                G,
                order_growth,
                foldergrowth_buff,
                built=True,
                color_built="firebrick",
                color_added="steelblue",
                color_newest="darkgreen",
                node_size=8,
                buffer=True,
                plot_metrics=True,
                growth_cov=metrics_dict["coverage"],
                growth_xx=metrics_dict["xx"],
                growth_dir=metrics_dict["directness"],
                growth_reldir=metrics_dict["relative_directness"],
            )
            plot.make_growth_video(
                foldergrowth_buff, foldergrowth_buff + "/growth_video.mp4", fps=3
            )
        for METRICNAME in [
            "coverage",
            "adaptive_coverage",
            "directness",
            "relative_directness",
        ]:
            log.info(f"Start computation for metric {METRICNAME}")
            if METRICNAME == "coverage":
                kwargs = {"buff_size": BUFF_SIZE}
            elif METRICNAME == "adaptive_coverage":
                kwargs = {"max_buff": MAX_BUFF, "min_buff": MIN_BUFF}
            else:
                kwargs = {}
            foldername = folderoots + METRICNAME + "_" + ORDERNAME
            if CONNECTED:
                foldername += "_connected"
            if BUILT:
                foldername += "_built"
            if not os.path.exists(foldername):
                os.makedirs(foldername)
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
            foldergrowth_buff = foldername + "/plots"
            if not os.path.exists(foldergrowth_buff):
                os.makedirs(foldergrowth_buff)
            plot.plot_growth(
                G,
                order_growth,
                foldergrowth_buff,
                built=True,
                color_built="firebrick",
                color_added="steelblue",
                color_newest="darkgreen",
                node_size=8,
                buffer=True,
                plot_metrics=True,
                growth_cov=metrics_dict["coverage"],
                growth_xx=metrics_dict["xx"],
                growth_dir=metrics_dict["directness"],
                growth_reldir=metrics_dict["relative_directness"],
            )
            plot.make_growth_video(
                foldergrowth_buff, foldergrowth_buff + "/growth_video.mp4", fps=3
            )
        log.info(f"Start random computation, order {ORDERNAME}")
        for i in range(100):
            log.info(f"Start trial {i}")
            foldername = folderoots + "random_" + ORDERNAME
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
            with open(foldername + f"/order_growth_{i:02}.json", "w") as f:
                json.dump(order_growth, f)
            with open(foldername + f"/metrics_growth_{i:02}.json", "w") as f:
                json.dump(metrics_dict, f)
    log.info("Finished !")
