# -*- coding: utf-8 -*-
"""
Script to plot multiple strategies of same graph compared on the same metrics, with specific comparison for random trials.
"""

import os
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

if __name__ == "__main__":
    PAD = 3
    for graphname in [
        # "utg_grid_trials",
        # "utg_radio_concentric_trials",
        # "utg_three_bridges_trials",
        "utg_diagonal_grid_trials",
    ]:
        folderoots = f"./data/processed/ignored_files/{graphname}/"
        if not os.path.exists(folderoots + "plots/"):
            os.makedirs(folderoots + "plots/")
        sns.set_theme(style="whitegrid")
        hue_order = [
            "coverage",
            "adaptive_coverage",
            "directness",
            "relative_directness",
            "betweenness",
            "closeness",
            "random",
        ]
        if graphname == "utg_grid_trials":
            hue_order.append("manual")
        # Create color palette, need 7 colors in 2 hues !!! Impossible to make pretty with everything
        add_colors = sns.color_palette("bright")[: len(hue_order)]
        sub_colors = sns.color_palette("deep")[: len(hue_order)]
        color_palette = [
            item for sublist in zip(add_colors, sub_colors) for item in sublist
        ]
        # With and without exponential discounting
        for exp_disc in [True, False]:
            savename = str(folderoots) + "/auc_table_growth"
            if exp_disc:
                savename += "_expdisc"
            savename += ".json"
            df_growth = pd.read_json(savename)
            for auc in ["AUC of Coverage", "AUC of Directness"]:
                fig, ax = plt.subplots(figsize=(16, 9))
                idx = 0
                if auc == "AUC of Coverage":
                    yy = "coverage"
                else:
                    yy = "directness"
                ax.set_ylabel(auc[7:])
                for met in set(df_growth["Metric optimized"]):
                    for order in ["additive", "subtractive"]:
                        chosen = max(
                            df_growth[
                                (df_growth["Metric optimized"] == met)
                                & (df_growth["Order"] == order)
                            ][auc]
                        )
                        trial = df_growth[df_growth[auc] == chosen]["Trial"].values[0]
                        df = pd.read_json(
                            folderoots
                            + f"{met}_{order}_connected/metrics_growth_{int(trial):0{PAD}}.json"
                        )
                        if order == "additive":
                            markerstyle = "P"
                        else:
                            markerstyle = "o"
                        ax.plot(
                            df["xx"],
                            df[yy],
                            color=color_palette[idx],
                            label=met,
                            marker=markerstyle,
                            alpha=0.9,
                            markersize=5,
                        )
                        idx += 1

                ax.set_xlabel("Meters built")
                plt.tight_layout()
                plt.legend()
                plt.savefig(folderoots + f"/plots/{yy}_lineplot.png", dpi=300)
                plt.close()
