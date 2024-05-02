"""
Script to plot as a scatterplot the Area Under Curve for the Coverage versus the Area Under Curve for the Directness.
"""

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
    # TODO Finish it
    folderoots = "./data/processed/ignored_files/utg"
    sns.set_theme(style="whitegrid")
    # Open for all toy graphs
    for toy_graph_folder in [
        fold
        for fold in pathlib.Path(folderoots).iterdir()
        if ".DS_Store" not in str(fold)
    ]:
        toy_graph_aucs = []
        random_add = []
        random_sub = []
        # Open for all growth strategies for a toy graph
        for growth_f in [
            fold
            for fold in pathlib.Path(toy_graph_folder).iterdir()
            if not fold.is_file()
            and "plot" not in str(fold)
            and ".DS_Store" not in str(fold)
        ]:
            # For random trials, open all trials
            if "random_trials" in str(growth_f):
                for random_trial in sorted(list(pathlib.Path(growth_f).iterdir())):
                    # Open only the metrics growth not the order growth
                    if "metrics" in str(random_trial):
                        with open(random_trial, "r") as f:
                            # Divide between additive and subtractive growth
                            if "random_trials_additive" in str(random_trial):
                                random_add.append(json.load(f))
                            else:
                                random_sub.append(json.load(f))
            else:
                with open(str(growth_f) + "/metrics_growth.json", "r") as f:
                    met_dict = json.load(f)
                growthname = str(growth_f).split("/")[-1].removesuffix("_connected")
                if "additive" in growthname:
                    order = "additive"
                elif "subtractive" in growthname:
                    order = "subtractive"
                met_name = "_".join(growthname.split("_")[:-1])
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
                toy_graph_aucs.append([met_name, order, auc_cov, auc_dir, auc_reldir])
        random_add_aucs = []
        for met_dict in random_add:
            auc_cov = auc_from_metrics_dict(
                met_dict, "coverage", normalize_y=True, zero_yaxis=False
            )
            auc_dir = auc_from_metrics_dict(met_dict, "directness", normalize_y=False)
            auc_reldir = auc_from_metrics_dict(
                met_dict, "relative_directness", normalize_y=False
            )
            random_add_aucs.append(["random", "additive", auc_cov, auc_dir, auc_reldir])
        random_sub_aucs = []
        for met_dict in random_sub:
            auc_cov = auc_from_metrics_dict(
                met_dict, "coverage", normalize_y=True, zero_yaxis=False
            )
            auc_dir = auc_from_metrics_dict(met_dict, "directness", normalize_y=False)
            auc_reldir = auc_from_metrics_dict(
                met_dict, "relative_directness", normalize_y=False
            )
            random_sub_aucs.append(
                ["random", "subtractive", auc_cov, auc_dir, auc_reldir]
            )
        random_aucs = random_add_aucs + random_sub_aucs
        # Save everything as JSON with Pandas Dataframe
        df_growth = pd.DataFrame(
            toy_graph_aucs,
            columns=[
                "Metric optimized",
                "Order",
                "AUC of Coverage",
                "AUC of Directness",
                "AUC of Relative Directness",
            ],
        )
        df_random = pd.DataFrame(
            random_aucs,
            columns=[
                "Metric optimized",
                "Order",
                "AUC of Coverage",
                "AUC of Directness",
                "AUC of Relative Directness",
            ],
        )
        df_growth.to_json(str(toy_graph_folder) + "/auc_table_growth.json")
        df_random.to_json(str(toy_graph_folder) + "/auc_table_random.json")
        fig, ax = plt.subplots(figsize=(16, 9))
        ax.set_title("Growth strategies, AUC comparison")
        sns.scatterplot(
            df_growth,
            x="AUC of Directness",
            y="AUC of Coverage",
            style="Order",
            hue="Metric optimized",
            ax=ax,
            s=100,
        )
        plt.tight_layout()
        plt.savefig(
            str(toy_graph_folder) + "/plots/AUC_comparison_cov_dir.png", dpi=200
        )
        plt.close()
        fig, ax = plt.subplots(figsize=(16, 9))
        sns.scatterplot(
            df_random,
            x="AUC of Directness",
            y="AUC of Coverage",
            hue="Order",
            ax=ax,
            alpha=0.2,
            palette=sns.color_palette("pastel")[:2],
        )
        ax.set_title("All strategies, AUC comparison")
        sns.scatterplot(
            df_growth,
            x="AUC of Directness",
            y="AUC of Coverage",
            style="Order",
            hue="Metric optimized",
            ax=ax,
            s=100,
            palette=sns.color_palette("deep")[2:-2],
        )
        plt.tight_layout()
        plt.savefig(
            str(toy_graph_folder) + "/plots/AUC_comparison_cov_dir_all.png", dpi=200
        )
        plt.close()
        fig, ax = plt.subplots(figsize=(16, 9))
        ax.set_title("Random growths, AUC comparison")
        sns.scatterplot(
            df_random,
            x="AUC of Directness",
            y="AUC of Coverage",
            hue="Order",
            ax=ax,
            alpha=0.2,
        )
        plt.tight_layout()
        plt.savefig(
            str(toy_graph_folder) + "/plots/AUC_comparison_cov_dir_random.png", dpi=200
        )
        plt.close()
        fig, ax = plt.subplots(figsize=(16, 9))
        ax.set_title("Growth strategies, AUC comparison")
        sns.scatterplot(
            df_growth,
            x="AUC of Directness",
            y="AUC of Relative Directness",
            style="Order",
            hue="Metric optimized",
            ax=ax,
            s=100,
        )
        plt.tight_layout()
        plt.savefig(
            str(toy_graph_folder) + "/plots/AUC_comparison_reldir_dir.png", dpi=200
        )
        plt.close()
        fig, ax = plt.subplots(figsize=(16, 9))
        ax.set_title("Random growths, AUC comparison")
        sns.scatterplot(
            df_random,
            x="AUC of Directness",
            y="AUC of Relative Directness",
            hue="Order",
            ax=ax,
            alpha=0.2,
        )
        plt.tight_layout()
        plt.savefig(
            str(toy_graph_folder) + "/plots/AUC_comparison_reldir_dir_random.png",
            dpi=200,
        )
        plt.close()
        fig, ax = plt.subplots(figsize=(16, 9))
        ax.set_title("All strategies, AUC comparison")
        sns.scatterplot(
            df_growth,
            x="AUC of Directness",
            y="AUC of Relative Directness",
            style="Order",
            hue="Metric optimized",
            ax=ax,
            s=100,
            palette=sns.color_palette("deep")[2:-2],
        )
        sns.scatterplot(
            df_random,
            x="AUC of Directness",
            y="AUC of Relative Directness",
            hue="Order",
            ax=ax,
            alpha=0.2,
            palette=sns.color_palette("pastel")[:2],
        )
        plt.tight_layout()
        plt.savefig(
            str(toy_graph_folder) + "/plots/AUC_comparison_reldir_dir_all.png",
            dpi=200,
        )
        plt.close()
