# -*- coding: utf-8 -*-
"""
Functions to visualize results of the growth of a graph.
"""


import os
import pickle
import matplotlib as mpl
import cv2
import networkx as nx
import osmnx as ox
from orderbike import utils


def make_image_from_array(
    folder_name,
    G=None,
    array_name=None,
    order="subtractive",
    built=False,
    cmap="coolwarm",
):
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
    # TODO: update by removing gpickle and pickle to load whenever updated in metrics and growth python file
    if G is None:  # name by default of the gpickle file with the graph
        G = nx.read_gpickle(folder_name + "/final_network.gpickle")
    PAD = len(str(len(G)))  # number of 0 to pad to order images
    if array_name is None:  # name by default of the array
        with open(folder_name + "/arrchoice.pickle", "rb") as fp:
            choice_history = pickle.load(fp)
    else:
        with open(array_name, "rb") as fp:
            choice_history = pickle.load(fp)
    img_folder_name = folder_name + "/network_images"
    if not os.path.exists(img_folder_name):
        os.makedirs(img_folder_name)
    c = mpl.cm.get_cmap(cmap)  # color to see built and planned
    built_color = c(1.0)  # color of the built part
    if order == "subtractive":
        if not built:
            ec = c(0.0)
            im_arr = choice_history
        else:
            ec = ox.plot.get_edge_colors_by_attr(nx.MultiDiGraph(G), "built", cmap=cmap)
            im_arr = choice_history[:-1]
        fig, ax = ox.plot_graph(  # this allow to save every step as a png
            nx.MultiDiGraph(G),
            edge_color=ec,
            bgcolor="white",
            node_color="black",
            node_size=20,
            node_alpha=0.7,
            edge_linewidth=2,
            edge_alpha=0.5,
            figsize=(20, 12),
            filepath=img_folder_name + f"/image_{0:0{PAD}}.png",
            save=True,
            show=False,
            close=True,
        )
        xlim = ax.get_xlim()  # keep same size of image for video
        ylim = ax.get_ylim()
        bb = [ylim[1], ylim[0], xlim[1], xlim[0]]
        for idx, edge in enumerate(im_arr):
            G.remove_edge(*edge)
            G = utils.clean_isolated_node(G)  # remove node without edge
            ec = ox.plot.get_edge_colors_by_attr(nx.MultiDiGraph(G), "built", cmap=cmap)
            fig, ax = ox.plot_graph(
                nx.MultiDiGraph(G),
                bbox=bb,
                edge_color=ec,
                bgcolor="white",
                node_color="black",
                node_size=20,
                node_alpha=0.7,
                edge_linewidth=2,
                edge_alpha=0.5,
                figsize=(20, 12),
                filepath=img_folder_name + f"/image_{idx+1:0{PAD}}.png",
                save=True,
                show=False,
                close=True,
            )
        # when every planned edge removed, we can't use the function
        # to find the right color, so need to put it manually
        if built:
            G.remove_edge(*choice_history[-1])
            G = utils.clean_isolated_node(G)  # remove node without edge
            fig, ax = ox.plot_graph(
                nx.MultiDiGraph(G),
                bbox=bb,
                edge_color=built_color,
                bgcolor="white",
                node_color="black",
                node_size=20,
                node_alpha=0.7,
                edge_linewidth=2,
                edge_alpha=0.5,
                figsize=(20, 12),
                filepath=img_folder_name + f"/image_{idx+2:0{PAD}}.png",
                save=True,
                show=False,
                close=True,
            )
    elif order == "additive":
        fig, ax = ox.plot_graph(  # this allow to have the good bounding box
            nx.MultiDiGraph(G), show=False, close=True
        )
        xlim = ax.get_xlim()  # keep same size of image for video
        ylim = ax.get_ylim()
        bb = [ylim[1], ylim[0], xlim[1], xlim[0]]
        if not built:
            actual_edges = []
            init = 0
        else:
            actual_edges = [edge for edge in G.edges if edge not in choice_history]
            init = 1
            fig, ax = ox.plot_graph(
                nx.MultiDiGraph(G.edge_subgraph(actual_edges)),
                edge_color=built_color,
                bbox=bb,
                bgcolor="white",
                node_color="black",
                node_size=20,
                node_alpha=0.7,
                edge_linewidth=2,
                edge_alpha=0.5,
                figsize=(20, 12),
                filepath=img_folder_name + f"/image_{0:0{PAD}}.png",
                save=True,
                show=False,
                close=True,
            )
        for idx, edge in enumerate(choice_history):
            actual_edges.append(edge)
            if not built:
                ec = c(0.0)
            else:
                ec = ox.plot.get_edge_colors_by_attr(
                    nx.MultiDiGraph(G.edge_subgraph(actual_edges)), "built", cmap=cmap
                )
            fig, ax = ox.plot_graph(
                nx.MultiDiGraph(G.edge_subgraph(actual_edges)),
                bbox=bb,
                edge_color=ec,
                bgcolor="white",
                node_color="black",
                node_size=20,
                node_alpha=0.7,
                edge_linewidth=2,
                edge_alpha=0.5,
                figsize=(20, 12),
                filepath=img_folder_name + f"/image_{idx+init:0{PAD}}.png",
                save=True,
                show=False,
                close=True,
            )
    else:
        raise ValueError(
            """
                         Incorrect value for the order attribute, please
                         put subtractive or additive.
                         """
        )


def make_video_from_image(img_folder_name, reverse=False, video_name=None, fps=5):
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
    if video_name is None:  # default name of the video
        video_name = folder_name + "/network_video"
        if reverse is True:
            video_name = video_name + "_reverse.mp4"
        else:
            video_name = video_name + ".mp4"
    images = [img for img in os.listdir(img_folder_name) if img.endswith(".png")]
    if reverse is True:  # reverse order of the images
        images.reverse()
    # dimensions between images need to be constant
    frame = cv2.imread(os.path.join(img_folder_name, images[0]))
    height, width, layers = frame.shape
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video = cv2.VideoWriter(video_name, fourcc, fps, (width, height))
    for image in images:
        video.write(cv2.imread(os.path.join(img_folder_name, image)))
    cv2.destroyAllWindows()
    video.release()
