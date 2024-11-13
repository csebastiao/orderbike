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
    with open("./scripts/plot_params_met_sm_add.json", "r") as f:
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
        if not os.path.exists(folderoots + "plots/"):
            os.makedirs(folderoots + "plots/")
        savename = str(folderoots) + "/auc_table_growth.json"
        df_growth = pd.read_json(savename)
        trial_dict = {}
        for met in plot_params["order"][:7]:
            mask = (df_growth["Metric optimized"] == met) & (
                df_growth["Order"] == "additive"
            )
            arr = [
                val
                for val in zip(
                    df_growth[mask]["AUC of Coverage"].values,
                    df_growth[mask]["AUC of Directness"].values,
                )
            ]
            medoid = find_medoid(arr)
            max_cov = max(df_growth[mask]["AUC of Coverage"].values)
            min_cov = min(df_growth[mask]["AUC of Coverage"].values)
            best_cov = df_growth.iloc[
                df_growth[df_growth["AUC of Coverage"] == max_cov][
                    "AUC of Directness"
                ].idxmax()
            ]["Trial"]
            worst_cov = df_growth.iloc[
                df_growth[df_growth["AUC of Coverage"] == min_cov][
                    "AUC of Directness"
                ].idxmax()
            ]["Trial"]
            trial_dict[met] = {
                "medoid": medoid,
                "best_cov": best_cov,
                "worst_cov": worst_cov,
            }
        for auc in ["AUC of Coverage", "AUC of Directness"]:
            for met in plot_params["order"][:7]:
                fig, ax = plt.subplots(figsize=plot_params["figsize"])
                ax.set_axisbelow(True)
                if auc == "AUC of Coverage":
                    yy = "coverage"
                    ax.set_ylabel("Coverage ($m^2$)")
                else:
                    yy = "directness"
                    ax.set_ylabel("Directness")
                for trial in [
                    x
                    for x in Path(folderoots + f"{met}_additive_connected/").glob(
                        "**/*"
                    )
                    if "metrics_growth" in str(x)
                ]:
                    df = pd.read_json(trial)
                    idx = 3
                    trial_num = int(str(trial.stem).split("_")[-1])
                    if trial_num == trial_dict[met]["best_cov"]:
                        idx = 0
                    elif trial_num == trial_dict[met]["worst_cov"]:
                        idx = 1
                    elif trial_num == trial_dict[met]["medoid"]:
                        idx = 2
                    if idx < 3:
                        ax.plot(
                            df["xx"],
                            df[yy],
                            **{
                                key: val[idx]
                                for key, val in plot_params.items()
                                if key not in ["figsize", "rcparams", "order"]
                            },
                        )
                    else:
                        ax.plot(
                            df["xx"],
                            df[yy],
                            **{
                                key: val[idx]
                                for key, val in plot_params.items()
                                if key not in ["figsize", "rcparams", "order", "label"]
                            },
                        )
                if trial_dict[met]["best_cov"] == trial_dict[met]["worst_cov"]:
                    ax.plot(
                        df["xx"],
                        df[yy],
                        **{
                            key: val[1]
                            for key, val in plot_params.items()
                            if key not in ["figsize", "rcparams", "order"]
                        },
                    )
                if (trial_dict[met]["best_cov"] == trial_dict[met]["medoid"]) or (
                    trial_dict[met]["worst_cov"] == trial_dict[met]["medoid"]
                ):
                    ax.plot(
                        df["xx"],
                        df[yy],
                        **{
                            key: val[2]
                            for key, val in plot_params.items()
                            if key not in ["figsize", "rcparams", "order"]
                        },
                    )
                ax.set_xlabel("Meters built ($m$)")
                plt.tight_layout()
                plt.legend()
                plt.savefig(folderoots + f"/plots/sm_{yy}_lineplot_{met}_additive.png")
                plt.close()
