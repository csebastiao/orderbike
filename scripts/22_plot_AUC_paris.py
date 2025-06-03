# -*- coding: utf-8 -*-
"""
Plot the AUC in additive order of all strategies on the tested graphs.
"""

import os
import pandas as pd
import matplotlib as mpl
from matplotlib import pyplot as plt
import json
import numpy as np


def is_pareto_efficient(x, df, fdim, sdim):
    return ~np.any(df[(df[fdim] > x[fdim]) & (df[sdim] > x[sdim])])


if __name__ == "__main__":
    with open("./scripts/22_plot_params_AUC_paris.json", "r") as f:
        plot_params = json.load(f)
    for key in plot_params["rcparams"]:
        mpl.rcParams[key] = plot_params["rcparams"][key]
    folderoots = "./data/processed/ignored_files/results_paris/"
    folderplot = folderoots + "plots/AUC"
    if not os.path.exists(folderplot):
        os.makedirs(folderplot)
    for built in [True, False]:
        for exp in [True, False]:
            savename = str(folderoots) + "/auc_table_growth"
            if built:
                savename += "_built"
            if exp:
                savename += "_expdisc"
            savename += ".json"
            df_growth = pd.read_json(savename)
            for order in [
                "additive",
                # "subtractive",
            ]:
                num = 7
                mask_ord = df_growth["Order"] == order
                for samelim in [True, False]:
                    fig, ax = plt.subplots(figsize=plot_params["figsize"])
                    for ids, met in enumerate(plot_params["order"][:num]):
                        mask_met = df_growth["Metric optimized"] == met
                        ax.scatter(
                            df_growth[mask_ord & mask_met]["AUC of Directness"],
                            df_growth[mask_ord & mask_met]["AUC of Coverage"],
                            zorder=2,
                            **{
                                key: val[ids]
                                for key, val in plot_params.items()
                                if key not in ["dpi", "figsize", "rcparams", "order"]
                            },
                        )
                    ax.set_xlabel("AUC of directness")
                    ax.set_ylabel("AUC of coverage")
                    savename = folderplot + f"/AUC_comparison_cov_dir_{order}"
                    if built:
                        savename += "_built"
                    if exp:
                        savename += "_expdisc"
                    # Put ticks at each 0.1
                    loc = mpl.ticker.MultipleLocator(base=0.1)
                    ax.xaxis.set_major_locator(loc)
                    ax.yaxis.set_major_locator(loc)
                    plt.axis("square")
                    # Set rounded limits at smallest and highest 0.1
                    dirmin = df_growth[mask_ord]["AUC of Directness"].min()
                    dirmax = df_growth[mask_ord]["AUC of Directness"].max()
                    covmin = df_growth[mask_ord]["AUC of Coverage"].min()
                    covmax = df_growth[mask_ord]["AUC of Coverage"].max()
                    if samelim:
                        savename += "_samelim"
                        mmin = round(min(dirmin, covmin) - 0.05, 1)
                        mmax = round(max(dirmax, covmax) + 0.05, 1)
                        ax.set_xlim([mmin, mmax])
                        ax.set_ylim([mmin, mmax])
                    else:
                        ax.set_xlim([round(dirmin - 0.05, 1), round(dirmax + 0.05, 1)])
                        ax.set_ylim([round(covmin - 0.05, 1), round(covmax + 0.05, 1)])
                    parfront = df_growth[mask_ord].copy()
                    parfront = parfront[
                        parfront.apply(
                            lambda x: is_pareto_efficient(
                                x, parfront, "AUC of Coverage", "AUC of Directness"
                            ),
                            axis=1,
                        )
                    ]
                    parfront.sort_values("AUC of Directness", axis=0, inplace=True)
                    ax.plot(
                        parfront["AUC of Directness"],
                        parfront["AUC of Coverage"],
                        linestyle="dashed",
                        linewidth=1,
                        color="black",
                        zorder=1,
                        label="Pareto front",
                    )
                    plt.legend(prop={"size": plot_params["rcparams"]["font.size"]})
                    plt.savefig(savename)
                    plt.close()
