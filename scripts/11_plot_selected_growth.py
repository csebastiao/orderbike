from utg import utils
from orderbike.plot import plot_graph
from matplotlib import pyplot as plt
import os
import json
import geopandas as gpd
import networkx as nx


def load_subnetwork(G, filename, max_id):
    with open(filename) as f:
        val = json.load(f)
        val = [(arr[0], arr[1]) for arr in val]
        init_edges = [edge for edge in G.edges if edge not in val]
        val = init_edges + val
        val = val[:max_id]
    return G.edge_subgraph(val)


if __name__ == "__main__":
    folderplot = "./data/processed/ignored_files/paper/plot/selected_growths/"
    if not os.path.exists(folderplot):
        os.makedirs(folderplot)
    folderoot_grid = "./data/processed/ignored_files/paper/grid/"
    folderoot_grid_diag = "./data/processed/ignored_files/paper/grid_with_diagonal/"
    G_grid = utils.load_graph(folderoot_grid + "graph.graphml")
    G_grid_diag = utils.load_graph(folderoot_grid_diag + "graph.graphml")
    networks = []
    networks.append(
        load_subnetwork(
            G_grid,
            folderoot_grid + "coverage_additive_connected/order_growth_014.json",
            55,
        )
    )
    networks.append(
        load_subnetwork(
            G_grid,
            folderoot_grid + "coverage_additive_connected/order_growth_014.json",
            58,
        )
    )
    networks.append(
        load_subnetwork(
            G_grid,
            folderoot_grid + "coverage_additive_connected/order_growth_014.json",
            59,
        )
    )
    networks.append(
        load_subnetwork(
            G_grid,
            folderoot_grid + "coverage_subtractive_connected/order_growth_044.json",
            55,
        )
    )
    networks.append(
        load_subnetwork(
            G_grid,
            folderoot_grid + "coverage_subtractive_connected/order_growth_044.json",
            58,
        )
    )
    networks.append(
        load_subnetwork(
            G_grid,
            folderoot_grid + "coverage_subtractive_connected/order_growth_044.json",
            59,
        )
    )
    networks.append(
        load_subnetwork(
            G_grid,
            folderoot_grid
            + "adaptive_coverage_additive_connected/order_growth_040.json",
            37,
        )
    )
    networks.append(
        load_subnetwork(
            G_grid,
            folderoot_grid
            + "adaptive_coverage_additive_connected/order_growth_040.json",
            51,
        )
    )
    networks.append(
        load_subnetwork(
            G_grid,
            folderoot_grid
            + "adaptive_coverage_additive_connected/order_growth_040.json",
            101,
        )
    )
    networks.append(
        load_subnetwork(
            G_grid_diag,
            folderoot_grid_diag
            + "adaptive_coverage_additive_connected/order_growth_041.json",
            27,
        )
    )
    networks.append(
        load_subnetwork(
            G_grid_diag,
            folderoot_grid_diag + "coverage_additive_connected/order_growth_000.json",
            27,
        )
    )
    names = [
        "grid_additive_coverage_n14_e55",
        "grid_additive_coverage_n14_e58",
        "grid_additive_coverage_n14_e59",
        "grid_subtractive_coverage_n44_e55",
        "grid_subtractive_coverage_n44_e58",
        "grid_subtractive_coverage_n44_e59",
        "grid_adaptive_coverage_additive_n40_e37",
        "grid_adaptive_coverage_additive_n40_e51",
        "grid_adaptive_coverage_additive_n40_e101",
        "gridiag_adaptive_coverage_additive_n41_e27",
        "gridiag_coverage_additive_n0_e27",
    ]
    gdf_edge = gpd.GeoDataFrame(
        geometry=list(nx.get_edge_attributes(G_grid, "geometry").values())
    )
    buff = gpd.GeoSeries(gdf_edge.geometry.buffer(152).union_all())
    for idx, G in enumerate(networks):
        fig_ind, ax_ind = plot_graph(
            G,
            filepath=folderplot,
            figsize=(10, 10),
            buffer=True,
            buff_size=152,
            buff_color="grey",
            edge_color="black",
            edge_linewidth=4,
            node_color="black",
            node_size=200,
            show=False,
            save=False,
            close=False,
        )
        gdf_edge_ind = gpd.GeoDataFrame(
            geometry=list(nx.get_edge_attributes(G, "geometry").values())
        )
        buff_ind = gpd.GeoSeries(gdf_edge_ind.geometry.buffer(152).union_all())
        buff_remaining = buff.difference(buff_ind)
        buff_remaining.plot(ax=ax_ind, color="#FF0000", zorder=0)
        savename = folderplot + f"{names[idx]}.png"
        ax_ind.set_xlim([-200, 1100])
        ax_ind.set_ylim([-200, 1100])
        ax_ind.axis("off")
        fig_ind.savefig(savename)
        plt.close()
