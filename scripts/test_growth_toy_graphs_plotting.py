"""Script to plot results from test_growth_toy_graphs."""

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
            if met == "xx":
                pass
            else:
                fig, ax = plt.subplots(figsize=(16, 9))
                ax.set_title(f"{str(toy_graph_folder).split("/")[-1]}, {met}")
                # Add all growth strategies for a single metric
                for idx, (key, df) in enumerate(sorted(df_graph.items())):
                    # Put different marker based on order
                    if "additive" in key:
                        markerstyle = "^"
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
                # Add random trial, put 50 for median, 0 for min, 100 for max
                perc = 50
                # Compute the sum of all values so the highest sum is the highest area under curve so the better performing
                val_ra = np.sum(
                    [random_add[i][met].values for i in range(len(random_add))], axis=1
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
                    marker="^",
                )
                val_rs = np.sum(
                    [random_sub[i][met].values for i in range(len(random_sub))], axis=1
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
                plt.savefig(plotpath + f"/{met}.png", dpi=200)
                plt.close()
