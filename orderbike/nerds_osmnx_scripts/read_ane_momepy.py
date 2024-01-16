# -*- coding: utf-8 -*-
"""
Based on files created with momepy to make a graph with the osmnx
convention, show how to use the 
nerds_osmnx.simplification.momepy_simplify_graph function.
"""


import networkx as nx
import osmnx as ox
import nerds_osmnx.simplification
import geopandas as gpd

if __name__ == "__main__":
    G = nx.read_graphml("g_ox.graphml")
    # Transform geometry attribute from a string 'LINESTRING (...)' to 
    # actual shapely LineString object, same for length and node x and y
    gpd_edges = gpd.read_file("ox_edges.gpkg")
    geometry_dict = dict(zip(
        zip(gpd_edges['u'], gpd_edges['v'], gpd_edges['key']),
        gpd_edges['geometry']
        ))
    nx.set_edge_attributes(G, geometry_dict, name='geometry')
    length_dict = dict(zip(
        zip(gpd_edges['u'], gpd_edges['v'], gpd_edges['key']),
        gpd_edges['length']
        ))
    nx.set_edge_attributes(G, length_dict, name='length')
    gpd_nodes = gpd.read_file("ox_nodes.gpkg")
    x_dict = dict(zip(gpd_nodes['osmid'], gpd_nodes['x']))
    y_dict = dict(zip(gpd_nodes['osmid'], gpd_nodes['y']))
    nx.set_node_attributes(G, x_dict, name='x')
    nx.set_node_attributes(G, y_dict, name='y')
    ox.plot_graph(G, figsize=(12, 8), bgcolor='w',
                  node_color='r', node_size=10,
                  edge_color='black', edge_linewidth=1)
    G_simple = nerds_osmnx.simplification.momepy_simplify_graph(G)
    ox.plot_graph(G_simple, figsize=(12, 8), bgcolor='w',
                  node_color='red', node_size=10,
                  edge_color='black', edge_linewidth=1)
    G_old = nerds_osmnx.simplification.simplify_graph(G)
    ox.plot_graph(G_old, figsize=(12, 8), bgcolor='w',
                  node_color='red', node_size=10,
                  edge_color='black', edge_linewidth=1)