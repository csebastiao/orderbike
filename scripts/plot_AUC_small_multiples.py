# -*- coding: utf-8 -*-
"""
Plot the AUC in additive order of all strategies on the tested graphs.
"""

import os
import pandas as pd
import matplotlib as mpl
from matplotlib import pyplot as plt
import json
from orderbike.plot import plot_graph
from utg import utils
import numpy as np


def is_pareto_efficient(x, df, fdim, sdim):
    return ~np.any(df[(df[fdim] > x[fdim]) & (df[sdim] > x[sdim])])


if __name__ == "__main__":
    folderplot = "./data/processed/ignored_files/paper/plot"
    if not os.path.exists(folderplot):
        os.makedirs(folderplot)
    with open("./scripts/plot_params_AUC_sm.json", "r") as f:
        plot_params = json.load(f)
    for key in plot_params["rcparams"]:
        mpl.rcParams[key] = plot_params["rcparams"][key]
    for exp in [True, False]:
        fig, axs = plt.subplots(
            4,
            3,
            figsize=plot_params["figsize"],
            width_ratios=[1, 3, 3],
        )
        fig.subplots_adjust(hspace=0.1, wspace=0.35)
        axs[0][1].set_title(
            "Additive growth", fontsize=plot_params["rcparams"]["font.size"] * 1.2
        )
        axs[0][2].set_title(
            "Subtractive growth", fontsize=plot_params["rcparams"]["font.size"] * 1.2
        )
        for idxg, graphname in enumerate(
            [
                "grid",
                "grid_with_diagonal",
                "three_bridges",
                "radio_concentric",
            ]
        ):
            folderoots = f"./data/processed/ignored_files/paper/{graphname}/"
            G = utils.load_graph(folderoots + "graph.graphml")
            plot_graph(
                G,
                ax=axs[idxg][0],
                edge_color="black",
                edge_linewidth=0.5,
                node_color="black",
                node_size=1.5,
                save=False,
                show=False,
                close=False,
            )
            axs[idxg][0].axis("off")
            savename = str(folderoots) + "/auc_table_growth"
            if exp:
                savename += "_expdisc"
            savename += ".json"
            df_growth = pd.read_json(savename)
            for idxo, order in enumerate(
                [
                    "additive",
                    "subtractive",
                ]
            ):
                ax = axs[idxg][idxo + 1]
                num = 7
                if graphname == "grid":
                    num += 1
                    if order == "subtractive":
                        df_growth.loc[
                            df_growth["Metric optimized"] == "manual", "Order"
                        ] = "subtractive"
                mask_ord = df_growth["Order"] == order
                for ids, met in enumerate(plot_params["order"][:num]):
                    mask_met = df_growth["Metric optimized"] == met
                    ax.scatter(
                        df_growth[mask_ord & mask_met]["AUC of Directness"],
                        df_growth[mask_ord & mask_met]["AUC of Coverage"],
                        zorder=2,
                        **{
                            key: val[ids]
                            for key, val in plot_params.items()
                            if key not in ["dpi", "figsize", "rcparams", "order"]
                        },
                    )
                ax.set(xlim=[0.4, 1.0], ylim=[0.45, 0.9])
                parfront = df_growth[mask_ord].copy()
                parfront = parfront[
                    parfront.apply(
                        lambda x: is_pareto_efficient(
                            x, parfront, "AUC of Coverage", "AUC of Directness"
                        ),
                        axis=1,
                    )
                ]
                parfront.sort_values("AUC of Directness", axis=0, inplace=True)
                ax.plot(
                    parfront["AUC of Directness"],
                    parfront["AUC of Coverage"],
                    linestyle="dashed",
                    linewidth=1,
                    color="black",
                    zorder=1,
                    label="Pareto front",
                )
        axs[0][1].legend(prop={"size": plot_params["rcparams"]["font.size"] * 0.5})
        axs[0][1].set_ylabel("AUC of coverage")
        axs[1][1].set_ylabel("AUC of coverage")
        axs[2][1].set_ylabel("AUC of coverage")
        axs[3][1].set_ylabel("AUC of coverage")
        axs[3][1].set_xlabel("AUC of directness")
        axs[3][2].set_xlabel("AUC of directness")
        for i in range(4):
            axs[i][2].set(yticklabels=[])
            if i < 3:
                axs[i][1].set(xticklabels=[])
                axs[i][2].set(xticklabels=[])
        savename = folderplot + "/AUC_small_multiples_paretofront"
        if exp:
            savename += "_expdisc"
        plt.savefig(savename)
        plt.close()
