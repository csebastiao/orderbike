"""
Script to plot as a scatterplot the Area Under Curve for the Coverage versus the Area Under Curve for the Directness, for multiple trials for all strategies.
"""

import os
import pandas as pd
import json
from orderbike import plot
import geopandas as gpd
import momepy

if __name__ == "__main__":
    BUILT = False
    graph = "smrainet"
    folderoots = f"./data/processed/ignored_files/paper/{graph}"
    streets = gpd.read_file(
        "./data/processed/ignored_files/paper/smrainet/idf_metro.gpkg"
    )
    streets = streets.loc[streets.geometry.type == "LineString"]
    streets = streets.to_crs(streets.estimate_utm_crs())
    G = momepy.gdf_to_nx(streets, approach="primal", integer_labels=True)
    # plot.plot_graph(
    #     G,
    #     filepath=folderoots + "/picture.png",
    #     figsize=(10, 10),
    #     buffer=False,
    #     edge_color="black",
    #     edge_linewidth=4,
    #     node_color="black",
    #     node_size=200,
    #     show=False,
    #     save=True,
    #     close=True,
    # )
    df_growth = pd.read_json(str(folderoots) + "/auc_table_growth.json")
    plot_growth_folder = folderoots + "/plot_selected_growth"
    if not os.path.exists(plot_growth_folder):
        os.makedirs(plot_growth_folder)
    selected_id = []
    paddings = []
    for order in [
        "additive",
        # "subtractive",
    ]:
        for metric in [
            "coverage",
            "directness",
            "relative_directness",
            "adaptive_coverage",
            "betweenness",
            "closeness",
            "random",
        ]:
            oc = df_growth["Order"] == order
            mc = df_growth["Metric optimized"] == metric
            mincov = df_growth[oc & mc]["AUC of Coverage"].idxmin()
            maxcov = df_growth[oc & mc]["AUC of Coverage"].idxmax()
            mindir = df_growth[oc & mc]["AUC of Directness"].idxmin()
            maxdir = df_growth[oc & mc]["AUC of Directness"].idxmax()
            selected_id.append([mincov, "min_cov"])
            selected_id.append([maxcov, "max_cov"])
            selected_id.append([mindir, "min_dir"])
            selected_id.append([maxdir, "max_dir"])
    for ids, (idx, why) in enumerate(selected_id):
        if BUILT:
            add = "_built"
        else:
            add = ""
        PAD = 3
        metric, order, trialnum = df_growth.loc[idx].values[:3]
        print(metric, order, trialnum, why)
        with open(
            folderoots
            + f"/{metric}_{order}_connected"
            + add
            + f"/order_growth_{trialnum:0{PAD}}.json"
        ) as f:
            order_growth = json.load(f)
        order_growth = [tuple(val) for val in order_growth]
        with open(
            folderoots
            + f"/{metric}_{order}_connected"
            + add
            + f"/metrics_growth_{trialnum:0{PAD}}.json"
        ) as f:
            metrics_dict = json.load(f)
        foldergrowth = (
            plot_growth_folder
            + f"/{metric}_{order}_trial_{trialnum:0{PAD}}_{why}_growth_visual"
        )
        if not os.path.exists(foldergrowth):
            os.makedirs(foldergrowth)
        plot.plot_growth(
            G,
            order_growth,
            foldergrowth,
            figsize=(10, 10),
            built=BUILT,
            color_built="black",
            color_added="black",
            color_newest="black",
            buffer=False,
            plot_metrics=False,
            edge_linewidth=4,
            node_color="black",
            node_size=200,
        )
        # foldergrowth_buff = (
        #     plot_growth_folder
        #     + f"/{metric}_{order}_trial_{trialnum:0{PAD}}_{why}_growth_analysis"
        # )
        # if not os.path.exists(foldergrowth_buff):
        #     os.makedirs(foldergrowth_buff)
        # plot.plot_growth(
        #     G,
        #     order_growth,
        #     foldergrowth_buff,
        #     built=BUILT,
        #     color_built="firebrick",
        #     color_added="steelblue",
        #     color_newest="darkgreen",
        #     node_size=8,
        #     buffer=True,
        #     buff_size=152,
        #     plot_metrics=True,
        #     growth_cov=metrics_dict["coverage"],
        #     growth_xx=metrics_dict["xx"],
        #     growth_dir=metrics_dict["directness"],
        #     growth_reldir=metrics_dict["relative_directness"],
        # )
