# -*- coding: utf-8 -*-
"""
Script plot on the same figure the AUC of coverage and directness for the medoid of all strategies for the distorted grids and the perfect grid.
"""

import pandas as pd
import matplotlib as mpl
from matplotlib import pyplot as plt
import json
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
    with open("./scripts/09_plot_params_AUC_dg.json", "r") as f:
        plot_params = json.load(f)
    for key in plot_params["rcparams"]:
        mpl.rcParams[key] = plot_params["rcparams"][key]
    for order in ["additive", "subtractive"]:
        fig, ax = plt.subplots(figsize=plot_params["figsize"])
        ax.set_xlabel("AUC of directness")
        ax.set_ylabel("AUC of coverage")
        plt.axis("square")
        # Set rounded limits at smallest and highest 0.1
        plt.legend(prop={"size": plot_params["rcparams"]["font.size"] * 0.75})
        for i in range(5):
            folderoots = f"data/processed/ignored_files/utg_distorted_grids/dg_{i}"
            df_growth = pd.read_json(folderoots + "/auc_table_growth.json")
            df_growth["Graph"] = f"Distorted_{i}"
            mask_ord = df_growth["Order"] == order
            for idx, met in enumerate(plot_params["order"][:7]):
                mask_met = df_growth["Metric optimized"] == met
                arr = [
                    val
                    for val in zip(
                        df_growth[mask_ord & mask_met]["AUC of Coverage"].values,
                        df_growth[mask_ord & mask_met]["AUC of Directness"].values,
                    )
                ]
                medoid = find_medoid(arr)
                mask_trial = df_growth["Trial"] == medoid
                if idx == 0:
                    df_med = df_growth[mask_ord & mask_met & mask_trial]
                else:
                    df_med = pd.concat(
                        [df_med, df_growth[mask_ord & mask_met & mask_trial]]
                    )
            if i == 0:
                df_med_all = df_med
            else:
                df_med_all = pd.concat([df_med_all, df_med])
        for idx, met in enumerate(plot_params["order"][:7]):
            mask_ord = df_med_all["Order"] == order
            mask_met = df_med_all["Metric optimized"] == met
            ax.scatter(
                df_med_all[mask_met & mask_ord]["AUC of Directness"],
                df_med_all[mask_met & mask_ord]["AUC of Coverage"],
                zorder=1,
                alpha=0.3,
                **{
                    key: val[idx]
                    for key, val in plot_params.items()
                    if key not in ["dpi", "figsize", "rcparams", "order", "label"]
                },
            )
        folderoots = "./data/processed/ignored_files/paper/grid"
        df_growth = pd.read_json(folderoots + "/auc_table_growth.json")
        mask_ord = df_growth["Order"] == order
        for idx, met in enumerate(plot_params["order"][:7]):
            mask_met = df_growth["Metric optimized"] == met
            arr = [
                val
                for val in zip(
                    df_growth[mask_ord & mask_met]["AUC of Coverage"].values,
                    df_growth[mask_ord & mask_met]["AUC of Directness"].values,
                )
            ]
            medoid = find_medoid(arr)
            mask_trial = df_growth["Trial"] == medoid
            df_med = df_growth[mask_ord & mask_met & mask_trial]
            ax.scatter(
                df_med["AUC of Directness"],
                df_med["AUC of Coverage"],
                zorder=2,
                alpha=1,
                **{
                    key: val[idx]
                    for key, val in plot_params.items()
                    if key not in ["dpi", "figsize", "rcparams", "order"]
                },
            )
        plt.legend(prop={"size": plot_params["rcparams"]["font.size"] * 0.75})
        dirmin = df_med_all["AUC of Directness"].min()
        dirmax = df_med_all["AUC of Directness"].max()
        covmin = df_med_all["AUC of Coverage"].min()
        covmax = df_med_all["AUC of Coverage"].max()
        mmin = round(min(dirmin, covmin) - 0.05, 1)
        mmax = round(max(dirmax, covmax) + 0.05, 1)
        ax.set_xlim([mmin, mmax])
        ax.set_ylim([mmin, mmax])
        loc = mpl.ticker.MultipleLocator(base=0.1)
        ax.xaxis.set_major_locator(loc)
        ax.yaxis.set_major_locator(loc)
        plt.savefig(
            f"data/processed/ignored_files/utg_distorted_grids/AUC_{order}", dpi=400
        )
        plt.close()
