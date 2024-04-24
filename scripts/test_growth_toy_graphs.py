# -*- coding: utf-8 -*-
"""
Script to find growth order on 5 urban toy graphs, with all growth strategies, dynamic and ranked, and random trials.
"""

import os
import json
import tqdm
from utg import create_graph
from utg import utils as utgut
from orderbike import growth, plot, metrics

if __name__ == "__main__":
    BUILT = False
    CONNECTED = True
    ranking_func = {}
    ranking_func["closeness"] = metrics.growth_closeness
    ranking_func["betweenness"] = metrics.growth_betweenness
    G_graph = {}
    G_graph["single_bridge"] = create_graph.create_bridge_graph(
        outrows=3, sscols=4, bridges=1, block_side=100, blength=300
    )
    G_graph["multiple_bridges"] = create_graph.create_bridge_graph(
        outrows=3, sscols=4, bridges=3, block_side=100, blength=300
    )
    G_graph["grid_wdiagonal"] = create_graph.create_grid_graph(
        rows=10, cols=10, diagonal=True, width=100
    )
    G_graph["grid"] = create_graph.create_grid_graph(
        rows=10, cols=10, diagonal=False, width=100
    )
    G_graph["radio_concentric"] = create_graph.create_concentric_graph(
        radial=8, zones=6, radius=100, straight_edges=True, center=True
    )
    # Put slightly more than 150 to avoid rounding wizardry
    BUFF_SIZE = 152
    for name in tqdm.tqdm(["grid"]):
        foldername = "./data/processed/ignored_files/utg/" + name
        if not os.path.exists(foldername):
            os.makedirs(foldername)
        utgut.save_graph(G_graph[name], foldername + "/graph.graphml")
        utgut.plot_graph(
            G_graph[name],
            save=True,
            show=False,
            close=True,
            filepath=foldername + "/picture.png",
        )
        for ORDERNAME in ["additive", "subtractive"]:
            for METRICNAME in [
                "coverage",
                "adaptive_coverage",
                "directness",
                "relative_directness",
            ]:
                if METRICNAME == "coverage":
                    kwargs = {"buff_size": BUFF_SIZE}
                elif METRICNAME == "adaptive_coverage":
                    kwargs = {"buff_size": BUFF_SIZE * 2, "min_buff": BUFF_SIZE / 2}
                else:
                    kwargs = {}
                metrics_dict, order_growth = growth.order_dynamic_network_growth(
                    G_graph[name],
                    built=BUILT,
                    keep_connected=CONNECTED,
                    order=ORDERNAME,
                    metric=METRICNAME,
                    progress_bar=False,
                    save_metrics=True,
                    buff_size_metrics=BUFF_SIZE,
                    **kwargs,
                )
                foldername = (
                    "./data/processed/ignored_files/utg/"
                    + name
                    + "/"
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
                with open(foldername + "/order_growth.json", "w") as f:
                    json.dump(order_growth, f)
                with open(foldername + "/metrics_growth.json", "w") as f:
                    json.dump(metrics_dict, f)
                md = {}
                md["growth"] = "dynamic"
                md["built"] = BUILT
                md["keep_connected"] = CONNECTED
                md["metric"] = METRICNAME
                md["order"] = ORDERNAME
                if METRICNAME == "adaptive_coverage":
                    md["max_buff_size"] = BUFF_SIZE * 2
                    md["min_buff_size"] = BUFF_SIZE / 2
                    md["threshold_change"] = 0.01
                md["buff_size"] = BUFF_SIZE
                with open(foldername + "/metadata.json", "w") as f:
                    json.dump(md, f)
                fig, ax = plot.plot_order_growth(
                    G_graph[name],
                    order_growth,
                    show=False,
                    save=True,
                    close=True,
                    filepath=foldername + "/order_growth.png",
                )
                plot.plot_growth(
                    G_graph[name],
                    order_growth,
                    foldername,
                    built=BUILT,
                    color_built="firebrick",
                    color_added="steelblue",
                    color_newest="darkgreen",
                    node_size=8,
                )
                plot.make_growth_video(
                    foldername, foldername + "/growth_video.mp4", fps=3
                )
                fig, ax = plot.plot_coverage(
                    G_graph[name],
                    order_growth,
                    built=BUILT,
                    show=False,
                    save=True,
                    close=True,
                    filepath=foldername + "/coverage.png",
                )
                fig, ax = plot.plot_directness(
                    G_graph[name],
                    order_growth,
                    show=False,
                    built=BUILT,
                    save=True,
                    close=True,
                    filepath=foldername + "/directness.png",
                    x_meter=True,
                )
                fig, ax = plot.plot_relative_directness(
                    G_graph[name],
                    order_growth,
                    show=False,
                    built=BUILT,
                    save=True,
                    close=True,
                    filepath=foldername + "/relative_directness.png",
                    x_meter=True,
                )
            for METRICNAME in ranking_func:
                metrics_dict, order_growth = growth.order_ranked_network_growth(
                    G_graph[name],
                    built=BUILT,
                    keep_connected=CONNECTED,
                    order=ORDERNAME,
                    ranking_func=ranking_func[METRICNAME],
                    save_metrics=True,
                    buff_size_metrics=BUFF_SIZE,
                )
                foldername = (
                    "./data/processed/ignored_files/utg/"
                    + name
                    + "/"
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
                with open(foldername + "/order_growth.json", "w") as f:
                    json.dump(order_growth, f)
                with open(foldername + "/metrics_growth.json", "w") as f:
                    json.dump(metrics_dict, f)
                md = {}
                md["growth"] = "ranked"
                md["built"] = BUILT
                md["keep_connected"] = CONNECTED
                md["metric"] = METRICNAME
                md["order"] = ORDERNAME
                md["buff_size"] = BUFF_SIZE
                with open(foldername + "/metadata.json", "w") as f:
                    json.dump(md, f)
                fig, ax = plot.plot_order_growth(
                    G_graph[name],
                    order_growth,
                    show=False,
                    save=True,
                    close=True,
                    filepath=foldername + "/order_growth.png",
                )
                plot.plot_growth(
                    G_graph[name],
                    order_growth,
                    foldername,
                    built=BUILT,
                    color_built="firebrick",
                    color_added="steelblue",
                    color_newest="darkgreen",
                    node_size=8,
                )
                plot.make_growth_video(
                    foldername, foldername + "/growth_video.mp4", fps=3
                )
                fig, ax = plot.plot_coverage(
                    G_graph[name],
                    order_growth,
                    show=False,
                    built=BUILT,
                    save=True,
                    close=True,
                    filepath=foldername + "/coverage.png",
                )
                fig, ax = plot.plot_directness(
                    G_graph[name],
                    order_growth,
                    show=False,
                    built=BUILT,
                    save=True,
                    close=True,
                    filepath=foldername + "/directness.png",
                    x_meter=True,
                )
                fig, ax = plot.plot_relative_directness(
                    G_graph[name],
                    order_growth,
                    show=False,
                    built=BUILT,
                    save=True,
                    close=True,
                    filepath=foldername + "/relative_directness.png",
                    x_meter=True,
                )
            foldername = (
                "./data/processed/ignored_files/utg/"
                + name
                + "/"
                + "random_trials"
                + "_"
                + ORDERNAME
            )
            if CONNECTED:
                foldername += "_connected"
            if BUILT:
                foldername += "_built"
            if not os.path.exists(foldername):
                os.makedirs(foldername)
            NUM_TRIALS = 1000
            md = {}
            md["growth"] = "ranked"
            md["built"] = BUILT
            md["keep_connected"] = CONNECTED
            md["metric"] = "random"
            md["order"] = ORDERNAME
            md["buff_size"] = BUFF_SIZE
            md["trials"] = NUM_TRIALS
            with open(foldername + "/metadata.json", "w") as f:
                json.dump(md, f)
            for i in range(NUM_TRIALS):
                metrics_dict, order_growth = growth.order_ranked_network_growth(
                    G_graph[name],
                    built=BUILT,
                    keep_connected=CONNECTED,
                    order=ORDERNAME,
                    ranking_func=metrics.growth_random,
                    save_metrics=True,
                    buff_size_metrics=BUFF_SIZE,
                )
                with open(foldername + f"/order_growth_{i:03}.json", "w") as f:
                    json.dump(order_growth, f)
                with open(foldername + f"/metrics_growth_{i:03}.json", "w") as f:
                    json.dump(metrics_dict, f)
