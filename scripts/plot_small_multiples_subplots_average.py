# -*- coding: utf-8 -*-
"""
Plot the metrics in additive order of all strategies on the tested graphs, chosing the medoid in AUC of Coverage and Directness as the shown trial.
"""

import os
import pandas as pd
import json
import matplotlib as mpl
from matplotlib import pyplot as plt
from pathlib import Path
from orderbike.utils import get_auc


def average_x(df):
    arr = []
    for ind in set(df.index):
        arr.append(df[df.index == ind].mean())
    return arr


if __name__ == "__main__":
    PAD = 3
    with open("./scripts/plot_params_met_sm.json", "r") as f:
        plot_params = json.load(f)
    for key in plot_params["rcparams"]:
        mpl.rcParams[key] = plot_params["rcparams"][key]
    for graphname in [
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
        avg = {}
        auc_cov_avg = {}
        auc_dir_avg = {}
        for met in plot_params["order"][:7]:
            avg[met] = {}
            auc_cov_avg[met] = {}
            auc_dir_avg[met] = {}
            df_concat = pd.DataFrame()
            for order in ["additive", "subtractive"]:
                for trial in [
                    x
                    for x in Path(folderoots + f"{met}_{order}_connected/").glob("**/*")
                    if "metrics_growth" in str(x)
                ]:
                    df = pd.read_json(trial)
                    df_concat = pd.concat([df_concat, df])
                    dirmin_temp = df["directness"].min()
                    if dirmin_temp < dirmin:
                        dirmin = dirmin_temp
                    dirmax_temp = df["directness"].max()
                    if dirmax_temp > dirmax:
                        dirmax = dirmax_temp
                avg[met][order] = pd.DataFrame(average_x(df_concat))
                auc_cov_avg[met][order] = get_auc(
                    df["xx"],
                    avg[met][order]["coverage"].values,
                    zero_yaxis=False,
                    exp_discounting=False,
                )
                auc_dir_avg[met][order] = get_auc(
                    df["xx"],
                    avg[met][order]["directness"].values,
                    normalize_y=False,
                    exp_discounting=False,
                )
        xmax = df["xx"].max()
        savename = str(folderoots) + "/auc_table_growth.json"
        df_growth = pd.read_json(savename)
        for order in ["additive", "subtractive"]:
            med_dict = {}
            fig, axs = plt.subplots(
                nrows=7, ncols=2, figsize=plot_params["figsize"], sharex="col"
            )
            axs[0][0].set_ylabel("Coverage (km$^2$)", rotation=0, y=1.2)
            axs[0][1].set_ylabel("Directness", rotation=0, y=1.2)
            for auc in ["AUC of Coverage", "AUC of Directness"]:
                for num, met in enumerate(plot_params["order"][:7]):
                    if auc == "AUC of Coverage":
                        yy = "coverage"
                        ax = axs[num][0]
                        ax.set_ylim([0, 1.5])
                        ax.set_yticks([0.0, 0.5, 1, 1.5])
                        plt.text(
                            0.95,
                            0.1,
                            plot_params["label_met"][num],
                            ha="right",
                            va="bottom",
                            fontsize="medium",
                            transform=ax.transAxes,
                            color=plot_params["color_label"][num],
                            weight="extra bold",
                        )
                        plt.text(
                            0.3,
                            0.1,
                            round(auc_cov_avg[met][order], 3),
                            ha="left",
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
                        ax.set_ylim([0.4, 1])
                        ax.set_yticks([0.4, 0.6, 0.8, 1])
                        plt.text(
                            0.8,
                            0.1,
                            round(auc_dir_avg[met][order], 3),
                            ha="left",
                            va="bottom",
                            fontsize="medium",
                            transform=ax.transAxes,
                            color=plot_params["color_label"][num],
                            weight="extra bold",
                        )
                        ratio = 1
                    ax.set_xlim([0, xmax / 10**3])
                    for trial in [
                        x
                        for x in Path(folderoots + f"{met}_{order}_connected/").glob(
                            "**/*"
                        )
                        if "metrics_growth" in str(x)
                    ]:
                        df = pd.read_json(trial)
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
                                    "label",
                                    "color_label",
                                ]
                            },
                        )
                    ax.plot(
                        avg[met][order]["xx"] / 10**3,
                        avg[met][order][yy] / ratio,
                        label="Average",
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
            axs[6][0].set_xlabel("Built length (km)")
            axs[6][1].set_xlabel("Built length (km)")
            axs[6][0].set_xlim([0, xmax / 10**3])
            axs[6][1].set_xlim([0, xmax / 10**3])
            savename = folderplot + f"/sm_all_{order}_average"
            plt.savefig(savename + ".png")
            plt.close()
