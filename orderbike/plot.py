# -*- coding: utf-8 -*-
"""
Functions to visualize results of the growth of a graph.
"""

import os

import cv2
import networkx as nx
import osmnx as ox
import pandas as pd


def plot_graph(G, show=True, save=False, filepath=None, **kwargs):
    """Replace with working plotting function not using osmnx, need G.graph["crs"] to exists."""
    fig, ax = ox.plot_graph(
        nx.MultiDiGraph(G), show=show, save=save, filepath=filepath, **kwargs
    )
    return fig, ax


def make_edge_dict_multidigraph(edge_dict):
    """Temporary function for as long as using osmnx plotting function"""
    m_edge_dict = {}
    for edge in edge_dict:
        u, v = edge
        m_edge_dict[u, v, 0] = edge_dict[edge]
        m_edge_dict[v, u, 0] = edge_dict[edge]
    return m_edge_dict


# TODO: Redo it by using geopandas directly and not the hellscape of osmnx
def plot_growth(
    G,
    growth_steps,
    folder_name,
    built=True,
    color_built="red",
    color_added="blue",
    color_newest="green",
):
    if built:
        init_edges = [edge for edge in G.edges if G.edges[edge]["built"] == 1]
        edge_color = {edge: color_built for edge in init_edges}
    # Find initial edges if not built by finding the ones that are not on the growth steps. Supposedly it's a single random edge from the highest closeness node, see growth.order_network_growth
    else:
        init_edges = [edge for edge in G.edges if edge not in growth_steps]
        edge_color = {edge: color_newest for edge in init_edges}
    G_init = G.edge_subgraph(init_edges)
    # Make first plot only to get a fixed bounding box for plots, being the one for the final graph
    fig, ax = plot_graph(G, show=False, save=False, close=True)
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    bb = [ylim[1], ylim[0], xlim[1], xlim[0]]
    pad = len(str(len(G.edges)))
    fig, ax = plot_graph(
        nx.MultiDiGraph(G_init),
        bgcolor="white",
        node_color="black",
        node_size=5,
        edge_color=pd.Series(make_edge_dict_multidigraph(edge_color)),
        edge_linewidth=2,
        save=True,
        show=False,
        filepath=folder_name + f"/step_{0:0{pad}}.png",
        bbox=bb,
        close=True,
    )
    if not built:
        edge_color = {edge: color_added for edge in init_edges}
    actual_edges = init_edges.copy()
    old_edge = None
    for ids, edge in enumerate(growth_steps):
        actual_edges.append(edge)
        edge_color[edge] = color_newest
        # Replace color of previous edge from being the newest to being an added one
        if old_edge is not None:
            edge_color[old_edge] = color_added
        G_actual = G.edge_subgraph(actual_edges)
        fig, ax = plot_graph(
            nx.MultiDiGraph(G_actual),
            bgcolor="white",
            node_color="black",
            node_size=5,
            edge_color=pd.Series(make_edge_dict_multidigraph(edge_color)),
            edge_linewidth=2,
            save=True,
            show=False,
            filepath=folder_name + f"/step_{ids+1:0{pad}}.png",
            bbox=bb,
            close=True,
        )
        old_edge = edge


def make_growth_video(img_folder_name, video_name, fps=5):
    """
    From a folder of ordered images make a video.
    """
    images = [img for img in os.listdir(img_folder_name) if img.endswith(".png")]
    images.sort()
    # dimensions between images need to be constant
    frame = cv2.imread(os.path.join(img_folder_name, images[0]))
    height, width, layers = frame.shape
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video = cv2.VideoWriter(video_name, fourcc, fps, (width, height))
    for image in images:
        video.write(cv2.imread(os.path.join(img_folder_name, image)))
    cv2.destroyAllWindows()
    video.release()
