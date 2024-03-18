# -*- coding: utf-8 -*-
"""
Functions to visualize results of the growth of a graph.
"""

import os

import cv2
import geopandas as gpd
from matplotlib import pyplot as plt
import networkx as nx
import shapely

from .utils import get_node_positions


# TODO: Add minimal buffer as plateau so replace buffer smaller than min_buff by min_buff ?
# TODO: Change buff_size based on relative change, taking into account size of added edge compared to total length of graph ?
def plot_adaptative_coverage(
    G,
    growth_steps,
    ax=None,
    built=True,
    x_meter=True,
    plot_change=True,
    show_buffer_change=True,
    buff_size=500,
    threshold_change=0.01,
    min_buff=20,
    show=True,
    save=False,
    close=False,
    filepath=None,
    dpi=1000,
    figsize=(16, 9),
):
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize, layout="constrained")
    else:
        fig = ax.get_figure()
    G_actual = _init_graph(G, growth_steps, built=built)
    actual_edges = [edge for edge in G_actual.edges]
    yy = []
    if x_meter:
        xx = []
        total_length = sum([G_actual.edges[edge]["length"] for edge in G_actual.edges])
        ax.set_xlabel("Meters built")
    else:
        xx = range(len(growth_steps))
        ax.set_xlabel("Steps built")
    buffer_change = {}
    for ids, edge in enumerate(growth_steps):
        new_buff = False
        actual_edges.append(edge)
        geom = [G.edges[edge]["geometry"].buffer(buff_size) for edge in actual_edges]
        geom_bef = [
            G.edges[edge]["geometry"].buffer(buff_size) for edge in actual_edges[:-1]
        ]
        change = (
            shapely.ops.unary_union(geom).area - shapely.ops.unary_union(geom_bef).area
        ) / shapely.ops.unary_union(geom_bef).area
        while change < threshold_change and buff_size > min_buff:
            new_buff = True
            buff_size = buff_size / 2
            geom = [
                G.edges[edge]["geometry"].buffer(buff_size) for edge in actual_edges
            ]
            geom_bef = [
                G.edges[edge]["geometry"].buffer(buff_size)
                for edge in actual_edges[:-1]
            ]
            change = (
                shapely.ops.unary_union(geom).area
                - shapely.ops.unary_union(geom_bef).area
            ) / shapely.ops.unary_union(geom_bef).area
        if plot_change:
            yy.append(change)
        if x_meter:
            total_length += G.edges[edge]["length"]
            xx.append(total_length)
        if new_buff:
            if x_meter:
                buffer_change[total_length] = buff_size
            else:
                buffer_change[ids] = buff_size
    if not plot_change:
        G_actual = _init_graph(G, growth_steps, built=built)
        actual_edges = [edge for edge in G_actual.edges]
        for edge in growth_steps:
            actual_edges.append(edge)
            geom = [
                G.edges[edge]["geometry"].buffer(buff_size) for edge in actual_edges
            ]
            yy.append(shapely.ops.unary_union(geom).area)
    if plot_change:
        ax.axhline(
            threshold_change,
            color="red",
            linestyle="dashed",
            label="Threshold for buffer change",
        )
        label = "Change in coverage with decreasing buffer"
        ax.set_ylabel("Change in the coverage")
    else:
        ax.set_ylabel("Total coverage ($m^2$)")
        label = "Coverage with decreasing buffer"
    ax.scatter(xx, yy, color="blue", label=label)
    if show_buffer_change:
        for val in buffer_change:
            ax.axvline(
                val,
                color="gray",
                linestyle="dashed",
                label=f"Buffer changing to {buffer_change[val]}m",
            )
    plt.legend()
    _show_save_close(fig, show=show, save=save, close=close, filepath=filepath, dpi=dpi)
    return fig, ax


def plot_graph(
    G,
    edge_linewidth=2,
    node_size=6,
    edge_color="steelblue",
    node_color="black",
    ax=None,
    figsize=(16, 9),
    show=True,
    save=False,
    close=False,
    filepath=None,
    dpi=200,
    bbox=None,
):
    """Replace with working plotting function not using osmnx, need G.graph["crs"] to exists."""
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize, layout="constrained")
    else:
        fig = ax.get_figure()
    if bbox is not None:
        ax.set_ylim(bbox[0], bbox[1])
        ax.set_xlim(bbox[2], bbox[3])
    geom_node = [shapely.Point(x, y) for x, y in get_node_positions(G)]
    geom_edge = list(nx.get_edge_attributes(G, "geometry").values())
    if isinstance(edge_color, dict):
        edgeidx = [edge for edge in G.edges]
        new_edge_color = {}
        for edge in edge_color:
            if edge not in edgeidx:
                if tuple(reversed(edge)) in edgeidx:
                    new_edge_color[tuple(reversed(edge))] = edge_color[edge]
                else:
                    raise ValueError(f"{edge} in edge_color is not in G")
            else:
                new_edge_color[edge] = edge_color[edge]
        edge_color = new_edge_color
    gdf_node = gpd.GeoDataFrame(index=[node for node in G.nodes], geometry=geom_node)
    gdf_node = gdf_node.assign(color=node_color)
    gdf_edge = gpd.GeoDataFrame(index=[edge for edge in G.edges], geometry=geom_edge)
    gdf_edge = gdf_edge.assign(color=edge_color)
    gdf_edge.plot(ax=ax, color=gdf_edge["color"], zorder=1, linewidth=edge_linewidth)
    gdf_node.plot(ax=ax, color=gdf_node["color"], zorder=2, markersize=node_size)
    ax.set_xticks([])
    ax.set_yticks([])
    _show_save_close(fig, show=show, save=save, close=close, filepath=filepath, dpi=dpi)
    return fig, ax


def _show_save_close(fig, show=True, save=False, close=False, filepath=None, dpi=1000):
    if show:
        plt.show()
    if save:
        fig.savefig(filepath, dpi=dpi)
    if close:
        plt.close()


def plot_growth(
    G,
    growth_steps,
    folder_name,
    built=True,
    color_built="red",
    color_added="blue",
    color_newest="green",
    dpi=200,
    **kwargs,
):
    G_init = _init_graph(G, growth_steps, built=built)
    if built:
        edge_color = {edge: color_built for edge in G_init.edges}
    else:
        edge_color = {edge: color_newest for edge in G_init.edges}
    # Make first plot only to get a fixed bounding box for plots, being the one for the final graph
    fig, ax = plot_graph(G, show=False, save=False, close=True, dpi=dpi)
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    bb = [ylim[1], ylim[0], xlim[1], xlim[0]]
    pad = len(str(len(G.edges)))
    fig, ax = plot_graph(
        G_init,
        edge_color=edge_color,
        save=True,
        show=False,
        filepath=folder_name + f"/step_{0:0{pad}}.png",
        bbox=bb,
        close=True,
        dpi=dpi,
        **kwargs,
    )
    if not built:
        edge_color = {edge: color_added for edge in G_init.edges}
    actual_edges = list(G_init.edges)
    old_edge = None
    for ids, edge in enumerate(growth_steps):
        actual_edges.append(edge)
        edge_color[edge] = color_newest
        # Replace color of previous edge from being the newest to being an added one
        if old_edge is not None:
            edge_color[old_edge] = color_added
        G_actual = G.edge_subgraph(actual_edges)
        fig, ax = plot_graph(
            G_actual,
            edge_color=edge_color,
            save=True,
            show=False,
            filepath=folder_name + f"/step_{ids+1:0{pad}}.png",
            bbox=bb,
            close=True,
            dpi=dpi,
            **kwargs,
        )
        old_edge = edge


def _init_graph(G, growth_steps, built=True):
    if built:
        init_edges = [edge for edge in G.edges if G.edges[edge]["built"] == 1]
    # Find initial edges if not built by finding the ones that are not on the growth steps. Supposedly it's a single random edge from the highest closeness node, see growth.order_network_growth
    else:
        init_edges = [edge for edge in G.edges if edge not in growth_steps]
    return G.edge_subgraph(init_edges)


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
