# -*- coding: utf-8 -*-
"""
Toy MultiDiGraph to test out the various cases we could encounter in 
the process. Only thing not tested now is about directed edges.
"""


from nerds_osmnx.simplification import multidigraph_to_graph, simplify_graph
import networkx as nx
import osmnx as ox
import numpy as np


if __name__ == "__main__":
    G = nx.MultiDiGraph() # construct the graph
    G.add_node(1, x=1, y=1)
    G.add_node(2, x=2, y=1)
    G.add_node(3, x=2.5, y=1.5)
    G.add_node(4, x=3, y=2.5)
    G.add_node(5, x=3.5, y=3.5)
    G.add_node(6, x=3, y=4)
    G.add_node(7, x=3, y=5)
    G.add_node(8, x=3.5, y=5.5)
    G.add_node(9, x=3.5, y=6.5)
    G.add_node(10, x=4, y=7)
    G.add_node(11, x=5, y=8)
    G.add_node(12, x=6, y=8)
    G.add_node(13, x=6.5, y=8.5)
    G.add_node(14, x=7, y=9)
    G.add_node(15, x=7.5, y=8.5)
    G.add_node(16, x=8, y=8)
    G.add_node(17, x=7.5, y=7.5)
    G.add_node(18, x=7, y=7)
    G.add_node(19, x=6.5, y=7.5)
    # add length and osmid just for the osmnx function to work
    for i in range(1, 19):
        G.add_edge(i, i+1, 0, length=1, osmid=np.random.randint(1, 999999))
    G.add_node(20, x=4, y=4)
    G.add_node(21, x=4, y=5)
    G.add_edge(5, 20, 0, length=1, osmid=np.random.randint(1, 999999))
    G.add_edge(20, 21, 0, length=1, osmid=np.random.randint(1, 999999))
    G.add_edge(21, 8, 0, length=1, osmid=np.random.randint(1, 999999))
    G.add_edge(19, 12, 0, length=1, osmid=np.random.randint(1, 999999))
    # give three value of color to see the discrimination for an attribute
    for i in range(2, 8):
        G.edges[i, i+1, 0]['color'] = 1
    G.edges[1, 2, 0]['color'] = 2
    G.edges[5, 20, 0]['color'] = 1
    G.edges[20, 21, 0]['color'] = 1
    G.edges[21, 8, 0]['color'] = 1
    for i in range(8, 11):
        G.edges[i, i+1, 0]['color'] = 3
    for i in range(11, 19):
        G.edges[i, i+1, 0]['color'] = 2
    G.edges[19, 12, 0]['color'] = 2
    
    # add crs for the ox_plot_graph to work
    G.graph['crs'] = 'epsg:4326'
    
    
    ec = ox.plot.get_edge_colors_by_attr(G, 'color', cmap='Set1')
    ox.plot_graph(G, figsize=(12, 8), bgcolor='w',
                  node_color='black', node_size=30,
                  edge_color=ec, edge_linewidth=3)
    
    G_simple = simplify_graph(G, attributes='color')
    ec_s = ox.plot.get_edge_colors_by_attr(G_simple, 'color', cmap='Set1')
    ox.plot_graph(G_simple, figsize=(12, 8), bgcolor='w',
                  node_color='black', node_size=30,
                  edge_color=ec_s, edge_linewidth=3)
    
    G_graph, debug_dict = multidigraph_to_graph(G_simple, verbose=True,
                                                debug=True)
    ec_g = ox.plot.get_edge_colors_by_attr(G_graph, 'color', cmap='Set1')
    G_graph = nx.MultiGraph(G_graph)
    ox.plot_graph(G_graph, figsize=(12, 8), bgcolor='w', 
                  node_color='black', node_size=30,
                  edge_color=ec_g, edge_linewidth=3)