"""
Script to plot as a scatterplot the Area Under Curve for the Coverage versus the Area Under Curve for the Directness, for multiple trials for all strategies.
"""

import os
import json
import pandas as pd
from utg import utils
from orderbike import plot

if __name__ == "__main__":
    folderoots = "./data/processed/ignored_files/utg_milan_bikenet/"
    G = utils.load_graph(folderoots + "/graph.graphml")
    df_growth = pd.read_json(str(folderoots) + "/auc_table_growth.json")
    plot_growth_folder = folderoots + "/plot_selected_growth"
    if not os.path.exists(plot_growth_folder):
        os.makedirs(plot_growth_folder)
    selected_id = []
    paddings = []
    PAD = 3
    for order in ["additive", "subtractive"]:
        for metric in [
            "random",
            "coverage",
            "betweenness",
            "closeness",
            "directness",
            "relative_directness",
            "adaptive_coverage",
        ]:
            oc = df_growth["Order"] == order
            mc = df_growth["Metric optimized"] == metric
            # paddings.append(len(str(len(df_growth[oc & mc]) - 1)))
            # paddings.append(len(str(len(df_growth[oc & mc]) - 1)))
            # paddings.append(len(str(len(df_growth[oc & mc]) - 1)))
            # paddings.append(len(str(len(df_growth[oc & mc]) - 1)))
            mincov = df_growth[oc & mc]["AUC of Coverage"].idxmin()
            maxcov = df_growth[oc & mc]["AUC of Coverage"].idxmax()
            mindir = df_growth[oc & mc]["AUC of Directness"].idxmin()
            maxdir = df_growth[oc & mc]["AUC of Directness"].idxmax()
            selected_id.append(
                [
                    mincov,
                    "min_cov",
                ]
            )
            selected_id.append([maxcov, "max_cov"])
            selected_id.append([mindir, "min_dir"])
            selected_id.append([maxdir, "max_dir"])
    for ids, (idx, why) in enumerate(selected_id):
        # PAD = paddings[ids]
        metric, order, trialnum = df_growth.loc[idx].values[:3]
        with open(
            folderoots
            + f"/{metric}_{order}_connected/order_growth_{trialnum:0{PAD}}.json"
        ) as f:
            order_growth = json.load(f)
        order_growth = [tuple(val) for val in order_growth]
        with open(
            folderoots
            + f"/{metric}_{order}_connected/metrics_growth_{trialnum:0{PAD}}.json"
        ) as f:
            metrics_dict = json.load(f)
        foldergrowth_buff = (
            plot_growth_folder
            + f"/{metric}_{order}_trial_{trialnum:0{PAD}}_{why}_growth_buffer"
        )
        if not os.path.exists(foldergrowth_buff):
            os.makedirs(foldergrowth_buff)
        plot.plot_growth(
            G,
            order_growth,
            foldergrowth_buff,
            built=False,
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
