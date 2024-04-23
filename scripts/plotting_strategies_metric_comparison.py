# -*- coding: utf-8 -*-
"""
Script to plot multiple strategies of same graph compared on the same metrics, with specific comparison for random trials.
"""

import pathlib
import json
import pandas as pd
import seaborn as sns
import numpy as np
from matplotlib import pyplot as plt
from utg import utils as utgut

if __name__ == "__main__":
    folderoots = "./data/processed/ignored_files/utg"
    # Create color palette, need 7 colors in 2 hues !!! Impossible to make pretty with everything
    add_colors = sns.color_palette("bright")[:7]
    sub_colors = sns.color_palette("deep")[:7]
    color_palette = [
        item for sublist in zip(add_colors, sub_colors) for item in sublist
    ]
    # Set theme
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
        for met in random_add[0].columns:
            if met in ["xx", "length_lcc", "num_cc"]:
                pass
            else:
                # Plot for different values of random
                PERC_VALS = [0, 50, 100]
                for perc in PERC_VALS:
                    fig, ax = plt.subplots(figsize=(16, 9))
                    ax.set_title(f"{str(toy_graph_folder).split("/")[-1]}, {met}")
                    # Add all growth strategies for a single metric
                    for idx, (key, df) in enumerate(sorted(df_graph.items())):
                        # Put different marker based on order
                        if "additive" in key:
                            markerstyle = "P"
                        else:
                            markerstyle = "o"
                        sns.lineplot(
                            data=df,
                            x="xx",
                            y=met,
                            ax=ax,
                            color=color_palette[idx],
                            label=key,
                            marker=markerstyle,
                        )
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
                    sns.lineplot(
                        data=med_ra,
                        x="xx",
                        y=met,
                        ax=ax,
                        color=color_palette[-2],
                        label=f"random_{perc}th percentile_additive",
                        marker="P",
                    )
                    val_rs = np.sum(
                        [random_sub[i][met].values for i in range(len(random_sub))],
                        axis=1,
                    )
                    med_rs = random_sub[
                        list(val_rs).index(
                            np.percentile(val_rs, perc, interpolation="nearest")
                        )
                    ]
                    sns.lineplot(
                        data=med_rs,
                        x="xx",
                        y=met,
                        ax=ax,
                        color=color_palette[-1],
                        label=f"random_{perc}th percentile_subtractive",
                        marker="o",
                    )
                    ax.set_xlabel("Meters built")
                    plt.tight_layout()
                    plt.savefig(
                        plotpath + f"/{met}_random_{perc}_percentile.png", dpi=200
                    )
                    plt.close()
                # plot all random trials
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
                for i in sorted(ind_add_rem, reverse=True):
                    del random_others_add[i]
                for i in sorted(ind_sub_rem, reverse=True):
                    del random_others_sub[i]
                fig, ax = plt.subplots(figsize=(16, 9))
                ax.set_title(
                    f"{str(toy_graph_folder).split("/")[-1]}, {met}, additive random trials"
                )
                for df in random_others_add:
                    sns.lineplot(
                        data=df,
                        x="xx",
                        y=met,
                        ax=ax,
                        color=sns.color_palette()[0],
                        alpha=0.1,
                        zorder=0,
                    )
                for idx, df in enumerate(random_highlight_add):
                    sns.lineplot(
                        data=df,
                        x="xx",
                        y=met,
                        ax=ax,
                        color=sns.color_palette()[idx + 1],
                        label=f"{PERC_VALS[idx]}th percentile",
                        zorder=1,
                    )
                ax.set_xlabel("Meters built")
                plt.legend()
                plt.tight_layout()
                plt.savefig(plotpath + f"/{met}_random_additive_trials.png", dpi=200)
                plt.close()
                fig, ax = plt.subplots(figsize=(16, 9))
                ax.set_title(
                    f"{str(toy_graph_folder).split("/")[-1]}, {met}, subtractive random trials"
                )
                for df in random_others_sub:
                    sns.lineplot(
                        data=df,
                        x="xx",
                        y=met,
                        ax=ax,
                        color=sns.color_palette()[0],
                        alpha=0.1,
                        zorder=0,
                    )
                for df in random_highlight_sub:
                    sns.lineplot(
                        data=df,
                        x="xx",
                        y=met,
                        ax=ax,
                        color=sns.color_palette()[idx + 1],
                        label=f"{PERC_VALS[idx]}th percentile",
                        zorder=1,
                    )
                ax.set_xlabel("Meters built")
                plt.legend()
                plt.tight_layout()
                plt.savefig(plotpath + f"/{met}_random_subtractive_trials.png", dpi=200)
                plt.close()
                # TODO Add comparison with 6 small figure one next to another with add/subtractive on it instead of 12 on the same one
