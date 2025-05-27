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
from pathlib import Path


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
    with open("./scripts/plot_params_met_sm.json", "r") as f:
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
        folderplot = folderoots + "plots/small_multiples"
        if not os.path.exists(folderplot):
            os.makedirs(folderplot)
        dirmin = 1
        dirmax = 0
        for met in plot_params["order"][:7]:
            for order in [
                "additive",
                "subtractive",
            ]:
                for trial in [
                    x
                    for x in Path(folderoots + f"{met}_{order}_connected/").glob("**/*")
                    if "metrics_growth" in str(x)
                ]:
                    df = pd.read_json(trial)
                    dirmin_temp = df["directness"].min()
                    if dirmin_temp < dirmin:
                        dirmin = dirmin_temp
                    dirmax_temp = df["directness"].max()
                    if dirmax_temp > dirmax:
                        dirmax = dirmax_temp
        xmax = df["xx"].max() * 1.1
        dirmin = round(dirmin - 0.05, 1)
        dirmax = round(dirmax + 0.05, 1)
        savename = str(folderoots) + "/auc_table_growth.json"
        df_growth = pd.read_json(savename)
        for order in ["additive", "subtractive"]:
            med_dict = {}
            fig, axs = plt.subplots(
                nrows=7, ncols=2, figsize=plot_params["figsize"], sharex="col"
            )
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
                med_dict[met] = medoid
            for auc in ["AUC of Coverage", "AUC of Directness"]:
                for num, met in enumerate(plot_params["order"][:7]):
                    if auc == "AUC of Coverage":
                        yy = "coverage"
                        ax = axs[num][0]
                        ax.set_ylabel("Coverage ($km^2$)")
                        plt.text(
                            0.85,
                            0.25,
                            plot_params["label_met"][num],
                            ha="right",
                            va="bottom",
                            fontsize="medium",
                            transform=ax.transAxes,
                            color=plot_params["color_label"][num],
                            weight="extra bold",
                        )
                        ratio = 10**6
                    else:
                        yy = "directness"
                        ax = axs[num][1]
                        ax.set_ylabel("Directness")
                        ax.set_ylim([dirmin, dirmax])
                        ratio = 1
                    for trial in [
                        x
                        for x in Path(folderoots + f"{met}_{order}_connected/").glob(
                            "**/*"
                        )
                        if "metrics_growth" in str(x)
                    ]:
                        df = pd.read_json(trial)
                        trial_num = int(str(trial.stem).split("_")[-1])
                        if trial_num == med_dict[met]:
                            ax.plot(
                                df["xx"] / 10**3,
                                df[yy] / ratio,
                                label="Medoid",
                                **{
                                    key: val[0]
                                    for key, val in plot_params.items()
                                    if key
                                    not in [
                                        "figsize",
                                        "rcparams",
                                        "order",
                                        "label_met",
                                        "color_label",
                                    ]
                                },
                            )
                        else:
                            ax.plot(
                                df["xx"] / 10**3,
                                df[yy] / ratio,
                                **{
                                    key: val[1]
                                    for key, val in plot_params.items()
                                    if key
                                    not in [
                                        "figsize",
                                        "rcparams",
                                        "order",
                                        "label_met",
                                        "color_label",
                                    ]
                                },
                            )
            axs[6][0].set_xlabel("Kilometers built ($km$)")
            axs[6][1].set_xlabel("Kilometers built ($km$)")
            axs[6][0].set_xlim([0, xmax / 10**3])
            axs[6][1].set_xlim([0, xmax / 10**3])
            axs[0][1].legend()
            plt.savefig(folderplot + f"/sm_all_{order}_medoid.png")
            plt.close()
