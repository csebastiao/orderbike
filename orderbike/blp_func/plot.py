# -*- coding: utf-8 -*-
"""
Functions to visualize results of the growth of a graph.
"""


import os
import pickle
import matplotlib as mpl
from matplotlib import pyplot as plt
import seaborn as sns
import cv2
import networkx as nx
import osmnx as ox
from blp import utils


def plot_hysteresis(
        add_folder, sub_folder, show_metric = 'both', description = None):
    """
    Create a plot of the hysteresis of directness, coverage or both
    metrics where the additive growth is in blue and the subtractive
    in red.

    Parameters
    ----------
    add_folder : str
        Path to the folder with the additive growth.
    sub_folder : str
        Path to the folder with the subtractive growth.
    show_metric : str, optional
        Metric shown, either both, directness or coverage.
        The default is 'both'.
    description : str, optional
        Added description as the title of the figure.
        The default is None.

    Raises
    ------
    ValueError
        Raised if an invalid value is used as an input for show_metric.
        Valid values are both, directness and coverage.

    """
    # Set better default style
    mpl.rcParams.update({'font.size': 16})
    sns.set_style('ticks')
    palette = sns.color_palette('deep')
    if show_metric not in ['both', 'directness', 'coverage']:
        raise ValueError("""
                         Invalid value for show_metric input, please put
                         both, directness or coverage.
                         """)
    if show_metric in ['directness', 'coverage']:
        if show_metric == 'directness':
            normalize_x = True
            normalize_y = False
            with open(add_folder + '/arrdir.pickle', "rb") as fp:
                add_val = pickle.load(fp)
            with open(sub_folder + '/arrdir.pickle', "rb") as fp:
                sub_val = pickle.load(fp)
        elif show_metric == 'coverage':
            normalize_x = True
            normalize_y = True
            with open(add_folder + '/arrcov.pickle', "rb") as fp:
                add_val = pickle.load(fp)
            with open(sub_folder + '/arrcov.pickle', "rb") as fp:
                sub_val = pickle.load(fp)
        sub_val.reverse()
        fig = plt.figure(figsize=(18, 9))
        ax = fig.add_subplot(1, 1, 1)
        ax.plot(range(len(add_val)), add_val, color=palette[0],
                label='additive')
        ax.plot(range(len(sub_val)), sub_val, color=palette[3],
                label='subtractive')
        # Measure difference in area under curve between sub and add
        auc = (utils.get_area_under_curve(
            sub_val, normalize_x=normalize_x, normalize_y=normalize_y)
               - utils.get_area_under_curve(
                   add_val, normalize_x=normalize_x, normalize_y=normalize_y))
        ax.set_xlabel("Step")
        ax.set_ylabel(show_metric)
        ax.set_title(f"""
                     AUC difference between subtractive and 
                     additive: {round(auc, 6)}, normalize_x is 
                     {normalize_x} and normalize_y is {normalize_y}.
                     """)
        ax.legend()
    else:
        with open(add_folder + '/arrdir.pickle', "rb") as fp:
            add_dir = pickle.load(fp)
        with open(sub_folder + '/arrdir.pickle', "rb") as fp:
            sub_dir = pickle.load(fp)
        sub_dir.reverse()
        with open(add_folder + '/arrcov.pickle', "rb") as fp:
            add_cov = pickle.load(fp)
        with open(sub_folder + '/arrcov.pickle', "rb") as fp:
            sub_cov = pickle.load(fp)
        sub_cov.reverse()
        fig, ax = plt.subplots(1, 2, figsize=(24, 12))
        ax[0].set_xlabel("Step")
        ax[0].set_ylabel("Coverage")
        ax[1].set_xlabel("Step")
        ax[1].set_ylabel("Directness")
        ax[0].plot(
            range(len(add_cov)), add_cov, color = palette[0],
            label='additive')
        ax[0].plot(
            range(len(sub_cov)), sub_cov, color = palette[3],
            label='subtractive')
        ax[1].plot(
            range(len(add_dir)), add_dir, color = palette[0],
            label='additive')
        ax[1].plot(
            range(len(sub_dir)), sub_dir, color = palette[3],
            label='subtractive')
        auc_cov = (utils.get_area_under_curve(
            sub_cov, normalize_x=True, normalize_y=True)
            - utils.get_area_under_curve(
                add_cov, normalize_x=True, normalize_y=True))
        ax[0].set_title(f"""
                     AUC difference between subtractive and 
                     additive: {round(auc_cov, 6)}, normalize_x is 
                     True and normalize_y is True.
                     """)
        auc_dir = (utils.get_area_under_curve(
            sub_dir, normalize_x=True, normalize_y=False)
            - utils.get_area_under_curve(
                add_dir, normalize_x=True, normalize_y=False))
        ax[1].set_title(f"""
                     AUC difference between subtractive and 
                     additive: {round(auc_dir, 6)}, normalize_x is 
                     True and normalize_y is False.
                     """)
        if description is not None:
            fig.suptitle(description)
        ax[0].legend()
        ax[1].legend()
    return fig, ax


def plot_coverage_directness(
        folder_name, optimized = None, coverage_name = None,
        directness_name = None, save = False):
    """
    Plot both the coverage and the directness. Highlighted in red is 
    the metric that is optimized, if there is one.

    Parameters
    ----------
    folder_name : str
        Path to the folder where the files for the coverage and the
        directness arrays are.
    optimized : str, optional
        Specify which metric was optimized to produce those values.
        coverage and relative_coverage will mark the coverage plot
        while directness, relative_directness and global_efficiency
        will mark the directness plot. If any other value is used, 
        a message is printed out and both plot are with the same color.
    coverage_name : str, optional
        Name of the pickle file with the coverage value, if None use
        a standardized name. The default is None.
    directness_name : str, optional
        Name of the pickle file with the directness value, if None use
        a standardized name. The default is None.
    optimized : str, optional
        DESCRIPTION. The default is 'coverage'.
    save : bool, optional
        If True, save the figure in the folder. The default is False.

    """
    # Set better default style
    mpl.rcParams.update({'font.size': 16})
    sns.set_style('ticks')
    palette = sns.color_palette('deep')
    if optimized in ['coverage', 'relative_coverage']:
        colors = [palette[3], palette[0]]
    elif optimized in ['directness', 'relative_directness',
                       'global_efficiency']:
        colors = [palette[0], palette[3]]
    else:
        colors = [palette[0], palette[0]]
        print("No optimized value as input, same color for both plot.")
    if coverage_name is None:
        with open(folder_name + "/arrcov.pickle", "rb") as fp:
            cov_history = pickle.load(fp)
    else:
        with open(coverage_name, "rb") as fp:
            cov_history = pickle.load(fp)
    if directness_name is None:
        with open(folder_name + "/arrdir.pickle", "rb") as fp:
            dir_history = pickle.load(fp)
    else:
        with open(directness_name, "rb") as fp:
            dir_history = pickle.load(fp)
    fig, axs = plt.subplots(1, 2, figsize=(24, 12))
    axs[0].plot(range(len(cov_history)), cov_history,
                linewidth=5, color=colors[0])
    axs[0].set_xlabel("Step")
    axs[0].set_ylabel("Coverage")
    axs[0].set_title("Area under curve (xy_normalized):{}".format(
        round(utils.get_area_under_curve(
            cov_history, normalize_y=True, normalize_x=True), 3)))
    axs[1].plot(range(len(dir_history)), dir_history,
                linewidth=5, color=colors[1])
    axs[1].set_xlabel("Step")
    axs[1].set_ylabel("Linkwise directness")
    axs[1].set_title("Area under curve (x_normalized):{}".format(
        round(utils.get_area_under_curve(
            dir_history, normalize_x=True), 3)))
    if save is True:
        fig.savefig(folder_name + "/plot_cov_dir")
    return fig, axs


def make_image_from_array(
        folder_name, G = None, array_name = None,
        order = 'subtractive', built = False, cmap = 'coolwarm'):
    """
    Make a folder with images for every step of the growth of the
    graph from an array of the choice of the edge removed/added with 
    the subtractive/additive growth.

    Parameters
    ----------
    folder_name : str
        Name of the folder for the images.
    G : networkx.classes.graph.Graph, optional
        Final network. If None, read a gpickle file based on 
        folder_name. The default is None.
    array_name : str, optional
        Name of the array used to know the subtractive/additive order.
        If None, name of the array is based on folder_name.
        The default is None.
    order : str, optional
        Order of the history, either subtractive or additive.
        The default is 'subtractive'.
    built : bool, optional
        If True, find and color differently the already built network
        that is fixed and the planned network. The default is False.
    cmap : str, optional
        Name of the colormap used. The default is 'Reds'.

    Raises
    ------
    ValueError
        Raised if the order value is not valid.

    """
    if G is None: # name by default of the gpickle file with the graph
        G = nx.read_gpickle(folder_name + "/final_network.gpickle")
    PAD = len(str(len(G))) # number of 0 to pad to order images
    if array_name is None: # name by default of the array
        with open(folder_name + "/arrchoice.pickle", "rb") as fp:
            choice_history = pickle.load(fp)
    else:
        with open(array_name,"rb") as fp:
            choice_history = pickle.load(fp)
    img_folder_name = folder_name + "/network_images"
    if not os.path.exists(img_folder_name):
        os.makedirs(img_folder_name)
    c = mpl.cm.get_cmap(cmap) # color to see built and planned
    built_color = c(1.0) # color of the built part
    if order == 'subtractive':
        if built is False:
            fig, ax = ox.plot_graph(  #this allow to save every step as a png
                nx.MultiDiGraph(G),
                bgcolor='white', node_color='black', node_size=20,
                node_alpha=0.7, edge_color=c(0.0), edge_linewidth=2,
                edge_alpha=0.5, figsize=(20,12),
                filepath=img_folder_name + f"/image_{0:0{PAD}}.png",
                save=True, show=False, close=True)
            xlim = ax.get_xlim() # keep same size of image for video
            ylim = ax.get_ylim()
            bb = [ylim[1], ylim[0], xlim[1], xlim[0]]
            for idx, edge in enumerate(choice_history):
                G.remove_edge(*edge)
                G = utils.clean_isolated_node(G) # remove node without edge
                fig, ax = ox.plot_graph(
                    nx.MultiDiGraph(G), bbox=bb,
                    bgcolor='white', node_color='black', node_size=20,
                    node_alpha=0.7, edge_color=c(0.0), edge_linewidth=2,
                    edge_alpha=0.5, figsize=(20,12),
                    filepath=img_folder_name + f"/image_{idx+1:0{PAD}}.png",
                    save=True, show=False, close=True)
        else:
            ec = ox.plot.get_edge_colors_by_attr(nx.MultiDiGraph(G),
                                                 'built', cmap=cmap)
            fig, ax = ox.plot_graph(  #this allow to save every step as a png
                nx.MultiDiGraph(G), edge_color=ec,
                bgcolor='white', node_color='black', node_size=20,
                node_alpha=0.7, edge_linewidth=2,
                edge_alpha=0.5, figsize=(20,12),
                filepath=img_folder_name + f"/image_{0:0{PAD}}.png",
                save=True, show=False, close=True)
            xlim = ax.get_xlim() # keep same size of image for video
            ylim = ax.get_ylim()
            bb = [ylim[1], ylim[0], xlim[1], xlim[0]]
            for idx, edge in enumerate(choice_history[:-1]):
                G.remove_edge(*edge)
                G = utils.clean_isolated_node(G) # remove node without edge
                ec = ox.plot.get_edge_colors_by_attr(nx.MultiDiGraph(G),
                                                     'built', cmap=cmap)
                fig, ax = ox.plot_graph(
                    nx.MultiDiGraph(G), bbox=bb, edge_color=ec,
                    bgcolor='white', node_color='black', node_size=20,
                    node_alpha=0.7, edge_linewidth=2,
                    edge_alpha=0.5, figsize=(20,12),
                    filepath=img_folder_name + f"/image_{idx+1:0{PAD}}.png",
                    save=True, show=False, close=True)
            # when every planned edge removed, we can't use the function
            # to find the right color, so need to put it manually
            G.remove_edge(*choice_history[-1])
            G = utils.clean_isolated_node(G) # remove node without edge
            fig, ax = ox.plot_graph(
                nx.MultiDiGraph(G), bbox=bb, edge_color=built_color,
                bgcolor='white', node_color='black', node_size=20,
                node_alpha=0.7, edge_linewidth=2,
                edge_alpha=0.5, figsize=(20,12),
                filepath=img_folder_name + f"/image_{idx+2:0{PAD}}.png",
                save=True, show=False, close=True)
    elif order == 'additive':
        fig, ax = ox.plot_graph(  #this allow to have the good bounding box
            nx.MultiDiGraph(G), show=False, close=True)
        xlim = ax.get_xlim() # keep same size of image for video
        ylim = ax.get_ylim()
        bb = [ylim[1], ylim[0], xlim[1], xlim[0]]
        if built is False:
            actual_edges = []
            for idx, edge in enumerate(choice_history):
                actual_edges.append(edge)
                ec = ox.plot.get_edge_colors_by_attr(
                    nx.MultiDiGraph(G.edge_subgraph(actual_edges)),
                    'built', cmap = cmap)
                fig, ax = ox.plot_graph(
                    nx.MultiDiGraph(G.edge_subgraph(actual_edges)), bbox=bb,
                    bgcolor='white', node_color='black', node_size=20,
                    node_alpha=0.7, edge_color=c(0.0), edge_linewidth=2,
                    edge_alpha=0.5, figsize=(20,12),
                    filepath=img_folder_name + f"/image_{idx:0{PAD}}.png",
                    save=True, show=False, close=True)
        else:
            actual_edges = [
                edge for edge in G.edges if edge not in choice_history]
            fig, ax = ox.plot_graph(  #this allow to save every step as a png
                nx.MultiDiGraph(G.edge_subgraph(actual_edges)),
                edge_color=built_color,  bbox=bb,
                bgcolor='white', node_color='black', node_size=20,
                node_alpha=0.7, edge_linewidth=2,
                edge_alpha=0.5, figsize=(20,12),
                filepath=img_folder_name + f"/image_{0:0{PAD}}.png",
                save=True, show=False, close=True)
            for idx, edge in enumerate(choice_history):
                actual_edges.append(edge)
                ec = ox.plot.get_edge_colors_by_attr(
                    nx.MultiDiGraph(G.edge_subgraph(actual_edges)),
                    'built', cmap = cmap)
                fig, ax = ox.plot_graph(
                    nx.MultiDiGraph(G.edge_subgraph(actual_edges)),
                    bbox=bb, edge_color=ec,
                    bgcolor='white', node_color='black', node_size=20,
                    node_alpha=0.7, edge_linewidth=2,
                    edge_alpha=0.5, figsize=(20,12),
                    filepath=img_folder_name + f"/image_{idx+1:0{PAD}}.png",
                    save=True, show=False, close=True)
    else:
        raise ValueError("""
                         Incorrect value for the order attribute, please
                         put subtractive or additive.
                         """)


def make_video_from_image(img_folder_name, reverse = False,
                          video_name = None, fps = 5):
    """
    From a folder of ordered images, make a video, in the inverted 
    order if reverse is True.

    Parameters
    ----------
    img_folder_name : str
        Name of the folder where the images are.
    reverse : bool, optional
        If True, the order of the images in the video is reversed.
        The default is False.
    video_name : str, optional
        Name of the video. If None, the name is by default the name of the
        folder, with reverse added if reverse is True. The default is None.
    fps : int, optional
        Number of frame per second on the video. The default is 5.

    """
    folder_name = img_folder_name.rsplit("/", 1)[0]
    if video_name is None: # default name of the video
        video_name = folder_name + "/network_video"
        if reverse is True:
            video_name = video_name + "_reverse.mp4"
        else:
            video_name = video_name + ".mp4"
    images = [img for img in os.listdir(img_folder_name)
              if img.endswith(".png")]
    if reverse is True: # reverse order of the images
        images.reverse() 
    # dimensions between images need to be constant
    frame = cv2.imread(os.path.join(img_folder_name, images[0]))
    height, width, layers = frame.shape
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(video_name, fourcc, fps, (width,height))
    for image in images:
        video.write(cv2.imread(os.path.join(img_folder_name, image)))
    cv2.destroyAllWindows()
    video.release()


# TODO: Finish to make side by side evolution of network and metrics
# Careful ox.plot_graph don't work with subplot for some reason
# TODO: Make possibility to put either number of step or
# number of kilometers constructed, show it as a title or something ?
def make_evolution_from_array(
        folder_name, G = None, order = 'subtractive',
        built = False, cmap = 'coolwarm'):
    mpl.rc_file_defaults()
    if G is None: # name by default of the gpickle file with the graph
        G = nx.read_gpickle(folder_name + "/final_network.gpickle")
    PAD = len(str(len(G))) # number of 0 to pad to order images
    with open(folder_name + "/arrchoice.pickle", "rb") as fp:
        choice_history = pickle.load(fp)
    img_folder_name = folder_name + "/network_evolution"
    if not os.path.exists(img_folder_name):
        os.makedirs(img_folder_name)
    if order == 'subtractive':
        if built is False:
            fig, axs = plt.subplot(1, 3, figsize=(24, 12))
            ox.plot_graph(  #this allow to save every step as a png
                nx.MultiDiGraph(G), ax=axs[0], bgcolor='black',
                node_color='w', edge_color='w')
            xlim = axs[0].get_xlim() # keep same size of image for video
            ylim = axs[0].get_ylim()
            bb = [ylim[1], ylim[0], xlim[1], xlim[0]]
            plt.savefig(fig, img_folder_name + f"/image_{0:0{PAD}}.png")
            for idx, edge in enumerate(choice_history[:-1]):
                G.remove_edge(*edge)
                G = utils.clean_isolated_node(G) # remove node without edge
                fig, ax = ox.plot_graph(
                    nx.MultiDiGraph(G), bbox=bb,
                    filepath=img_folder_name + f"/image_{idx+1:0{PAD}}.png",
                    save=True, show=False, close=True)
        else:
            c = mpl.cm.get_cmap(cmap) # color to see built and planned
            built_color = c(1.0) # color of the built part
            ec = ox.plot.get_edge_colors_by_attr(nx.MultiDiGraph(G),
                                                 'built', cmap = cmap)
            fig, ax = ox.plot_graph(  #this allow to save every step as a png
                nx.MultiDiGraph(G), edge_color=ec,
                filepath=img_folder_name + f"/image_{0:0{PAD}}.png",
                save=True, show=False, close=True)
            xlim = ax.get_xlim() # keep same size of image for video
            ylim = ax.get_ylim()
            bb = [ylim[1], ylim[0], xlim[1], xlim[0]]
            for idx, edge in enumerate(choice_history[:-1]):
                G.remove_edge(*edge)
                G = utils.clean_isolated_node(G) # remove node without edge
                ec = ox.plot.get_edge_colors_by_attr(nx.MultiDiGraph(G),
                                                     'built', cmap = cmap)
                fig, ax = ox.plot_graph(
                    nx.MultiDiGraph(G), bbox=bb, edge_color=ec,
                    filepath=img_folder_name + f"/image_{idx+1:0{PAD}}.png",
                    save=True, show=False, close=True)
            # when every planned edge removed, we can't use the function
            # to find the right color, so need to put it manually
            G.remove_edge(*choice_history[-1])
            G = utils.clean_isolated_node(G) # remove node without edge
            fig, ax = ox.plot_graph(
                nx.MultiDiGraph(G), bbox=bb, edge_color=built_color,
                filepath=img_folder_name + f"/image_{idx+2:0{PAD}}.png",
                save=True, show=False, close=True)
    elif order == 'additive':
        fig, ax = ox.plot_graph(  #this allow to have the good bounding box
            nx.MultiDiGraph(G), show=False, close=True)
        xlim = ax.get_xlim() # keep same size of image for video
        ylim = ax.get_ylim()
        bb = [ylim[1], ylim[0], xlim[1], xlim[0]]
        if built is False:
            actual_edges = []
            for idx, edge in enumerate(choice_history):
                actual_edges.append(edge)
                ec = ox.plot.get_edge_colors_by_attr(
                    nx.MultiDiGraph(G.edge_subgraph(actual_edges)),
                    'built', cmap = cmap)
                fig, ax = ox.plot_graph(
                    nx.MultiDiGraph(G.edge_subgraph(actual_edges)), bbox=bb,
                    filepath=img_folder_name + f"/image_{idx:0{PAD}}.png",
                    save=True, show=False, close=True)
        else:
            actual_edges = [
                edge for edge in G.edges if edge not in choice_history]
            c = mpl.cm.get_cmap(cmap)
            built_color = c(1.0)
            fig, ax = ox.plot_graph(  #this allow to save every step as a png
                nx.MultiDiGraph(G.edge_subgraph(actual_edges)),
                edge_color=built_color,  bbox=bb,
                filepath=img_folder_name + f"/image_{0:0{PAD}}.png",
                save=True, show=False, close=True)
            for idx, edge in enumerate(choice_history):
                actual_edges.append(edge)
                ec = ox.plot.get_edge_colors_by_attr(
                    nx.MultiDiGraph(G.edge_subgraph(actual_edges)),
                    'built', cmap = cmap)
                fig, ax = ox.plot_graph(
                    nx.MultiDiGraph(G.edge_subgraph(actual_edges)),
                    bbox=bb, edge_color=ec,
                    filepath=img_folder_name + f"/image_{idx+1:0{PAD}}.png",
                    save=True, show=False, close=True)
    else:
        raise ValueError("""
                         Incorrect value for the order attribute, please
                         put subtractive or additive.
                         """)


# TODO: Before polishing, be sure what we want to do exactly
def color_order_growth_graph(G, folder_name, array_name = None, cmap = 'jet'):
    if array_name is None:
        with open(folder_name + "_arrchoice.pickle", "rb") as fp:
            choice_history = pickle.load(fp)
    else:
        with open(array_name, "rb") as fp:
            choice_history = pickle.load(fp)
    for idx, edge in enumerate(choice_history):
        G.edges[edge]['order_color'] = idx
    for edge in G.edges:
        if edge not in choice_history:
            G.edges[edge]['order_color'] = len(G.edges)
    ec = ox.plot.get_edge_colors_by_attr(nx.MultiGraph(G), 'order_color',
                                         cmap=cmap)
    ox.plot_graph(nx.MultiGraph(G), figsize = (12, 8), bgcolor='w',
                  node_color='black', node_size=10,
                  edge_color=ec, edge_linewidth=2,
                  filepath=folder_name + "_color_order.png",
                  save=True, show=False, close=True)

