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
    mapping = {0: "C", 1: "H", 2: "D"}
    with open("./scripts/06_plot_params_met_sm.json", "r") as f:
        plot_params = json.load(f)
    for key in plot_params["rcparams"]:
        mpl.rcParams[key] = plot_params["rcparams"][key]
    for graphname in [
        "grid",
        # "grid_2",
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
                if graphname == "grid_2":
                    add = "_built/"
                else:
                    add = "/"
                for trial in [
                    x
                    for x in Path(folderoots + f"{met}_{order}_connected" + add).glob(
                        "**/*"
                    )
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
                nrows=10, ncols=2, figsize=plot_params["figsize"], sharex="col"
            )
            axs[0][0].set_ylabel("Coverage (km$^2$)", rotation=0, y=1.2, labelpad=-30)
            axs[0][1].set_ylabel("Directness", rotation=0, y=1.2, labelpad=-30)
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
                            fontsize=plot_params["rcparams"]["font.size"],
                            transform=ax.transAxes,
                            color=plot_params["color_label"][num],
                            weight="extra bold",
                        )
                        plt.text(
                            0.3,
                            0.1,
                            "{:.3f}".format(round(auc_cov_avg[met][order], 3)),
                            ha="left",
                            va="bottom",
                            fontsize=plot_params["rcparams"]["font.size"],
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
                            "{:.3f}".format(round(auc_dir_avg[met][order], 3)),
                            ha="left",
                            va="bottom",
                            fontsize=plot_params["rcparams"]["font.size"],
                            transform=ax.transAxes,
                            color=plot_params["color_label"][num],
                            weight="extra bold",
                        )
                        ratio = 1
                    ax.set_xlim([0, xmax / 10**3])
                    for trial in [
                        x
                        for x in Path(
                            folderoots + f"{met}_{order}_connected" + add
                        ).glob("**/*")
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
            for i in range(3):
                df = pd.read_json(
                    folderoots + f"manual_additive_connected/metrics_growth_00{i}.json"
                )
                auc_cov = get_auc(
                    df["xx"],
                    df["coverage"].values,
                    zero_yaxis=False,
                    exp_discounting=False,
                )
                auc_dir = get_auc(
                    df["xx"],
                    df["directness"].values,
                    normalize_y=False,
                    exp_discounting=False,
                )
                for idx, auc in enumerate(["AUC of Coverage", "AUC of Directness"]):
                    if auc == "AUC of Coverage":
                        yy = "coverage"
                        ax = axs[7 + i][0]
                        ax.set_ylim([0, 1.5])
                        ax.set_yticks([0.0, 0.5, 1, 1.5])
                        plt.text(
                            0.95,
                            0.1,
                            f"Manual order {mapping[i]}",
                            ha="right",
                            va="bottom",
                            fontsize=plot_params["rcparams"]["font.size"],
                            transform=ax.transAxes,
                            color="black",
                            weight="extra bold",
                        )
                        plt.text(
                            0.3,
                            0.1,
                            "{:.3f}".format(round(auc_cov, 3)),
                            ha="left",
                            va="bottom",
                            fontsize=plot_params["rcparams"]["font.size"],
                            transform=ax.transAxes,
                            color="black",
                            weight="extra bold",
                        )
                        ratio = 10**6
                    else:
                        yy = "directness"
                        ax = axs[7 + i][1]
                        ax.set_ylim([0.4, 1])
                        ax.set_yticks([0.4, 0.6, 0.8, 1])
                        plt.text(
                            0.8,
                            0.1,
                            "{:.3f}".format(round(auc_dir, 3)),
                            ha="left",
                            va="bottom",
                            fontsize=plot_params["rcparams"]["font.size"],
                            transform=ax.transAxes,
                            color="black",
                            weight="extra bold",
                        )
                        ratio = 1
                    ax.set_xlim([0, xmax / 10**3])
                    ax.plot(
                        df["xx"] / 10**3,
                        df[yy] / ratio,
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
            axs[9][0].set_xlabel("Built length (km)")
            axs[9][1].set_xlabel("Built length (km)")
            axs[9][0].set_xlim([0, xmax / 10**3])
            axs[9][1].set_xlim([0, xmax / 10**3])
            savename = folderplot + f"/sm_all_{order}_average_wmanual"
            plt.savefig(savename + ".png")
            plt.close()
