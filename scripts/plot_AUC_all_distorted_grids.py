"""
Script to plot as a scatterplot the Area Under Curve for the Coverage versus the Area Under Curve for the Directness, for all distorted grids on the same plot.
"""


import pandas as pd
import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt

# TODO FINISH IT
if __name__ == "__main__":
    sns.set_theme(style="whitegrid")
    df_growth_all_noise = []
    for i in range(5):
        folderoots = f"./data/processed/ignored_files/utg_distorted_grids/dg_{i}/"
        df_growth = pd.read_json(str(folderoots) + "/auc_table_growth.json")
        for met in [
            "coverage",
            "adaptive_coverage",
            "directness",
            "relative_directness",
            "betweenness",
            "closeness",
            "random",
            "manual",
        ]:
            mc = df_growth["Metric optimized"] == met
            orderlist = ["additive", "subtractive"]
            if met == "manual":
                for arr in df_growth[mc].values:
                    df_growth_all_noise.append(np.insert(arr[:-1], 0, i))
            else:
                for order in orderlist:
                    oc = df_growth["Order"] == order
                    df_met = df_growth[oc & mc]
                    joint = (
                        df_met["AUC of Directness"] + df_met["AUC of Coverage"]
                    ) / 2
                    med_val = np.percentile(joint.values, 50, interpolation="nearest")
                    med_ind = joint.loc[joint.values == med_val].index[0]
                    df_growth_all_noise.append(
                        np.insert(df_growth.values[med_ind][:-1], 0, i)
                    )
    df_growth_all_noise = pd.DataFrame(
        df_growth_all_noise,
        columns=[
            "Grid",
            "Metric optimized",
            "Order",
            "Original trial index",
            "AUC of Coverage",
            "AUC of Directness",
        ],
    )
    df_growth_grid = []
    folderoots = "./data/processed/ignored_files/utg_grid_trials/"
    df_growth = pd.read_json(str(folderoots) + "/auc_table_growth.json")
    for met in [
        "coverage",
        "adaptive_coverage",
        "directness",
        "relative_directness",
        "betweenness",
        "closeness",
        "random",
        "manual",
    ]:
        mc = df_growth["Metric optimized"] == met
        orderlist = ["additive", "subtractive"]
        if met == "manual":
            for arr in df_growth[mc].values:
                df_growth_grid.append(np.insert(arr[:-1], 0, i))
        else:
            for order in orderlist:
                oc = df_growth["Order"] == order
                df_met = df_growth[oc & mc]
                joint = (df_met["AUC of Directness"] + df_met["AUC of Coverage"]) / 2
                med_val = np.percentile(joint.values, 50, interpolation="nearest")
                med_ind = joint.loc[joint.values == med_val].index[0]
                df_growth_grid.append(np.insert(df_growth.values[med_ind][:-1], 0, i))
    df_growth_grid = pd.DataFrame(
        df_growth_grid,
        columns=[
            "Grid",
            "Metric optimized",
            "Order",
            "Original trial index",
            "AUC of Coverage",
            "AUC of Directness",
        ],
    )
    fig, ax = plt.subplots(figsize=(16, 9))
    ax.set_title("Growth strategies, AUC comparison")
    sns.scatterplot(
        df_growth_grid,
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
        palette=sns.color_palette("bright")[:8],
        ax=ax,
        s=50,
        alpha=0.9,
        legend=False,
    )
    g = sns.scatterplot(
        df_growth_all_noise,
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
        alpha=0.4,
    )
    for lh in g.legend_.legend_handles[:-2]:
        lh.set_marker("o")
    for lh in g.legend_.legend_handles:
        lh.set_alpha(1)
    plt.tight_layout()
    plt.savefig(
        "./data/processed/ignored_files/utg_distorted_grids/AUC_comparison_cov_dir_all.png",
        dpi=200,
    )
    plt.close()
