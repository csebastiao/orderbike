# -*- coding: utf-8 -*-
"""
Script to compute the Area Under the Curve of all metrics for all strategies on all graph.
"""


import pandas as pd
import pathlib
import json
from orderbike.utils import auc_from_metrics_dict


if __name__ == "__main__":
    for graphname in [
        # "grid",
        # "grid_2",
        "radio_concentric",
        # "grid_with_diagonal",
        # "three_bridges",
    ]:
        folderoots = f"./data/processed/ignored_files/paper/{graphname}/"
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
                if "built" in str(growth_f):
                    growthname = (
                        str(growth_f).split("/")[-1].removesuffix("_connected_built")
                    )
                else:
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
