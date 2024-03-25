# -*- coding: utf-8 -*-
"""
Get the simplified network of Paris, keeping the bicycle network in a single boolean attribute.
"""
import osmnx as ox

from orderbike.utils import add_edge_attr_from_dict, OSM_bicycle_tag

if __name__ == "__main__":
    # First add every necessary tag on the tag_list so we can filter with them
    biketags = OSM_bicycle_tag()
    for tag_name in biketags.keys():
        if tag_name not in ox.settings.useful_tags_way:
            ox.settings.useful_tags_way += [tag_name]
    # Get the non-simplified graph with the extended list of attributes
    G = ox.graph_from_place("Paris, France", simplify=False)
    # Add as boolean attribute for all values and simplify the network with it
    G = add_edge_attr_from_dict(G, biketags, "protected_bicycling")
    G = ox.simplify_graph(G, endpoint_attrs=["protected_bicycling"])
    # Large file so avoid putting it on GitHub by putting it into ignored folder
    ox.save_graphml(
        G, filepath="./data/processed/large_files/paris_simp_bikenet.graphml"
    )
    ec = ox.plot.get_edge_colors_by_attr(G, attr="protected_bicycling", cmap="brg")
    ox.plot_graph(
        G,
        bgcolor="white",
        node_color="black",
        node_size=0.5,
        edge_color=ec,
        edge_linewidth=0.5,
        save=True,
        filepath="./plots/paris_bikenet_image.png",
        dpi=2000,
    )
