# -*- coding: utf-8 -*-
"""
Plot the metrics in additive order of all strategies on the tested graphs, chosing the medoid in AUC of Coverage and Directness as the shown trial.
"""

import os
import pandas as pd
import json
import matplotlib as mpl
from matplotlib import pyplot as plt
import numpy as np


def find_medoid(array):
    "Find the medoid of a list of points in 2D. Array of shape [[x1, y1], [x2, y2], ..., [xn, yn]]."
    array = np.array(array)
    dist_mat = np.array(
        [
            [np.linalg.norm([array[col] - array[row]]) for col in range(len(array))]
            for row in range(len(array))
        ]
    )
    return np.argmin(dist_mat.sum(axis=0))


if __name__ == "__main__":
    PAD = 3
    with open("./scripts/plot_params_met_all.json", "r") as f:
        plot_params = json.load(f)
    for key in plot_params["rcparams"]:
        mpl.rcParams[key] = plot_params["rcparams"][key]
    for graphname in [
        "grid",
        "radio_concentric",
        "grid_with_diagonal",
        "three_bridges",
    ]:
        folderoots = f"./data/processed/ignored_files/paper/{graphname}/"
        folderplot = folderoots + "plots/lineplot"
        if not os.path.exists(folderplot):
            os.makedirs(folderplot)
        savename = str(folderoots) + "/auc_table_growth.json"
        df_growth = pd.read_json(savename)
        for order in ["additive", "subtractive"]:
            trial_dict = {}
            for met in plot_params["order"][:7]:
                mask = (df_growth["Metric optimized"] == met) & (
                    df_growth["Order"] == order
                )
                arr = [
                    val
                    for val in zip(
                        df_growth[mask]["AUC of Coverage"].values,
                        df_growth[mask]["AUC of Directness"].values,
                    )
                ]
                medoid = find_medoid(arr)
                trial_dict[met] = medoid
            for auc in ["AUC of Coverage", "AUC of Directness"]:
                fig, ax = plt.subplots(figsize=plot_params["figsize"])
                idx = 0
                if auc == "AUC of Coverage":
                    yy = "coverage"
                    ax.set_ylabel("Coverage ($m^2$)")
                else:
                    yy = "directness"
                    ax.set_ylabel("Directness")
                for ids, met in enumerate(plot_params["order"][:7]):
                    df = pd.read_json(
                        folderoots
                        + f"{met}_{order}_connected/metrics_growth_{int(trial_dict[met]):0{PAD}}.json"
                    )
                    ax.plot(
                        df["xx"],
                        df[yy],
                        **{
                            key: val[ids]
                            for key, val in plot_params.items()
                            if key not in ["dpi", "figsize", "rcparams", "order"]
                        },
                    )
                ax.set_xlabel("Meters built ($m$)")
                ax.set_axisbelow(True)
                plt.tight_layout()
                plt.legend()
                plt.savefig(folderplot + f"/{yy}_lineplot_{order}.png")
                plt.close()
