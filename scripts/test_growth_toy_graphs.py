"""Script to find growth order on 3 urban toy graphs."""

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
    # 56 nodes and 91 edges
    G_graph["bridge"] = create_graph.create_bridge_graph(
        outrows=3, sscols=4, bridges=1, block_side=100, blength=300
    )
    # 49 nodes and 90 edges
    G_graph["grid_wdiagonal"] = create_graph.create_grid_graph(
        rows=7, cols=7, diagonal=True, width=100
    )
    # 49 nodes and 96 edges
    G_graph["radio_concentric"] = create_graph.create_concentric_graph(
        radial=8, zones=6, radius=100, straight_edges=True, center=True
    )
    for name in tqdm.tqdm(G_graph):
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
                "adaptative_coverage",
                "directness",
                "relative_directness",
            ]:
                metrics_dict, order_growth = growth.order_dynamic_network_growth(
                    G_graph[name],
                    built=BUILT,
                    keep_connected=CONNECTED,
                    order=ORDERNAME,
                    metric=METRICNAME,
                    progress_bar=False,
                    save_metrics=True,
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
            for i in range(1000):
                metrics_dict, order_growth = growth.order_ranked_network_growth(
                    G_graph[name],
                    built=BUILT,
                    keep_connected=CONNECTED,
                    order=ORDERNAME,
                    ranking_func=metrics.growth_random,
                    save_metrics=True,
                )
                with open(foldername + f"/order_growth_{i:03}.json", "w") as f:
                    json.dump(order_growth, f)
                with open(foldername + f"/metrics_growth_{i:03}.json", "w") as f:
                    json.dump(metrics_dict, f)
