# -*- coding: utf-8 -*-
"""
To plot and look at useful informations on step and length
relationship with coverage and directness for different growth
strategy.
"""

import os
import pickle
import numpy as np
import matplotlib as mpl
from matplotlib import pyplot as plt
import seaborn as sns
import networkx as nx
from blp import utils

if __name__ == "__main__":
    #%% For both directness and coverage in same figure
    
    mpl.rcParams.update({'font.size': 20})
    sns.set_style('ticks')
    palette = sns.color_palette('Paired')
    fig, axs = plt.subplots(1, 2, figsize=(20, 10))
    sns.despine(fig=fig)
    axs[0].set_xlabel("Length ($m$)")
    axs[0].set_xlim([7500, 40500])
    axs[0].set_ylim([1*10**6, 9*10**6])
    axs[0].set_ylabel("Coverage ($m^2$)")
    axs[1].set_xlabel("Length ($m$)")
    axs[1].set_xlim([7500, 40500])
    axs[1].set_ylim([0.600, 0.9])
    axs[1].set_ylabel("Directness")
    
    # To plot random aggregate

    add = '../data/s2000_copenhagen_built_connected_additive_bf200_random_folder'
    sub = '../data/s2000_copenhagen_built_connected_subtractive_bf200_random_folder'
    add_folders = os.listdir(add)
    sub_folders = os.listdir(sub)
    G = nx.read_gpickle(
        '../data/s2000_copenhagen_built_connected_additive_bf200_directness/final_network.gpickle')
    coverage_list = []
    length_list = []
    for f in add_folders:
        with open(add + '/' + f + "/arrcov.pickle", "rb") as fp:
            val = pickle.load(fp)
            coverage_list.append(val)
        with open(add + '/' + f + "/arrchoice.pickle", "rb") as fp:
            choice = pickle.load(fp)
            actual_edges = [edge for edge in G.edges if edge not in choice]
            length_batch = []
            total_length = 0
            for e in actual_edges:
                total_length += G.edges[e]['length']
            length_batch.append(total_length)
            for edge in choice:
                actual_edges.append(edge)
                total_length = 0
                for e in actual_edges:
                    total_length += G.edges[e]['length']
                length_batch.append(total_length)
            length_list.append(length_batch)
        # To plot every random trajectory

        # axs[0].plot(length_batch, val, linewidth=1, alpha=0.08,
        #             color=palette[7])

    average_coverage = np.mean(coverage_list, axis=0)
    std_coverage = np.std(coverage_list, axis=0)
    average_length = np.mean(length_list, axis=0)
    std_length = np.std(length_list, axis=0)
    
    # Some useful informations

    # print(utils.get_area_under_curve(average_coverage, xx=average_length,
    #                                  normalize_y=True, normalize_x=True))
    # print(average_length[50], average_length[100], average_length[150])
    # added_length = length_list[0][-1] - length_list[0][0]
    # fqid = next(idx for idx, val in enumerate(average_length)
    #             if val > length_list[0][0] + added_length*1/4)
    # sqid = next(idx for idx, val in enumerate(average_length)
    #             if val > length_list[0][0] + added_length*2/4)
    # tqid = next(idx for idx, val in enumerate(average_length)
    #             if val > length_list[0][0] + added_length*3/4)
    # print(fqid, sqid, tqid)

    axs[0].plot(average_length, average_coverage,
                color=palette[7], label='Additive, Random', linewidth=4)
    axs[0].fill_between(average_length,
                     average_coverage-std_coverage,
                     average_coverage+std_coverage, color=palette[7],
                     alpha=0.4)

    coverage_list = []
    length_list = []
    for f in sub_folders:
        with open(sub + '/' + f + "/arrcov.pickle", "rb") as fp:
            val = pickle.load(fp)
            val.reverse()
            coverage_list.append(val)
        with open(sub + '/' + f + "/arrchoice.pickle", "rb") as fp:
            choice = pickle.load(fp)
            choice.reverse()
            actual_edges = [edge for edge in G.edges if edge not in choice]
            length_batch = []
            total_length = 0
            for e in actual_edges:
                total_length += G.edges[e]['length']
            length_batch.append(total_length)
            for edge in choice:
                actual_edges.append(edge)
                total_length = 0
                for e in actual_edges:
                    total_length += G.edges[e]['length']
                length_batch.append(total_length)
            length_list.append(length_batch)
        # To plot every random trajectory

        # axs[0].plot(length_batch, val, linewidth=1, alpha=0.08,
        #             color=palette[9])

    average_coverage = np.mean(coverage_list, axis=0)
    std_coverage = np.std(coverage_list, axis=0)
    average_length = np.mean(length_list, axis=0)
    std_length = np.std(length_list, axis=0)

    # Some useful informations

    # print(length_list[0][-51], length_list[0][-101], length_list[0][-151])
    # print(utils.get_area_under_curve(average_coverage, xx=average_length,
    #                                  normalize_y=True, normalize_x=True))
    # print(average_length[50], average_length[100], average_length[150])
    # added_length = length_list[0][-1] - length_list[0][0]
    # fqid = next(idx for idx, val in enumerate(average_length)
    #             if val > length_list[0][0] + added_length*1/4)
    # sqid = next(idx for idx, val in enumerate(average_length)
    #             if val > length_list[0][0] + added_length*2/4)
    # tqid = next(idx for idx, val in enumerate(average_length)
    #             if val > length_list[0][0] + added_length*3/4)
    # print(fqid, sqid, tqid)

    axs[0].plot(average_length, average_coverage,
                color=palette[9], label='Subtractive, Random', linewidth=4)
    axs[0].fill_between(average_length,
                     average_coverage-std_coverage,
                     average_coverage+std_coverage, color=palette[9],
                     alpha=0.4)
    
    directness_list = []
    length_list = []
    for f in add_folders:
        with open(add + '/' + f + "/arrdir.pickle", "rb") as fp:
            val = pickle.load(fp)
            directness_list.append(val)
        with open(add + '/' + f + "/arrchoice.pickle", "rb") as fp:
            choice = pickle.load(fp)
            actual_edges = [edge for edge in G.edges if edge not in choice]
            length_batch = []
            total_length = 0
            for e in actual_edges:
                total_length += G.edges[e]['length']
            length_batch.append(total_length)
            for edge in choice:
                actual_edges.append(edge)
                total_length = 0
                for e in actual_edges:
                    total_length += G.edges[e]['length']
                length_batch.append(total_length)
            length_list.append(length_batch)
        # To plot every random trajectory

        # axs[1].plot(length_batch, val, linewidth=1, alpha=0.08,
        #             color=palette[7])

    average_directness = np.mean(directness_list, axis=0)
    std_directness = np.std(directness_list, axis=0)
    average_length = np.mean(length_list, axis=0)
    std_length = np.std(length_list, axis=0)

    # Some useful informations
    
    # print(utils.get_area_under_curve(average_directness, xx=average_length,
    #                                  normalize_y=False, normalize_x=True))

    axs[1].plot(average_length, average_directness,
                color=palette[7], label='Additive, Random', linewidth=4)
    axs[1].fill_between(average_length,
                     average_directness-std_directness,
                     average_directness+std_directness, color=palette[7],
                     alpha=0.4)

    directness_list = []
    length_list = []
    for f in sub_folders:
        with open(sub + '/' + f + "/arrdir.pickle", "rb") as fp:
            val = pickle.load(fp)
            val.reverse()
            directness_list.append(val)
        with open(sub + '/' + f + "/arrchoice.pickle", "rb") as fp:
            choice = pickle.load(fp)
            choice.reverse()
            actual_edges = [edge for edge in G.edges if edge not in choice]
            length_batch = []
            total_length = 0
            for e in actual_edges:
                total_length += G.edges[e]['length']
            length_batch.append(total_length)
            for edge in choice:
                actual_edges.append(edge)
                total_length = 0
                for e in actual_edges:
                    total_length += G.edges[e]['length']
                length_batch.append(total_length)
            length_list.append(length_batch)
        # To plot every random trajectory

        # axs[1].plot(length_batch, val, linewidth=1, alpha=0.08,
        #             color=palette[9])

    average_directness = np.mean(directness_list, axis=0)
    std_directness = np.std(directness_list, axis=0)
    average_length = np.mean(length_list, axis=0)
    std_length = np.std(length_list, axis=0)
    # print(utils.get_area_under_curve(average_directness, xx=average_length,
    #                                  normalize_y=False, normalize_x=True))
    axs[1].plot(average_length, average_directness,
                color=palette[9], label='Subtractive, Random', linewidth=4)
    axs[1].fill_between(average_length,
                     average_directness-std_directness,
                     average_directness+std_directness, color=palette[9],
                     alpha=0.4)

    # To plot other growth strategy
    
    f_list = ['../data/s2000_copenhagen_built_connected_additive_bf200_directness',
              '../data/s2000_copenhagen_built_connected_additive_bf200_relative_coverage',
              '../data/s2000_copenhagen_built_connected_additive_bf200_betweenness',
              '../data/s2000_copenhagen_built_connected_subtractive_bf200_directness',
              '../data/s2000_copenhagen_built_connected_subtractive_bf200_relative_coverage',
              '../data/s2000_copenhagen_built_connected_subtractive_bf200_betweenness',
              '../data/s2000_copenhagen_built_connected_additive_bf200_coverage',
              '../data/s2000_copenhagen_built_connected_subtractive_bf200_coverage']
    coverage_list = []
    directness_list = []
    choice_list = []
    length_list = []
    for folder_name in f_list:
        with open(folder_name + "/arrcov.pickle", "rb") as fp:
            coverage_list.append(pickle.load(fp))
        with open(folder_name + "/arrdir.pickle", "rb") as fp:
            directness_list.append(pickle.load(fp))
        with open(folder_name + "/arrchoice.pickle", "rb") as fp:
            choice_list.append(pickle.load(fp))
        # Reverse subtractive list
    coverage_list[3].reverse()
    directness_list[3].reverse()         
    coverage_list[4].reverse()
    directness_list[4].reverse()
    coverage_list[5].reverse()
    directness_list[5].reverse()
    coverage_list[7].reverse()
    directness_list[7].reverse()
    choice_list[3].reverse()      
    choice_list[4].reverse()
    choice_list[5].reverse()
    choice_list[7].reverse()
    # Find length of network at every step
    for choice_history in choice_list:
        actual_edges = [edge for edge in G.edges if edge not in choice_history]
        length_batch = []
        total_length = 0
        for e in actual_edges:
            total_length += G.edges[e]['length']
        length_batch.append(total_length)
        for edge in choice_history:
            actual_edges.append(edge)
            total_length = 0
            for e in actual_edges:
                total_length += G.edges[e]['length']
            length_batch.append(total_length)
        length_list.append(length_batch)
        

    axs[1].plot(length_list[0], directness_list[0],
                linewidth=4, label='Additive, Directness',
                color=palette[0])
    axs[1].plot(length_list[1], directness_list[1],
                linewidth=4, label='Additive, Relative coverage',
                color=palette[2])
    axs[1].plot(length_list[2], directness_list[2],
                linewidth=4, label='Additive, Betweenness',
                color=palette[4])
    axs[1].plot(length_list[3], directness_list[3],
                linewidth=4, label='Subtractive, Directness',
                color=palette[1])
    axs[1].plot(length_list[4], directness_list[4],
                linewidth=4, label='Subtractive, Relative coverage',
                color=palette[3])
    axs[1].plot(length_list[5], directness_list[5],
                linewidth=4, label='Subtractive, Betweenness',
                color=palette[5])
    # axs[1].plot(length_list[6], directness_list[6],
    #             linewidth=4, label='Additive, Coverage',
    #             color=palette[10])
    # axs[1].plot(length_list[7], directness_list[7],
    #             linewidth=4, label='Subtractive, Coverage',
    #             color=palette[11])
    
    axs[0].plot(length_list[0], coverage_list[0],
                linewidth=4, label='Additive, Directness',
                color=palette[0])
    axs[0].plot(length_list[1], coverage_list[1],
                linewidth=4, label='Additive, Relative coverage',
                color=palette[2])
    axs[0].plot(length_list[2], coverage_list[2],
                linewidth=4, label='Additive, Betweenness',
                color=palette[4])
    axs[0].plot(length_list[3], coverage_list[3],
                linewidth=4, label='Subtractive, Directness',
                color=palette[1])
    axs[0].plot(length_list[4], coverage_list[4],
                linewidth=4, label='Subtractive, Relative coverage',
                color=palette[3])
    axs[0].plot(length_list[5], coverage_list[5],
                linewidth=4, label='Subtractive, Betweenness',
                color=palette[5])
    # axs[0].plot(length_list[6], coverage_list[6],
    #             linewidth=4, label='Additive, Coverage',
    #             color=palette[10])
    # axs[0].plot(length_list[7], coverage_list[7],
    #             linewidth=4, label='Subtractive, Coverage',
    #             color=palette[11])
    
    axs[0].legend()
    # axs[1].legend()

    #%% To plot single metric and length informations
    f_list = ['../data/s2000_copenhagen_built_connected_additive_bf200_directness',
              '../data/s2000_copenhagen_built_connected_additive_bf200_relative_coverage',
              '../data/s2000_copenhagen_built_connected_additive_bf200_betweenness',
              '../data/s2000_copenhagen_built_connected_subtractive_bf200_directness',
              '../data/s2000_copenhagen_built_connected_subtractive_bf200_relative_coverage',
              '../data/s2000_copenhagen_built_connected_subtractive_bf200_betweenness']
    coverage_list = []
    directness_list = []
    choice_list = []
    length_list = []
    for folder_name in f_list:
        with open(folder_name + "/arrcov.pickle", "rb") as fp:
            coverage_list.append(pickle.load(fp))
        with open(folder_name + "/arrdir.pickle", "rb") as fp:
            directness_list.append(pickle.load(fp))
        with open(folder_name + "/arrchoice.pickle", "rb") as fp:
            choice_list.append(pickle.load(fp))

    # Reverse subtractive list
    coverage_list[3].reverse()
    coverage_list[4].reverse()
    coverage_list[5].reverse()
    directness_list[3].reverse()
    directness_list[4].reverse()
    directness_list[5].reverse()
    choice_list[3].reverse()      
    choice_list[4].reverse()
    choice_list[5].reverse()
    G = nx.read_gpickle(
        '../data/s2000_copenhagen_built_connected_additive_bf200_directness/final_network.gpickle')

    # Find length of network at every step
    for choice_history in choice_list:
        actual_edges = [edge for edge in G.edges if edge not in choice_history]
        length_batch = []
        total_length = 0
        for e in actual_edges:
            total_length += G.edges[e]['length']
        length_batch.append(total_length)
        for edge in choice_history:
            actual_edges.append(edge)
            total_length = 0
            for e in actual_edges:
                total_length += G.edges[e]['length']
            length_batch.append(total_length)
        length_list.append(length_batch)

    mpl.rcParams.update({'font.size': 25})
    sns.set_style('ticks')
    fig, axs = plt.subplots(figsize=(20, 10))
    palette = sns.color_palette('Paired')
    sns.despine(fig=fig)

    # axs.set_xlabel("Step)")
    # axs.set_xlim([-1, 203])
    axs.set_xlabel("Length ($m$)")
    axs.set_xlim([7500, 40500])

    axs.set_ylim([0.675, 0.875])
    axs.set_ylabel("Directness")
    # axs.set_ylim([1*10**6, 9*10**6])
    # axs.set_ylabel("Coverage ($m^2$)")

    # Replace length_list[] by len(directness_list[]) for step
    # Replace directness_list by coverage_list for coverage 
    axs.plot(length_list[0], directness_list[0],
                linewidth=4, label='Additive, Directness',
                color=palette[0])
    axs.plot(length_list[1], directness_list[1],
                linewidth=4, label='Additive, Relative coverage',
                color=palette[2])
    axs.plot(length_list[2], directness_list[2],
                linewidth=4, label='Additive, Betweenness',
                color=palette[4])
    axs.plot(length_list[3], directness_list[3],
                linewidth=4, label='Subtractive, Directness',
                color=palette[1])
    axs.plot(length_list[4], directness_list[4],
                linewidth=4, label='Subtractive, Relative coverage',
                color=palette[3])
    axs.plot(length_list[5], directness_list[5],
                linewidth=4, label='Subtractive, Betweenness',
                color=palette[5])
    axs.legend()
    plt.tight_layout()


    # To look at link between step and length

    # added_length = length_list[0][-1] - length_list[0][0]
    # for length_hist in length_list:
    #     fqid = next(idx for idx, val in enumerate(length_hist)
    #                 if val > length_list[0][0] + added_length*1/4)
    #     sqid = next(idx for idx, val in enumerate(length_hist)
    #                 if val > length_list[0][0] + added_length*2/4)
    #     tqid = next(idx for idx, val in enumerate(length_hist)
    #                 if val > length_list[0][0] + added_length*3/4)
    #     print(fqid, sqid, tqid)
    mpl.rcParams.update({'font.size': 25})
    sns.set_style('ticks')
    fig, axs = plt.subplots(figsize=(20, 10))
    palette = sns.color_palette('Paired')
    sns.despine(fig=fig)
    axs.set_xlabel("Step")
    axs.set_xlim([-1, 203])
    axs.set_ylim([7500, 40500])
    axs.set_ylabel("Length ($m$)")
    axs.plot(range(len(length_list[0])), length_list[0],
                linewidth=4, label='Additive, Directness',
                color=palette[0])
    axs.plot(range(len(length_list[1])), length_list[1],
                linewidth=4, label='Additive, Relative coverage',
                color=palette[2])
    axs.plot(range(len(length_list[2])), length_list[2],
                linewidth=4, label='Additive, Betweenness',
                color=palette[4])
    axs.plot(range(len(length_list[3])), length_list[3],
                linewidth=4, label='Subtractive, Directness',
                color=palette[1])
    axs.plot(range(len(length_list[4])), length_list[4],
                linewidth=4, label='Subtractive, Relative coverage',
                color=palette[3])
    axs.plot(range(len(length_list[5])), length_list[5],
                linewidth=4, label='Subtractive, Betweenness',
                color=palette[5])
    axs.legend()
    plt.tight_layout()
    
    length_dist = []
    for edge in G.edges:
        length_dist.append(G.edges[edge]['length'])
    ax = sns.histplot(length_dist, stat='percent', bins=10)
    ax.set_xlabel('Length ($m$)')