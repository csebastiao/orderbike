# -*- coding: utf-8 -*-
"""
Script to plot as a scatterplot the Area Under Curve for the Coverage versus the Area Under Curve for the Directness, for multiple trials for all strategies.
"""

import os
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
import pathlib
import json
from orderbike.utils import auc_from_metrics_dict


if __name__ == "__main__":
    for graphname in [
        "radio_concentric",
        "grid",
        "grid_with_diagonal",
        "three_bridges",
    ]:
        folderoots = f"./data/processed/ignored_files/paper/{graphname}/"
        if not os.path.exists(folderoots + "plots/"):
            os.makedirs(folderoots + "plots/")
        sns.set_theme(style="whitegrid")
        # With and without exponential discounting
        for exp_disc in [True, False]:
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
                        met_dict,
                        "coverage",
                        zero_yaxis=False,
                        exp_discounting=exp_disc,
                    )
                    auc_dir = auc_from_metrics_dict(
                        met_dict,
                        "directness",
                        normalize_y=False,
                        exp_discounting=exp_disc,
                    )
                    auc_reldir = auc_from_metrics_dict(
                        met_dict,
                        "relative_directness",
                        normalize_y=False,
                        exp_discounting=exp_disc,
                    )
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
            savename = str(folderoots) + "/auc_table_growth"
            if exp_disc:
                savename += "_expdisc"
            savename += ".json"
            df_growth.to_json(savename)
            df_growth = pd.read_json(savename)
            fig, ax = plt.subplots(figsize=(16, 9))
            ax.set_title("Growth strategies, AUC comparison")
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
            g = sns.scatterplot(
                df_growth,
                x="AUC of Directness",
                y="AUC of Coverage",
                hue="Metric optimized",
                hue_order=hue_order,
                style="Order",
                markers=["P", "o"],
                style_order=["additive", "subtractive"],
                palette=sns.color_palette("deep")[: len(hue_order)],
                ax=ax,
                s=50,
                alpha=0.9,
            )
            for lh in g.legend_.legend_handles[:-2]:
                lh.set_marker("o")
            for lh in g.legend_.legend_handles:
                lh.set_alpha(1)
            plt.tight_layout()
            savename = str(folderoots) + "/plots/AUC_comparison_cov_dir"
            if exp_disc:
                savename += "_expdisc"
            savename += ".png"
            plt.savefig(savename, dpi=300)
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
                hue_order=hue_order,
                palette=sns.color_palette("deep")[: len(hue_order)],
                ax=ax,
                s=50,
                alpha=0.9,
            )
            for lh in g.legend_.legend_handles[:-2]:
                lh.set_marker("o")
            for lh in g.legend_.legend_handles:
                lh.set_alpha(1)
            plt.tight_layout()
            savename = str(folderoots) + "/plots/AUC_comparison_rel_dir"
            if exp_disc:
                savename += "_expdisc"
            savename += ".png"
            plt.savefig(savename, dpi=300)
            plt.close()
