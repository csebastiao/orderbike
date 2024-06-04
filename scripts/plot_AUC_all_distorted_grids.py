"""
Script to plot as a scatterplot the Area Under Curve for the Coverage versus the Area Under Curve for the Directness, for all distorted grids on the same plot.
"""


import pandas as pd
import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt

# TODO FINISH IT
if __name__ == "__main__":
    df_growth_all = []
    for i in range(5):
        folderoots = f"./data/processed/ignored_files/utg_distorted_grids/dg_{i}/"
        sns.set_theme(style="whitegrid")
        df_growth = pd.read_json(str(folderoots) + "/auc_table_growth.json")
        for met in set(df_growth["Metric optimized"].values):
            df_met = df_growth[df_growth["Metric optimized"] == met]
            df_met["joint"] = (
                df_met["AUC of Directness"] + df_met["AUC of Coverage"]
            ) / 2
            med_val = list(df_met["joint"].values).index(
                np.percentile(df_met["joint"].values, 50, interpolation="nearest")
            )

    fig, ax = plt.subplots(figsize=(16, 9))
    ax.set_title("Growth strategies, AUC comparison")
    g = sns.scatterplot(
        df_growth_all,
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
        df_growth_all,
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
    plt.savefig(str(folderoots) + "/plots/AUC_comparison_reldir_dir_all.png", dpi=200)
    plt.close()
