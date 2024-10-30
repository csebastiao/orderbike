"""
Script to plot as a scatterplot the Area Under Curve for the Coverage versus the Area Under Curve for the Directness, for multiple trials for all strategies.
"""

import os
import pathlib
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

if __name__ == "__main__":
    folderoots = "./data/processed/plan_paris/ignored_growth/pruned_paris_multigraph/"
    for met_observed, ylabel in [
        ["coverage", "Coverage ($m^2$)"],
        ["directness", "Directness"],
        ["length_lcc", "Length of the largest component ($m$)"],
        ["num_cc", "Number of components"],
    ]:
        if not os.path.exists(folderoots + "plots/"):
            os.makedirs(folderoots + "plots/")
        sns.set_theme(font_scale=1.5, style="whitegrid")
        # Open for all toy graphs
        dfs = []
        dfs_random_add = []
        dfs_random_sub = []
        # Open for all growth strategies for a toy graph
        for growth_f in [
            fold
            for fold in pathlib.Path(folderoots).iterdir()
            if not fold.is_file()
            and "plot" not in str(fold)
            and ".DS_Store" not in str(fold)
        ]:
            growthname = str(growth_f).split("/")[-1].removesuffix("_connected_built")
            if (
                "adaptive_coverage" in growthname
                or "betweenness" in growthname
                or "closeness" in growthname
            ):
                pass
            else:
                if "additive" in growthname:
                    order = "additive"
                elif "subtractive" in growthname:
                    order = "subtractive"
                met_name = "_".join(growthname.split("_")[:-1])
                if "random" in growthname:
                    for trial in sorted(
                        [
                            fold
                            for fold in pathlib.Path(growth_f).iterdir()
                            if "metric" in str(fold)
                        ]
                    ):
                        trialnum = (
                            str(trial)
                            .split("/")[-1]
                            .split("_")[-1]
                            .removesuffix(".json")
                        )
                        df = pd.read_json(trial)
                        df["Trial"] = trialnum
                        df["Order"] = order
                        df["Metric optimized"] = met_name
                        if order == "additive":
                            dfs_random_add.append(df)
                        else:
                            dfs_random_sub.append(df)
                else:
                    df = pd.read_json(str(growth_f) + "/metrics_growth.json")
                    df["Trial"] = 0
                    df["Order"] = order
                    df["Metric optimized"] = met_name
                    dfs.append(df)
        val_ra = np.sum(
            [
                dfs_random_add[i][met_observed].values
                for i in range(len(dfs_random_add))
            ],
            axis=1,
        )
        # Find the DataFrame of the random trial at the chosen percentile
        med_ra = dfs_random_add[
            list(val_ra).index(np.percentile(val_ra, 50, interpolation="nearest"))
        ]
        dfs.append(med_ra)
        val_ra = np.sum(
            [
                dfs_random_sub[i][met_observed].values
                for i in range(len(dfs_random_sub))
            ],
            axis=1,
        )
        # Find the DataFrame of the random trial at the chosen percentile
        med_ra = dfs_random_sub[
            list(val_ra).index(np.percentile(val_ra, 50, interpolation="nearest"))
        ]
        dfs.append(med_ra)
        dfs = pd.concat(dfs, axis=0)
        fig, ax = plt.subplots(figsize=(16, 9))
        # ax.set_title("Growth strategies, Coverage")
        # g = sns.lineplot(
        #     data=dfs[dfs["Order"] == "subtractive"],
        #     x="xx",
        #     y=met_observed,
        #     hue="Metric optimized",
        #     hue_order=[
        #         "coverage",
        #         # "adaptive_coverage",
        #         "directness",
        #         # "relative_directness",
        #         "betweenness",
        #         "closeness",
        #         "random",
        #     ],
        #     style="Order",
        #     style_order=["additive", "subtractive"],
        #     markers = ["P", "o"],
        #     dashes = False,
        #     palette=sns.color_palette("deep")[:5],
        #     ax=ax,
        #     alpha=0.9,
        #     markersize=5,
        #     legend=False,
        # )
        g = sns.lineplot(
            data=dfs[dfs["Order"] == "additive"],
            x="xx",
            y=met_observed,
            hue="Metric optimized",
            hue_order=[
                "coverage",
                # "adaptive_coverage",
                "directness",
                # "relative_directness",
                # "betweenness",
                # "closeness",
                "random",
            ],
            # style="Order",
            # style_order=["additive", "subtractive"],
            markers="o",
            dashes=False,
            palette=sns.color_palette("bright")[:3],
            ax=ax,
            alpha=1,
            linewidth=5,
        )
        ax.set_xlabel("Road built ($m$)")
        ax.set_ylabel(ylabel)
        plt.tight_layout()
        plt.savefig(
            str(folderoots) + f"/plots/growth_srategies_{met_observed}.png", dpi=200
        )
        plt.close()
