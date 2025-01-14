# -*- coding: utf-8 -*-
"""
Plot the metrics in additive order of all strategies on the tested graphs, chosing the medoid in AUC of Coverage and Directness as the shown trial.
"""

import os
from pathlib import Path
import pandas as pd
import json
import matplotlib as mpl
from matplotlib import pyplot as plt


def average_x(df):
    arr = []
    for val in sorted(set(df["xx"].values)):
        arr.append(df[df["xx"] == val].mean())
    return arr


if __name__ == "__main__":
    PAD = 3
    with open("./scripts/plot_params_met_all.json", "r") as f:
        plot_params = json.load(f)
    for key in plot_params["rcparams"]:
        mpl.rcParams[key] = plot_params["rcparams"][key]
    for graphname in [
        "grid",
        # "radio_concentric",
        # "grid_with_diagonal",
        # "three_bridges",
    ]:
        folderoots = f"./data/processed/ignored_files/paper/{graphname}/"
        folderplot = folderoots + "plots/lineplot"
        if not os.path.exists(folderplot):
            os.makedirs(folderplot)
        savename = str(folderoots) + "/auc_table_growth.json"
        df_growth = pd.read_json(savename)
        avg = {}
        for met in plot_params["order"][:7]:
            avg[met] = {}
            df_concat = pd.DataFrame()
            for order in ["additive", "subtractive"]:
                for trial in [
                    x
                    for x in Path(folderoots + f"{met}_{order}_connected/").glob("**/*")
                    if "metrics_growth" in str(x)
                ]:
                    df = pd.read_json(trial)
                    df_concat = pd.concat([df_concat, df])
                avg[met][order] = pd.DataFrame(average_x(df_concat))
        for order in ["additive", "subtractive"]:
            fig, axs = plt.subplots(
                2, 1, figsize=(plot_params["figsize"][0], plot_params["figsize"][1] * 2)
            )
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
            for auc in ["AUC of Coverage", "AUC of Directness"]:
                idx = 0
                if auc == "AUC of Coverage":
                    ax = axs[0]
                    yy = "coverage"
                    ax.set_ylabel("Coverage ($km^2$)")
                    ax.axes.xaxis.set_ticklabels([])
                    ratio = 10**6
                else:
                    ax = axs[1]
                    yy = "directness"
                    ax.set_ylabel("Directness")
                    ratio = 1
                    ax.set_xlabel("Built length ($km$)")
                ax.set_xlim([0, max(df["xx"]) / 10**3])
                for ids, met in enumerate(plot_params["order"][:7]):
                    df = avg[met][order]
                    ax.plot(
                        df["xx"] / 10**3,
                        df[yy] / ratio,
                        **{
                            key: val[ids]
                            for key, val in plot_params.items()
                            if key not in ["dpi", "figsize", "rcparams", "order"]
                        },
                    )
            axs[0].legend()
            ax.set_axisbelow(True)
            plt.tight_layout()
            plt.savefig(folderplot + f"/lineplot_{order}_average_merged.png")
            plt.close()
