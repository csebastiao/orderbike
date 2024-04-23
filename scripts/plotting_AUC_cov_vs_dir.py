# -*- coding: utf-8 -*-
"""
Script to plot as a scatterplot the Area Under Curve for the Coverage versus the Area Under Curve for the Directness.
"""

import pathlib
import json
import pandas as pd
import seaborn as sns
import numpy as np
from matplotlib import pyplot as plt
from utg import utils as utgut
from sklearn.metrics import auc


def get_auc(xx, yy, normalize_x=True, normalize_y=True, zero_yaxis=False):
    if normalize_x:
        xx = (np.array(xx) - np.min(xx)) / (np.max(xx) - np.min(xx))
    if normalize_y:
        if zero_yaxis:
            min_y = 0
        else:
            min_y = np.min(yy)
        yy = (np.array(yy) - min_y) / (np.max(yy) - min_y)
    return auc(xx, yy)


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
        G = utgut.load_graph(str(toy_graph_folder) + "/graph.graphml")
        random_add = []
        random_sub = []
        df_graph = {}
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
                for random_trial in list(pathlib.Path(growth_f).iterdir()):
                    # Open only the metrics growth not the order growth
                    if "metrics" in str(random_trial):
                        with open(random_trial, "r") as f:
                            # Divide between additive and subtractive growth
                            if "random_trials_additive" in str(random_trial):
                                random_add.append(pd.DataFrame.from_dict(json.load(f)))
                            else:
                                random_sub.append(pd.DataFrame.from_dict(json.load(f)))
            else:
                # For growth strategies, add DataFrame with specific name of metric optimized and order as key
                with open(str(growth_f) + "/metrics_growth.json", "r") as f:
                    df_graph[
                        str(growth_f).split("/")[-1].removesuffix("_connected")
                    ] = pd.DataFrame.from_dict(json.load(f))
        # Create plot folder if not existing
        plotpath = str(toy_graph_folder) + "/plots"
        pathlib.Path(plotpath).mkdir(parents=True, exist_ok=True)
        # Start plotting metrics
        fig, ax = plt.subplots(figsize=(16, 9))
        ax.set_title(f"{str(toy_graph_folder).split("/")[-1]}, AUC comparison")
        for met in random_add[0].columns:
            if met in ["xx", "length_lcc", "num_cc"]:
                pass
            else:
                # Plot for different values of random
                PERC_VALS = [0, 50, 100]
                random_highlight_add = []
                random_others_add = random_add.copy()
                random_highlight_sub = []
                random_others_sub = random_sub.copy()
                ind_add_rem = []
                ind_sub_rem = []
                for perc in PERC_VALS:
                    # Compute the sum of all values so the highest sum is the highest area under curve so the better performing
                    val_ra = np.sum(
                        [random_add[i][met].values for i in range(len(random_add))],
                        axis=1,
                    )
                    # Find the DataFrame of the random trial at the chosen percentile
                    ind_ra = list(val_ra).index(
                        np.percentile(val_ra, perc, interpolation="nearest")
                    )
                    med_ra = random_add[ind_ra]
                    ind_add_rem.append(ind_ra)
                    val_rs = np.sum(
                        [random_sub[i][met].values for i in range(len(random_sub))],
                        axis=1,
                    )
                    ind_rs = list(val_rs).index(
                        np.percentile(val_rs, perc, interpolation="nearest")
                    )
                    med_rs = random_sub[ind_rs]
                    ind_sub_rem.append(ind_ra)
                    random_highlight_add.append(med_ra)
                    random_highlight_sub.append(med_rs)
                # Add all growth strategies for a single metric
                for idx, (key, df) in enumerate(sorted(df_graph.items())):
                    # Put different marker based on order
                    if "additive" in key:
                        markerstyle = "P"
                    else:
                        markerstyle = "o"
                # Compute the sum of all values so the highest sum is the highest area under curve so the better performing
                val_ra = np.sum(
                    [random_add[i][met].values for i in range(len(random_add))],
                    axis=1,
                )
                # Find the DataFrame of the random trial at the chosen percentile
                med_ra = random_add[
                    list(val_ra).index(
                        np.percentile(val_ra, perc, interpolation="nearest")
                    )
                ]
                val_rs = np.sum(
                    [random_sub[i][met].values for i in range(len(random_sub))],
                    axis=1,
                )
                med_rs = random_sub[
                    list(val_rs).index(
                        np.percentile(val_rs, perc, interpolation="nearest")
                    )
                ]
                ax.set_xlabel("Meters built")
                plt.tight_layout()
                plt.savefig(plotpath + f"/{met}_random_{perc}_percentile.png", dpi=200)
                plt.close()
                fig, ax = plt.subplots(figsize=(16, 9))
                ax.set_title(
                    f"{str(toy_graph_folder).split("/")[-1]}, AUC Comparison, random trials"
                )
                ax.set_xlabel("Normalized AUC of Coverage")
                ax.set_ylabel("Normalized AUC of Directness")
                plt.legend()
                plt.tight_layout()
                plt.savefig(plotpath + f"/{met}_random_subtractive_trials.png", dpi=200)
                plt.close()
