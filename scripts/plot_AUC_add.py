# -*- coding: utf-8 -*-
"""
Plot the AUC in additive order of all strategies on the tested graphs.
"""

import os
import pandas as pd
import matplotlib as mpl
from matplotlib import pyplot as plt
import json


if __name__ == "__main__":
    with open("./scripts/plot_params_AUC_add.json", "r") as f:
        plot_params = json.load(f)
    for key in plot_params["rcparams"]:
        mpl.rcParams[key] = plot_params["rcparams"][key]
    for graphname in [
        # "grid",
        "radio_concentric",
        "grid_with_diagonal",
        "three_bridges",
    ]:
        folderoots = f"./data/processed/ignored_files/paper/{graphname}/"
        if not os.path.exists(folderoots + "plots/"):
            os.makedirs(folderoots + "plots/")
        savename = str(folderoots) + "/auc_table_growth"
        savename += ".json"
        df_growth = pd.read_json(savename)
        fig, ax = plt.subplots(figsize=plot_params["figsize"])
        add = df_growth["Order"] == "additive"
        num = 7
        if graphname == "grid":
            num += 1
        for ids, met in enumerate(plot_params["order"][:num]):
            mask = df_growth["Metric optimized"] == met
            ax.scatter(
                df_growth[add & mask]["AUC of Directness"],
                df_growth[add & mask]["AUC of Coverage"],
                **{
                    key: val[ids]
                    for key, val in plot_params.items()
                    if key not in ["dpi", "figsize", "rcparams", "order"]
                },
            )
        ax.set_axisbelow(True)
        ax.set_xlabel("AUC of Directness")
        ax.set_ylabel("AUC of Coverage")
        ax.set_aspect("equal")
        # ax.set_xlim([0.6, 0.85])
        # ax.set_ylim([0.55, 0.9])
        plt.legend()
        savename = str(folderoots) + "/plots/AUC_comparison_cov_dir_additive_square"
        savename += ".png"
        plt.savefig(savename)
        plt.close()
