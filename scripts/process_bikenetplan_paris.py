"""Script to find growth order on Paris bikeplan."""
# STILL NEED TO CHECK IF WORKING WITH MULTIGRAPH

import os
import json
from utg import utils as utgut
from orderbike import growth, plot

if __name__ == "__main__":
    BUILT = True
    CONNECTED = True
    ORDERNAME = "subtractive"
    METRICNAME = "coverage"
    kwargs = {}
    G = utgut.load_graph("./data/processed/plan_paris/paris_bikeplan_graph.graphml")
    order_growth = growth.order_dynamic_network_growth(
        G,
        built=BUILT,
        keep_connected=CONNECTED,
        order=ORDERNAME,
        metric=METRICNAME,
        progress_bar=True,
        **kwargs,
    )
    foldername = (
        "./data/processed/plan_paris/ignored_growth/graph/"
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
    utgut.save_graph(G, foldername + "/toy_graph.graphml")
    plot.plot_growth(
        G,
        order_growth,
        foldername,
        built=BUILT,
        color_built="firebrick",
        color_added="steelblue",
        color_newest="darkgreen",
        node_size=8,
    )
    plot.make_growth_video(foldername, foldername + "/growth_video.mp4", fps=3)
    fig, ax = plot.plot_coverage(
        G,
        order_growth,
        show=False,
        save=True,
        close=True,
        filepath=foldername + "/coverage.png",
    )
    fig, ax = plot.plot_directness(
        G,
        order_growth,
        show=False,
        save=True,
        close=True,
        filepath=foldername + "/directness.png",
        x_meter=True,
    )
