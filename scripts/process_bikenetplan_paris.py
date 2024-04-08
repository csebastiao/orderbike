""""""

import os
import networkx as nx
import json
from utg import utils
from orderbike import metrics, growth, plot

if __name__ == "__main__":
    G = utils.load_graph("./data/processed/plan_paris/paris_bikeplan.graphml")
    G = nx.MultiGraph(G)
    for e in G.edges:
        G.edges[e]["built"] = int(G.edges[e]["built"])
        G.edges[e]["length"] = float(G.edges[e]["length"])
    for n in G.nodes:
        G.nodes[n]["x"] = float(G.nodes[n]["x"])
        G.nodes[n]["y"] = float(G.nodes[n]["y"])
    rankings = {}
    rankings["random"] = metrics.growth_random
    rankings["betweenness"] = metrics.growth_betweenness
    for r in rankings:
        for ORDERNAME in ["subtractive", "additive"]:
            for CONNECTED in [True, False]:
                for BUILT in [True, False]:
                    order_growth = growth.order_ranked_network_growth(
                        G,
                        built=BUILT,
                        keep_connected=CONNECTED,
                        order=ORDERNAME,
                        ranking_func=rankings[r],
                    )
                    foldername = (
                        "./data/processed/plan_paris/ignored_growth/"
                        + r
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
                    utils.save_graph(G, foldername + "/graph.graphml")
                    plot.plot_growth(
                        G,
                        order_growth,
                        foldername,
                        built=BUILT,
                        color_built="firebrick",
                        color_added="steelblue",
                        color_newest="darkgreen",
                        node_size=8,
                    )
                    plot.make_growth_video(
                        foldername, foldername + "/growth_video.mp4", fps=3
                    )
