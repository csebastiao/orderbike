# -*- coding: utf-8 -*-
"""
Script to compute the Area Under the Curve of all metrics for all strategies on all graph.
"""


from utg import utils
import json
from orderbike.plot import plot_graph
import geopandas as gpd
from matplotlib import pyplot as plt
import networkx as nx
import shapely

if __name__ == "__main__":
    names = ["netviz_grid", "netviz_rc", "netviz_gd", "netviz_tb"]
    for idx, graphname in enumerate(
        [
            "grid",
            "radio_concentric",
            "grid_with_diagonal",
            "three_bridges",
        ]
    ):
        folderoots = f"./data/processed/ignored_files/paper/{graphname}/"
        G = utils.load_graph(folderoots + "graph.graphml")
        with open(
            folderoots + "coverage_additive_connected/order_growth_000.json"
        ) as f:
            val = json.load(f)
            val = [(arr[0], arr[1]) for arr in val]
        init_edges = [edge for edge in G.edges if edge not in val]
        fig_ind, ax_ind = plot_graph(
            G,
            filepath=folderoots + "/plots",
            figsize=(10, 10),
            buffer=False,
            buff_size=152,
            buff_color="grey",
            edge_color="black",
            edge_linewidth=4,
            node_color="black",
            node_size=200,
            show=False,
            save=False,
            close=False,
        )

        gdf_edge_ind = gpd.GeoDataFrame(geometry=[G.edges[init_edges[0]]["geometry"]])
        geom_node = [
            shapely.Point(G.nodes[n]["x"], G.nodes[n]["y"]) for n in init_edges[0][:2]
        ]
        gdf_edge = gpd.GeoDataFrame(
            geometry=list(nx.get_edge_attributes(G, "geometry").values())
        )
        gdf_node = gpd.GeoDataFrame(geometry=geom_node)
        gdf_node.plot(ax=ax_ind, color="#FF0000", zorder=3, markersize=200)
        gdf_edge_ind.plot(ax=ax_ind, zorder=3, color="#FF0000", linewidth=4)
        savename = folderoots + f"/plots/{names[idx]}.png"
        ax_ind.axis("off")
        fig_ind.savefig(savename)
        plt.close()
