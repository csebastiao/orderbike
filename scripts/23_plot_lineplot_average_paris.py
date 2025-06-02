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
    for ind in set(df.index):
        arr.append(df[df.index == ind].mean())
    return arr


if __name__ == "__main__":
    PAD = 3
    with open("./scripts/23_plot_params_met_all_paris.json", "r") as f:
        plot_params = json.load(f)
    for key in plot_params["rcparams"]:
        mpl.rcParams[key] = plot_params["rcparams"][key]
    folderoots = "./data/processed/ignored_files/results_paris/"
    folderplot = folderoots + "plots/lineplot"
    if not os.path.exists(folderplot):
        os.makedirs(folderplot)
    savename = str(folderoots) + "/auc_table_growth.json"
    df_growth = pd.read_json(savename)
    avg = {}
    for met in plot_params["order"][:7]:
        avg[met] = {}
        df_concat = pd.DataFrame()
        for order in [
            "additive",
            # "subtractive",
        ]:
            if met == "random":
                for trial in [
                    x
                    for x in Path(folderoots + f"{met}_{order}_connected_built/").glob(
                        "**/*"
                    )
                    if "metrics_growth" in str(x)
                ]:
                    df = pd.read_json(trial)
                    df_concat = pd.concat([df_concat, df])
                avg[met][order] = pd.DataFrame(average_x(df_concat))
            else:
                avg[met][order] = pd.read_json(
                    folderoots + f"{met}_{order}_connected_built/metrics_growth.json"
                )
    for order in [
        "additive",
        # "subtractive",
    ]:
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
        mapping = {
            "AUC of Coverage": {
                "yy": "coverage",
                "label": "Coverage ($km^2$)",
                "ratio": 10**6,
            },
            "AUC of Directness": {
                "yy": "directness",
                "label": "Directness",
                "ratio": 1,
            },
            "Number of CC": {
                "yy": "num_cc",
                "label": "Number of CC",
                "ratio": 1,
            },
            "Length of LCC": {
                "yy": "length_lcc",
                "label": "Length of LCC",
                "ratio": 1,
            },
        }
        for auc in list(mapping):
            fig, ax = plt.subplots(figsize=plot_params["figsize"])
            idx = 0
            yy = mapping[auc]["yy"]
            ax.set_ylabel(mapping[auc]["label"])
            ratio = mapping[auc]["ratio"]
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
            ax.set_xlabel("Built length ($km$)")
            ax.set_axisbelow(True)
            plt.tight_layout()
            plt.legend()
            plt.savefig(folderplot + f"/{yy}_lineplot_{order}_average.png")
            plt.close()
