# -*- coding: utf-8 -*-
"""
Test metrics with part of the network built, keeping the network
connected and doing so in a subtractive or additive manner on a toy graph of
Copenhagen bicycle network.
"""


from nerds_osmnx import simplification as sf
from blp import growth
from blp import plot
import networkx as nx
import osmnx as ox


if __name__ == "__main__":
    com_G = nx.read_gpickle(
        "../data/all_graph/copenhagen_protected_bicycling_graph.gpickle")
    lcc_G = com_G.subgraph(max(nx.connected_components(com_G),
                               key=len)).copy()
    node_pos = [12.5500, 55.6825] # find central node
    n = ox.nearest_nodes(lcc_G, *node_pos)
    RAD = 1000 # make subgraph as radius around central node
    rad_G = nx.ego_graph(lcc_G, n, radius=RAD, distance='length')
    rad_G.graph['simplified'] = False
    sim_G = sf.momepy_simplify_graph(nx.MultiDiGraph(rad_G)) # simplify
    G = sf.multidigraph_to_graph(sim_G)

    # Make built subgraph that we can't touch during growth
    first_pos = [12.5385, 55.6854]
    second_pos = [12.5648, 55.6785]
    first_n = ox.nearest_nodes(G, *first_pos)
    second_n = ox.nearest_nodes(G, *second_pos)
    G_first_built = nx.ego_graph(G, first_n, radius=RAD/3,
                                 distance='length').copy()
    G_second_built = nx.ego_graph(G, second_n, radius=RAD/3,
                                  distance='length').copy()
    nx.set_edge_attributes(G, 0, name='built')
    for edge in G.edges:
        if edge in G_first_built.edges or edge in G_second_built.edges:
            G.edges[edge]['built'] = 1

    # G_built = nx.ego_graph(G, n, radius=RAD/2, distance='length').copy()
    # nx.set_edge_attributes(G, 0, name='built')
    # for edge in G.edges:
    #     if edge in G_built.edges:
    #         G.edges[edge]['built'] = 1

    local_proj = 'epsg:25832'
    buff_size = 200

    # import geopandas as gpd
    # import matplotlib.pyplot as plt
    # import shapely
    # fig, ax = plt.subplots()
    # ax.set_axis_off()
    # buff_size_list = [500, 200, 2]
    # color_list = [0.1, 0.5, 1]
    # color_dict = dict(zip(buff_size_list, color_list))
    # for buff_size in buff_size_list:
    #     test_buff = dict()
    #     for edge in G.edges:
    #         test_buff[edge] = shapely.ops.transform(
    #             proj.transform, G.edges[edge]['geometry']).buffer(buff_size)
    #     poly = shapely.ops.unary_union(list(test_buff.values()))
    #     p = gpd.GeoSeries(poly)
    #     p.plot(ax=ax, color='dodgerblue', alpha=color_dict[buff_size])

    name = f"../data/test/s{RAD}_copenhagen_multiple"

    orders = ['subtractive']
    list_built = [True]
    list_connected = [True]
    strat_list = ['random']
    metric_list = ['directness', 'coverage', 'relative_coverage']
    for built in list_built:
        for connected in list_connected:
            for order in orders:
                if order == 'subtractive':
                    rev = True
                else:
                    rev = False
                for strat in strat_list:
                    if strat == 'random':
                        f_name = growth.random_growth(
                            G, name, order, local_proj, buff_size=buff_size,
                            override_naming=False, built=built,
                            keep_connected=connected, save_network=True,
                            save_metrics=True)
                        plot.make_image_from_array(f_name, G=None, order=order,
                                                   built=built,
                                                   cmap='coolwarm')
                        plot.make_video_from_image(f_name + "/network_images",
                                                   reverse=rev,
                                                   video_name=None, fps=5)
                        plot.plot_coverage_directness(f_name,
                                                      optimized=None, 
                                                      coverage_name=None,
                                                      directness_name=None,
                                                      save=True)
                    elif strat == 'betweenness':
                        f_name = growth.betweenness_growth(
                            G, name, order, local_proj, buff_size=buff_size,
                            override_naming=False, built=built,
                            keep_connected=connected, save_network=True,
                            save_metrics=True)
                        plot.make_image_from_array(f_name, G=None, order=order,
                                                   built=built,
                                                   cmap='coolwarm')
                        plot.make_video_from_image(f_name + "/network_images",
                                                   reverse=rev,
                                                   video_name=None, fps=5)
                        plot.plot_coverage_directness(f_name,
                                                      optimized=None, 
                                                      coverage_name=None,
                                                      directness_name=None,
                                                      save=True)
                    elif strat == 'greedy_optimization':
                        for metric_choice in metric_list:
                            if order == 'additive':
                                f_name = growth.optimize_additive_growth(
                                    G, name, metric_choice, local_proj,
                                    buff_size=buff_size, override_naming=False,
                                    built=built, keep_connected=connected,
                                    profiling=True, save_network=True,
                                    save_metrics=True)
                                plot.make_image_from_array(f_name, G=None,
                                                           order=order,
                                                            built=built, 
                                                            cmap='coolwarm')
                                plot.make_video_from_image(
                                    f_name + "/network_images", reverse=False,
                                    video_name=None, fps=5)
                            elif order == 'subtractive':
                                f_name = growth.optimize_subtractive_growth(
                                    G, name, metric_choice, local_proj,
                                    buff_size=buff_size, override_naming=False,
                                    built=built, keep_connected=connected,
                                    profiling=True, save_network=True,
                                    save_metrics=True)
                                plot.make_image_from_array(f_name, G=None,
                                                           order=order,
                                                           built=built,
                                                           cmap='coolwarm')
                                plot.make_video_from_image(
                                    f_name + "/network_images", reverse=True,
                                    video_name=None, fps=5)
                            plot.plot_coverage_directness(
                                f_name, optimized=metric_choice, 
                                coverage_name=None, directness_name=None,
                                save=True)
            