"""
Script to plot as a scatterplot the Area Under Curve for the Coverage versus the Area Under Curve for the Directness, for multiple trials for all strategies.
"""

import os
import pathlib
import json
import pandas as pd
import seaborn as sns
import numpy as np
from matplotlib import pyplot as plt
from sklearn.metrics import auc


def get_auc(xx, yy, normalize_x=True, normalize_y=True, zero_yaxis=True):
    if normalize_x:
        xx = (np.array(xx) - np.min(xx)) / (np.max(xx) - np.min(xx))
    if normalize_y:
        if zero_yaxis:
            min_y = 0
        else:
            min_y = np.min(yy)
        yy = (np.array(yy) - min_y) / (np.max(yy) - min_y)
    return auc(xx, yy)


def auc_from_metrics_dict(met_dict, met, **kwargs):
    xx = met_dict["xx"]
    yy = met_dict[met]
    return get_auc(xx, yy, **kwargs)


if __name__ == "__main__":
    for i in range(4, 5):
        folderoots = f"./data/processed/ignored_files/utg_distorted_grids/dg_{i}/"
        if not os.path.exists(folderoots + "plots/"):
            os.makedirs(folderoots + "plots/")
        sns.set_theme(style="whitegrid")
        # Open for all toy graphs
        toy_graph_aucs = []
        # Open for all growth strategies for a toy graph
        for growth_f in [
            fold
            for fold in pathlib.Path(folderoots).iterdir()
            if not fold.is_file()
            and "plot" not in str(fold)
            and ".DS_Store" not in str(fold)
        ]:
            growthname = str(growth_f).split("/")[-1].removesuffix("_connected")
            if "additive" in growthname:
                order = "additive"
            elif "subtractive" in growthname:
                order = "subtractive"
            met_name = "_".join(growthname.split("_")[:-1])
            for trial in sorted(
                [
                    fold
                    for fold in pathlib.Path(growth_f).iterdir()
                    if "metric" in str(fold)
                ]
            ):
                trialnum = (
                    str(trial).split("/")[-1].split("_")[-1].removesuffix(".json")
                )
                with open(trial, "r") as f:
                    met_dict = json.load(f)
                auc_cov = auc_from_metrics_dict(
                    met_dict, "coverage", normalize_y=True, zero_yaxis=False
                )
                auc_dir = auc_from_metrics_dict(
                    met_dict, "directness", normalize_y=False
                )
                auc_reldir = auc_from_metrics_dict(
                    met_dict, "relative_directness", normalize_y=False
                )
                # Add to the table the length of lcc when using true graph with built part, and don't start with zero_yaxis=True for AUC
                toy_graph_aucs.append(
                    [met_name, order, trialnum, auc_cov, auc_dir, auc_reldir]
                )
        # Save everything as JSON with Pandas Dataframe
        df_growth = pd.DataFrame(
            toy_graph_aucs,
            columns=[
                "Metric optimized",
                "Order",
                "Trial",
                "AUC of Coverage",
                "AUC of Directness",
                "AUC of Relative Directness",
            ],
        )
        df_growth.to_json(str(folderoots) + "/auc_table_growth.json")
        df_growth = pd.read_json(str(folderoots) + "/auc_table_growth.json")
        fig, ax = plt.subplots(figsize=(16, 9))
        ax.set_title("Growth strategies, AUC comparison")
        g = sns.scatterplot(
            df_growth,
            x="AUC of Directness",
            y="AUC of Coverage",
            hue="Metric optimized",
            hue_order=[
                "coverage",
                "adaptive_coverage",
                "directness",
                "relative_directness",
                "betweenness",
                "closeness",
                "random",
                "manual",
            ],
            style="Order",
            markers=["P", "o"],
            style_order=["additive", "subtractive"],
            palette=sns.color_palette("deep")[:8],
            ax=ax,
            s=50,
            alpha=0.8,
        )
        for lh in g.legend_.legend_handles[:-2]:
            lh.set_marker("o")
        for lh in g.legend_.legend_handles:
            lh.set_alpha(1)
        plt.tight_layout()
        plt.savefig(str(folderoots) + "/plots/AUC_comparison_cov_dir_all.png", dpi=200)
        plt.close()
        fig, ax = plt.subplots(figsize=(16, 9))
        ax.set_title("Growth strategies, AUC comparison")
        g = sns.scatterplot(
            df_growth,
            x="AUC of Directness",
            y="AUC of Relative Directness",
            style="Order",
            markers=["P", "o"],
            style_order=["additive", "subtractive"],
            hue="Metric optimized",
            hue_order=[
                "coverage",
                "adaptive_coverage",
                "directness",
                "relative_directness",
                "betweenness",
                "closeness",
                "random",
                "manual",
            ],
            palette=sns.color_palette("deep")[:8],
            ax=ax,
            s=50,
            alpha=0.8,
        )
        for lh in g.legend_.legend_handles[:-2]:
            lh.set_marker("o")
        for lh in g.legend_.legend_handles:
            lh.set_alpha(1)
        plt.tight_layout()
        plt.savefig(
            str(folderoots) + "/plots/AUC_comparison_reldir_dir_all.png", dpi=200
        )
        plt.close()
