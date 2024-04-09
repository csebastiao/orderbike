"""Script to find growth order on Paris bikeplan."""

import json
from utg import utils as utgut
from orderbike import metrics, growth
import tqdm

if __name__ == "__main__":
    G = utgut.load_graph("./data/processed/plan_paris/paris_bikeplan_graph.graphml")
    # STILL NEED TO CHECK IF WORKING WITH MULTIGRAPH
    for e in G.edges:
        G.edges[e]["built"] = int(G.edges[e]["built"])
        G.edges[e]["length"] = float(G.edges[e]["length"])
    for n in G.nodes:
        G.nodes[n]["x"] = float(G.nodes[n]["x"])
        G.nodes[n]["y"] = float(G.nodes[n]["y"])
    for it in tqdm.tqdm(range(100)):
        order_growth = growth.order_ranked_network_growth(
            G,
            built=True,
            keep_connected=True,
            order="additive",
            ranking_func=metrics.growth_random,
        )
        foldername = "./data/processed/plan_paris/ignored_growth/graph/trials_random_additive_built_connected/"
        with open(foldername + f"/order_growth_{it:05}.json", "w") as f:
            json.dump(order_growth, f)
