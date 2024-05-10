# -*- coding: utf-8 -*-
"""
Script to find growth order on 5 urban toy graphs, with all growth strategies, dynamic and ranked, and random trials.
"""

import os
import json

from matplotlib import pyplot as plt
import seaborn as sns

from utg import create_graph
from utg import utils as utgut
from orderbike import growth, plot, metrics
from orderbike.utils import log

if __name__ == "__main__":
    BUILT = False
    CONNECTED = True
    ranking_func = {}
    ranking_func["closeness"] = metrics.growth_closeness
    ranking_func["betweenness"] = metrics.growth_betweenness
    G_graph = {}
    G_graph["grid"] = create_graph.create_grid_graph(
        rows=10, cols=10, diagonal=False, width=100
    )
    # G_graph["single_bridge"] = create_graph.create_bridge_graph(
    #     outrows=3, sscols=4, bridges=1, block_side=100, blength=300
    # )
    # G_graph["multiple_bridges"] = create_graph.create_bridge_graph(
    #     outrows=3, sscols=4, bridges=3, block_side=100, blength=300
    # )
    # G_graph["grid_wdiagonal"] = create_graph.create_grid_graph(
    #     rows=10, cols=10, diagonal=True, width=100
    # )
    # G_graph["radio_concentric"] = create_graph.create_concentric_graph(
    #     radial=8, zones=6, radius=100, straight_edges=True, center=True
    # )
    # Put slightly more than 150 to avoid rounding wizardry
    BUFF_SIZE = 152
    for name in ["grid"]:
        log.info(f"Start all computations for the {name} graph")
        foldername = "./data/processed/ignored_files/utg/" + name
        if not os.path.exists(foldername):
            os.makedirs(foldername)
        utgut.save_graph(G_graph[name], foldername + "/graph.graphml")
        utgut.plot_graph(
            G_graph[name],
            save=True,
            show=False,
            close=True,
            filepath=foldername + "/picture.png",
        )
        for ORDERNAME in ["additive", "subtractive"]:
            for METRICNAME in [
                "coverage",
                "adaptive_coverage",
                "directness",
                "relative_directness",
            ]:
                log.info(
                    f"Start computation for metric {METRICNAME}, order {ORDERNAME}"
                )
                if METRICNAME == "coverage":
                    kwargs = {"buff_size": BUFF_SIZE}
                elif METRICNAME == "adaptive_coverage":
                    kwargs = {"max_buff": BUFF_SIZE * 2, "min_buff": BUFF_SIZE / 2}
                else:
                    kwargs = {}
                metrics_dict, order_growth = growth.order_dynamic_network_growth(
                    G_graph[name],
                    built=BUILT,
                    keep_connected=CONNECTED,
                    order=ORDERNAME,
                    metric=METRICNAME,
                    progress_bar=False,
                    save_metrics=True,
                    buff_size_metrics=BUFF_SIZE,
                    **kwargs,
                )
                foldername = (
                    "./data/processed/ignored_files/utg/"
                    + name
                    + "/"
                    + METRICNAME
                    + "_"
                    + ORDERNAME
                )
                if CONNECTED:
                    foldername += "_connected"
                if BUILT:
                    foldername += "_built"
                if not os.path.exists(foldername):
                    os.makedirs(foldername)
                with open(foldername + "/order_growth.json", "w") as f:
                    json.dump(order_growth, f)
                with open(foldername + "/metrics_growth.json", "w") as f:
                    json.dump(metrics_dict, f)
                md = {}
                md["growth"] = "dynamic"
                md["built"] = BUILT
                md["keep_connected"] = CONNECTED
                md["metric"] = METRICNAME
                md["order"] = ORDERNAME
                if METRICNAME == "adaptive_coverage":
                    md["max_buff_size"] = BUFF_SIZE * 2
                    md["min_buff_size"] = BUFF_SIZE / 2
                    md["threshold_change"] = 0.01
                md["buff_size"] = BUFF_SIZE
                with open(foldername + "/metadata.json", "w") as f:
                    json.dump(md, f)
                foldergrowth = foldername + "/growth"
                if not os.path.exists(foldergrowth):
                    os.makedirs(foldergrowth)
                log.info("Plot growth")
                plot.plot_growth(
                    G_graph[name],
                    order_growth,
                    foldergrowth,
                    built=BUILT,
                    color_built="firebrick",
                    color_added="steelblue",
                    color_newest="darkgreen",
                    node_size=8,
                )
                plot.make_growth_video(
                    foldergrowth, foldergrowth + "/growth_video.mp4", fps=3
                )
                log.info("Plot growth with buffer and metrics")
                foldergrowth_buff = foldername + "/growth_buffer"
                if not os.path.exists(foldergrowth_buff):
                    os.makedirs(foldergrowth_buff)
                plot.plot_growth(
                    G_graph[name],
                    order_growth,
                    foldergrowth_buff,
                    built=BUILT,
                    color_built="firebrick",
                    color_added="steelblue",
                    color_newest="darkgreen",
                    node_size=8,
                    buffer=True,
                    plot_metrics=True,
                    growth_cov=metrics_dict["coverage"],
                    growth_xx=metrics_dict["xx"],
                    growth_dir=metrics_dict["directness"],
                    growth_reldir=metrics_dict["relative_directness"],
                )
                plot.make_growth_video(
                    foldergrowth_buff, foldergrowth_buff + "/growth_video.mp4", fps=3
                )
                fig, ax = plot.plot_order_growth(
                    G_graph[name],
                    order_growth,
                    show=False,
                    save=True,
                    close=True,
                    filepath=foldername + "/order_growth.png",
                )
                log.info("Plot metrics")
                for met in metrics_dict:
                    if met == "xx":
                        pass
                    else:
                        fig, ax = plt.subplots(figsize=(16, 9))
                        sns.lineplot(
                            x=metrics_dict["xx"], y=metrics_dict[met], ax=ax, marker="o"
                        )
                        ax.set_xlabel("Meters built")
                        plt.tight_layout()
                        fig.savefig(foldername + f"/{met}.png", dpi=100)
                        plt.close()
            for METRICNAME in ranking_func:
                log.info(
                    f"Start computation for metric {METRICNAME}, order {ORDERNAME}"
                )
                metrics_dict, order_growth = growth.order_ranked_network_growth(
                    G_graph[name],
                    built=BUILT,
                    keep_connected=CONNECTED,
                    order=ORDERNAME,
                    ranking_func=ranking_func[METRICNAME],
                    save_metrics=True,
                    buff_size_metrics=BUFF_SIZE,
                )
                foldername = (
                    "./data/processed/ignored_files/utg/"
                    + name
                    + "/"
                    + METRICNAME
                    + "_"
                    + ORDERNAME
                )
                if CONNECTED:
                    foldername += "_connected"
                if BUILT:
                    foldername += "_built"
                if not os.path.exists(foldername):
                    os.makedirs(foldername)
                with open(foldername + "/order_growth.json", "w") as f:
                    json.dump(order_growth, f)
                with open(foldername + "/metrics_growth.json", "w") as f:
                    json.dump(metrics_dict, f)
                md = {}
                md["growth"] = "ranked"
                md["built"] = BUILT
                md["keep_connected"] = CONNECTED
                md["metric"] = METRICNAME
                md["order"] = ORDERNAME
                md["buff_size"] = BUFF_SIZE
                with open(foldername + "/metadata.json", "w") as f:
                    json.dump(md, f)
                foldergrowth = foldername + "/growth"
                if not os.path.exists(foldergrowth):
                    os.makedirs(foldergrowth)
                log.info("Plot growth")
                plot.plot_growth(
                    G_graph[name],
                    order_growth,
                    foldergrowth,
                    built=BUILT,
                    color_built="firebrick",
                    color_added="steelblue",
                    color_newest="darkgreen",
                    node_size=8,
                )
                plot.make_growth_video(
                    foldergrowth, foldergrowth + "/growth_video.mp4", fps=3
                )
                log.info("Plot growth with buffer and metrics")
                foldergrowth_buff = foldername + "/growth_buffer"
                if not os.path.exists(foldergrowth_buff):
                    os.makedirs(foldergrowth_buff)
                plot.plot_growth(
                    G_graph[name],
                    order_growth,
                    foldergrowth_buff,
                    built=BUILT,
                    color_built="firebrick",
                    color_added="steelblue",
                    color_newest="darkgreen",
                    node_size=8,
                    buffer=True,
                    plot_metrics=True,
                    growth_cov=metrics_dict["coverage"],
                    growth_xx=metrics_dict["xx"],
                    growth_dir=metrics_dict["directness"],
                    growth_reldir=metrics_dict["relative_directness"],
                )
                plot.make_growth_video(
                    foldergrowth_buff, foldergrowth_buff + "/growth_video.mp4", fps=3
                )
                fig, ax = plot.plot_order_growth(
                    G_graph[name],
                    order_growth,
                    show=False,
                    save=True,
                    close=True,
                    filepath=foldername + "/order_growth.png",
                )
                log.info("Plot metrics")
                for met in metrics_dict:
                    if met == "xx":
                        pass
                    else:
                        fig, ax = plt.subplots(figsize=(16, 9))
                        sns.lineplot(
                            x=metrics_dict["xx"], y=metrics_dict[met], ax=ax, marker="o"
                        )
                        ax.set_xlabel("Meters built")
                        plt.tight_layout()
                        fig.savefig(foldername + f"/{met}.png", dpi=100)
                        plt.close()
        log.info("Finished !")
        # foldername = (
        #     "./data/processed/ignored_files/utg/"
        #     + name
        #     + "/"
        #     + "random_trials"
        #     + "_"
        #     + ORDERNAME
        # )
        # if CONNECTED:
        #     foldername += "_connected"
        # if BUILT:
        #     foldername += "_built"
        # if not os.path.exists(foldername):
        #     os.makedirs(foldername)
        # NUM_TRIALS = 1000
        # md = {}
        # md["growth"] = "ranked"
        # md["built"] = BUILT
        # md["keep_connected"] = CONNECTED
        # md["metric"] = "random"
        # md["order"] = ORDERNAME
        # md["buff_size"] = BUFF_SIZE
        # md["trials"] = NUM_TRIALS
        # with open(foldername + "/metadata.json", "w") as f:
        #     json.dump(md, f)
        # log.info("Start random computations")
        # for i in range(NUM_TRIALS):
        #     metrics_dict, order_growth = growth.order_ranked_network_growth(
        #         G_graph[name],
        #         built=BUILT,
        #         keep_connected=CONNECTED,
        #         order=ORDERNAME,
        #         ranking_func=metrics.growth_random,
        #         save_metrics=True,
        #         buff_size_metrics=BUFF_SIZE,
        #     )
        #     with open(foldername + f"/order_growth_{i:03}.json", "w") as f:
        #         json.dump(order_growth, f)
        #     with open(foldername + f"/metrics_growth_{i:03}.json", "w") as f:
        #         json.dump(metrics_dict, f)
