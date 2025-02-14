from utg import create_graph
from orderbike.plot import plot_graph
import shapely
import geopandas as gpd
from matplotlib import pyplot as plt
from orderbike.metrics import directness
import os


if __name__ == "__main__":
    folderplot = "./data/processed/ignored_files/paper/plot/showcase_networks/"
    if not os.path.exists(folderplot):
        os.makedirs(folderplot)
    G_init = create_graph.create_grid_graph(rows=10, cols=10, width=100, diagonal=False)
    max_coverage = shapely.unary_union(
        [G_init.edges[e]["geometry"].buffer(152) for e in G_init.edges]
    ).area
    # number of edges = 24
    order_disconnected = [
        (0, 10),
        (20, 21),
        (40, 50),
        (70, 71),
        (80, 90),
        (1, 2),
        (91, 92),
        (3, 13),
        (42, 52),
        (83, 93),
        (4, 5),
        (34, 35),
        (64, 65),
        (6, 16),
        (47, 57),
        (86, 96),
        (7, 8),
        (97, 98),
        (9, 19),
        (28, 29),
        (78, 79),
        (89, 99),
        (49, 59),
        (94, 95),
    ]
    order_deprecated_1 = [
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 4),
        (4, 5),
        (5, 6),
        (6, 7),
        (7, 8),
        (8, 9),
        (9, 19),
        (19, 29),
        (29, 39),
        (39, 49),
        (49, 59),
        (59, 69),
        (0, 10),
        (10, 20),
        (20, 30),
        (30, 40),
        (40, 50),
        (50, 60),
    ]
    order_deprecated_2 = [
        (4, 14),
        (13, 14),
        (14, 15),
        (14, 24),
        (24, 34),
        (34, 44),
        (44, 54),
        (54, 64),
        (64, 74),
        (74, 84),
        (73, 74),
        (74, 75),
        (44, 43),
        (43, 42),
        (42, 41),
        (41, 40),
        (41, 51),
        (41, 31),
        (44, 45),
        (45, 46),
        (46, 47),
        (47, 48),
        (47, 57),
        (37, 47),
    ]
    order_midcovmiddir = [
        (24, 25),
        (24, 34),
        (34, 44),
        (25, 35),
        (35, 45),
        (44, 45),
        (44, 54),
        (45, 55),
        (54, 55),
        (54, 64),
        (64, 74),
        (55, 65),
        (65, 75),
        (74, 75),
        (42, 43),
        (43, 44),
        (45, 46),
        (46, 47),
        (52, 53),
        (53, 54),
        (55, 56),
        (56, 57),
        (42, 52),
        (47, 57),
    ]
    order_maxcovmindir = [
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 4),
        (4, 5),
        (5, 6),
        (6, 16),
        (16, 26),
        (26, 36),
        (36, 46),
        (46, 56),
        (56, 66),
        (66, 65),
        (66, 65),
        (65, 64),
        (64, 63),
        (63, 62),
        (62, 61),
        (61, 60),
        (60, 50),
        (50, 40),
        (40, 30),
        (30, 20),
        (20, 10),
        (10, 0),
    ]
    order_mincovmaxdir = [
        [0, 1],
        [1, 2],
        [2, 3],
        [3, 4],
        [4, 5],
        [5, 6],
        [6, 7],
        [7, 8],
        [0, 10],
        [1, 11],
        [10, 11],
        [2, 12],
        [11, 12],
        [3, 13],
        [12, 13],
        [4, 14],
        [13, 14],
        [5, 15],
        [14, 15],
        [6, 16],
        [15, 16],
        [7, 17],
        [16, 17],
        [8, 18],
        [17, 18],
    ]
    order_mincovmaxdir = [tuple(val) for val in order_mincovmaxdir]
    order_deprecated_3 = [
        (33, 34),
        (34, 35),
        (35, 36),
        (43, 44),
        (44, 45),
        (45, 46),
        (53, 54),
        (54, 55),
        (55, 56),
        (63, 64),
        (64, 65),
        (65, 66),
        (33, 43),
        (43, 53),
        (53, 63),
        (34, 44),
        (44, 54),
        (54, 64),
        (35, 45),
        (45, 55),
        (55, 65),
        (36, 46),
        (46, 56),
        (56, 66),
    ]
    orders = [
        order_disconnected,
        order_deprecated_1,
        order_deprecated_2,
        order_midcovmiddir,
        order_maxcovmindir,
        order_mincovmaxdir,
        order_deprecated_3,
    ]
    networks = [G_init.edge_subgraph(order) for order in orders]
    names = [
        "disconnected",
        "deprecated_1",
        "deprecated_2",
        "midcovmiddir",
        "maxcovmindir",
        "mincovmaxdir",
        "deprecated_3",
    ]
    fig_mul, ax_mul = plt.subplots(figsize=(10, 10))
    for idx, G in enumerate(networks):
        fig_ind, ax_ind = plot_graph(
            G,
            filepath=folderplot,
            buffer=True,
            buff_size=152,
            buff_color="grey",
            edge_color="black",
            edge_linewidth=2,
            node_color="black",
            node_size=200,
            show=False,
            save=False,
            close=False,
        )
        ax_ind.set_xlim([-200, 1100])
        ax_ind.set_ylim([-200, 1100])
        if names[idx] == "deprecated_1":
            geom_node = [
                shapely.Point(G.nodes[n]["x"], G.nodes[n]["y"]) for n in [60, 69]
            ]
            gdf_node = gpd.GeoDataFrame(index=[60, 69], geometry=geom_node)
            gdf_node.plot(ax=ax_ind, color="red", zorder=3, markersize=200)
        fig_ind.savefig(folderplot + f"network_{names[idx]}.png")
        ax_mul.scatter(
            directness(G, 0),
            shapely.unary_union(
                [G.edges[e]["geometry"].buffer(152) for e in G.edges]
            ).area
            / max_coverage,
            label=names[idx],
        )
    ax_mul.legend()
    ax_mul.set_xlabel("Directness")
    ax_mul.set_ylabel("Coverage/Max Coverage")
    fig_mul.savefig(folderplot + "scatterplot_manual_networks.png")
