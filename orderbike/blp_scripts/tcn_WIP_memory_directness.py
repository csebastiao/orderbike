# -*- coding: utf-8 -*-
"""
Take a smaller and connected part of the bicycle network in Copenhagen
to test more quickly the workflow.
"""


# Profiling
import cProfile
import pstats
import io

# Custom packages
from nerds_osmnx import simplification as sf
from blp import directness
from blp import utils

# Network extraction, analysis and manipulation
import networkx as nx
import osmnx as ox

# Math
import numpy as np

# Visualization
from matplotlib import pyplot as plt


if __name__ == "__main__":
    pr = cProfile.Profile() # profiler to see what takes time in the script
    pr.enable()

    com_G = nx.read_gpickle(
        "../data/copenhagen_protected_bicycling_graph.gpickle")
    lcc_G = com_G.subgraph(max(nx.connected_components(com_G), key=len)).copy()
    node_pos = [12.5500, 55.6825] # find central node
    n = ox.nearest_nodes(lcc_G, *node_pos)
    RAD = 1000 # make subgraph as radius around central node
    rad_G = nx.ego_graph(lcc_G, n, radius=RAD, distance='length')
    rad_G.graph['simplified'] = False
    sim_G = sf.momepy_simplify_graph(nx.MultiDiGraph(rad_G)) # simplify
    fin_G = sf.multidigraph_to_graph(sim_G)
    G = fin_G.copy()
    G = utils.add_edge_index(fin_G)

    em, sm = directness.get_directness_matrix_networkx(G, separate=True)
    node_index = utils.create_node_index(G)
    edgelist = directness.get_edgelist_shortest_path(G)
    d = directness.directness_from_matrix(np.divide(em, sm))
    d_history = [d]
    choice_history = []

    PAD = len(str(len(G))) # know how many 0 you need to pad for png name
    folder_name = ("s" + f"{RAD}" +
                   "_copenhagen_linkwise_directness_every_edge")

    fig, ax = ox.plot_graph(  #this allow to save every step as a png
        nx.MultiDiGraph(G),
        filepath="../data/" + folder_name + f"/image_{0:0{PAD}}.png",
        save=True, show=False, close=True)
    xlim = ax.get_xlim() # keep same size of image for video
    ylim = ax.get_ylim()
    bb = [ylim[1], ylim[0], xlim[1], xlim[0]]

    COUNT = 1
    while len(G) > 2:
        batch_d = []
        batch_choice = []
        for u, v in G.edges:
            temp_sm = np.copy(sm)
            temp_em = np.copy(em)
            H = G.copy()
            edge_id = H.edges[u, v]['index']
            H.remove_edge(u, v)
            # TODO: Vectorize this ? Make it in igraph
            if edge_id in edgelist:
                for s, t in edgelist[edge_id]:
                    if nx.has_path(H, s, t):
                        path_length = nx.shortest_path_length(
                            H, source=s, target=t, weight='length')
                        temp_sm[node_index[s]][
                            node_index[t]] = path_length
                        temp_sm[node_index[t]][
                            node_index[s]] = path_length
                    else:
                        temp_em[node_index[s]][node_index[t]] = 0
                        temp_em[node_index[t]][node_index[s]] = 0
            sdm = np.divide(temp_em, temp_sm)
            batch_d.append(directness.directness_from_matrix(sdm))
            batch_choice.append([u, v])
        batch = zip(batch_d, batch_choice)
        new_d, choice = max(batch) # find max directness + edge we remove
        d_history.append(new_d)
        choice_history.append(choice)
        
        
        # TODO: Part where it gets messy
        index_choice = G.edges[choice[0], choice[1]]['index']
        rem = False
        batch = []
        for node in choice:
            if nx.degree(G, node) == 1:
                batch.append(node)
        for n in batch:
            directness.remove_matrix_node(em, node_index[n])
            directness.remove_matrix_node(sm, node_index[n])
            G.remove_node(n)
            rem = True
            node_index = utils.create_node_index(G)
        if rem is False:
            G.remove_edge(*choice)
            if index_choice in edgelist:
                for s, t in edgelist[index_choice]:
                    if nx.has_path(G, s, t):
                        path_length = nx.shortest_path_length(
                            G, source=s, target=t, weight='length')
                        sm[node_index[s]][node_index[t]] = path_length
                        sm[node_index[t]][node_index[s]] = path_length
                        sp = nx.shortest_path(
                            G, source=s, target=t, weight='length')
                        for f_node, s_node in zip(sp[:-1], sp[1:]):
                            edge_id = G.edges[f_node, s_node]['index']
                            if edge_id in edgelist:
                                edgelist[edge_id].append([sp[0], sp[-1]])
                            else:
                                edgelist[edge_id] = [[sp[0], sp[-1]]]
                    else:
                        em[node_index[s]][node_index[t]] = 0
                        em[node_index[t]][node_index[s]] = 0
                edgelist.pop(index_choice)
        else:
            edgelist.pop(index_choice)
            for node in choice:
                for edge in edgelist:
                    temp = []
                    for pair in edgelist[edge]:
                        if node in pair:
                            temp.append(pair)
                    for val in temp:
                        edgelist[edge].remove(val)

        # End of messy part
        fig, ax = ox.plot_graph(
            nx.MultiDiGraph(G), bbox=bb,
            filepath="../data/" + folder_name
            + f"/image_{COUNT:0{PAD}}.png",
            save=True, show=False, close=True)
        COUNT += 1

    plt.figure(figsize=(12,8))
    plt.plot(range(len(d_history)), d_history, linewidth=5)
    plt.xlabel("Step")
    plt.ylabel("Linkwise directness")

    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('tottime')
    ps.print_stats()

    with open('../data/' + folder_name + '.txt', 'w+') as f:
        f.write(s.getvalue())
