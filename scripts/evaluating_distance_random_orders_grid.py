# -*- coding: utf-8 -*-
"""
Evaluate the difference of the median value for random choices on smaller to larger grids.
"""

import os
import json
import pandas as pd
import seaborn as sns
import numpy as np
from matplotlib import pyplot as plt
from sklearn.metrics import auc

from utg import create_graph
from utg import utils as utgut
from orderbike import growth, metrics
from orderbike.utils import log


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
    BUILT = False
    CONNECTED = True
    # Put slightly more than 150 to avoid rounding wizardry
    BUFF_SIZE = 152
    NUM_RAND_TRIAL = 500
    PAD = len(str(NUM_RAND_TRIAL))
    for i in range(10):
        log.info(f"Start graph of size {3+i}")
        G = create_graph.create_grid_graph(rows=3 + i, cols=3 + i, width=100)
        folderoots = (
            f"./data/processed/ignored_files/utg_variable_grid_random/size_{3+i}/"
        )
        if not os.path.exists(folderoots):
            os.makedirs(folderoots)
        utgut.save_graph(G, folderoots + "graph.graphml")
        utgut.plot_graph(
            G,
            save=True,
            show=False,
            close=True,
            filepath=folderoots + "picture.png",
        )
        met_df = []
        for ORDERNAME in [
            "additive",
            "subtractive",
        ]:
            foldername = folderoots + "random_" + ORDERNAME
            if CONNECTED:
                foldername += "_connected"
            if BUILT:
                foldername += "_built"
            if not os.path.exists(foldername):
                os.makedirs(foldername)
            log.info(f"Start random computation, order {ORDERNAME}")
            for j in range(NUM_RAND_TRIAL):
                metrics_dict, order_growth = growth.order_ranked_network_growth(
                    G,
                    built=BUILT,
                    keep_connected=CONNECTED,
                    order=ORDERNAME,
                    ranking_func=metrics.growth_random,
                    save_metrics=True,
                    buff_size_metrics=BUFF_SIZE,
                )
                with open(foldername + f"/order_growth_{j:0{PAD}}.json", "w") as f:
                    json.dump(order_growth, f)
                with open(foldername + f"/metrics_growth_{j:0{PAD}}.json", "w") as f:
                    json.dump(metrics_dict, f)
                auc_cov = auc_from_metrics_dict(
                    metrics_dict, "coverage", normalize_y=True, zero_yaxis=False
                )
                auc_dir = auc_from_metrics_dict(
                    metrics_dict, "directness", normalize_y=False
                )
                met_df.append([3 + i, ORDERNAME, j, auc_cov, auc_dir])
        met_df = pd.DataFrame(
            met_df,
            columns=[
                "Grid size",
                "Order",
                "Trial",
                "AUC of Coverage",
                "AUC of Directness",
            ],
        )
        met_df.to_json(folderoots + "auc_table.json")
        fig, ax = plt.subplots(figsize=(16, 9))
        ax.set_title("Growth strategies, AUC comparison")
        sns.scatterplot(
            met_df,
            x="AUC of Directness",
            y="AUC of Coverage",
            hue="Order",
            ax=ax,
            s=100,
            alpha=0.8,
        )
        plt.tight_layout()
        plt.savefig(folderoots + "AUC_comparison_cov_dir.png", dpi=200)
        plt.close()
    log.info("Finished !")
