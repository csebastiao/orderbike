# -*- coding: utf-8 -*-
"""
From a list of LineStrings, create a simplified networkx street network of Paris. The list of LineStrings is a manually modified version of the bicycle plan that can be found on the OpenData Paris website: https://opendata.paris.fr/explore/dataset/plan-velo-2026/map/
"""

import geopandas as gpd
import momepy as mp
import networkx as nx
import osmnx as ox
import shapely

from orderbike import plot

if __name__ == "__main__":
    # Read the GeoPackage manually made from QGIS
    gdf = gpd.read_file("./data/processed/plan_paris/mun_edges_graph_ready.gpkg")
    # Remove invalid geometry
    gdf_filt = gdf[gdf.geometry.apply(lambda x: True if len(x.geoms) == 1 else False)]
    gdf_ls = gdf_filt.copy()
    # Transform MultiLineString into LineString
    gdf_ls.geometry = gdf_ls.geometry.apply(lambda x: x.geoms[0])
    # Get a networkx MultiDigraph and add node coordinates
    G = mp.gdf_to_nx(gdf_ls, multigraph=True, directed=True, length="length")
    for n in G:
        G.nodes[n]["x"] = n[0]
        G.nodes[n]["y"] = n[1]
    H = G.copy()
    # Segmentize by having all edges being straight edges so osmnx can simplify it
    for e in G.edges:
        coord = G.edges[e]["geometry"].coords[:]
        if len(G.edges[e]["geometry"].coords[:]) > 2:
            attr = G.edges[e]["attribute"]
            for i in range(len(coord) - 1):
                H.add_node(coord[i + 1], x=coord[i + 1][0], y=coord[i + 1][1])
                egeom = shapely.LineString([coord[i], coord[i + 1]])
                H.add_edge(
                    coord[i],
                    coord[i + 1],
                    0,
                    geometry=egeom,
                    length=egeom.length,
                    attribute=attr,
                )
            H.remove_edge(*e)
    H = nx.convert_node_labels_to_integers(H)
    # Simplify while keeping the attribute about built and planned discriminated
    H = ox.simplify_graph(H, endpoint_attrs=["attribute"])
    ec = {}
    for edge in H.edges:
        if H.edges[edge]["attribute"] == "built":
            ec[edge] = "green"
        elif H.edges[edge]["attribute"] == "planned":
            ec[edge] = "red"
        else:
            ec[edge] = "gray"
    plot.plot_graph(H, edge_color=ec, save=False, show=True, close=False)
    for e in H.edges:
        if H.edges[e]["attribute"] == "built":
            H.edges[e]["built"] = 1
        elif H.edges[e]["attribute"] == "planned":
            H.edges[e]["built"] = 0
    ox.save_graphml(H, filepath="./data/processed/plan_paris/paris_bikeplan.graphml")
