# -*- coding: utf-8 -*-
"""
From a list of LineStrings, create a simplified networkx street network of Paris. The list of LineStrings is a manually modified version of the bicycle plan that can be found on the OpenData Paris website: https://opendata.paris.fr/explore/dataset/plan-velo-2026/map/
"""

import geopandas as gpd
import momepy as mp
import networkx as nx

from orderbike import plot

if __name__ == "__main__":
    gdf = gpd.read_file("./data/processed/plan_paris/mun_edges_all_cleaned.gpkg")
    gdf_filt = gdf[gdf.geometry.apply(lambda x: True if len(x.geoms) == 1 else False)]
    gdf_ls = gdf_filt.copy()
    gdf_ls.geometry = gdf_ls.geometry.apply(lambda x: x.geoms[0])
    gdf_simp = mp.remove_false_nodes(gdf_ls)
    G = mp.gdf_to_nx(gdf_simp, multigraph=True, directed=False, length="length")
    for n in G:
        G.nodes[n]["x"] = n[0]
        G.nodes[n]["y"] = n[1]
    G = nx.convert_node_labels_to_integers(G)
    ec = {}
    for edge in G.edges:
        if G.edges[edge]["attribute"] == "built":
            ec[edge] = "red"
        elif G.edges[edge]["attribute"] == "planned":
            ec[edge] = "green"
        else:
            ec[edge] = "gray"
    plot.plot_graph(G, edge_color=ec, save=False, show=True, close=False)
