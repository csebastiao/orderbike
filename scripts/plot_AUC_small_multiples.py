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
            4, 3, figsize=plot_params["figsize"], width_ratios=[1, 3, 3]
        )
        fig.subplots_adjust(hspace=0.2, wspace=0.4)
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
                        **{
                            key: val[ids]
                            for key, val in plot_params.items()
                            if key not in ["dpi", "figsize", "rcparams", "order"]
                        },
                    )
                # if order == "additive":
                # plt.text(
                #     0.3,
                #     0.1,
                #     " ".join(graphname.split("_")).capitalize(),
                #     ha="left",
                #     va="bottom",
                #     fontsize="large",
                #     transform=ax.transAxes,
                #     color="black",
                #     weight="extra bold",
                # )
                ax.set(xlim=[0.4, 1.0], ylim=[0.5, 0.9])
        axs[0][1].legend(prop={"size": plot_params["rcparams"]["font.size"] * 0.5})
        axs[0][1].set_ylabel("AUC of Coverage")
        axs[1][1].set_ylabel("AUC of Coverage")
        axs[2][1].set_ylabel("AUC of Coverage")
        axs[3][1].set_ylabel("AUC of Coverage")
        axs[3][1].set_xlabel("AUC of Directness")
        axs[3][2].set_xlabel("AUC of Directness")
        savename = folderplot + "/AUC_small_multiples"
        if exp:
            savename += "_expdisc"
        plt.savefig(savename)
        plt.close()
