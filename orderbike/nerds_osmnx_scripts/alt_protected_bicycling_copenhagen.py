# -*- coding: utf-8 -*-
"""
Alternative simplified graph of Copenhagen (and Frederiksberg).
See protected_bicycling_copenhagen_simplified.py for more explanation.
"""


import nerds_osmnx.simplification as simplification
import nerds.osmnx.utils as utils
import osmnx as ox
import shapely
import networkx as nx


if __name__ == "__main__":
    # First add every necessary tag on the tag_list so we can filter with them
    tag_list = ["sidewalk:left:bicycle", "sidewalk:right:bicycle",
                "cycleway:left", "cycleway:right", "cycleway", "cycleway:both",
                "cyclestreet", "bicycle", "bicycle_road"]
    for tag_name in tag_list:
        if tag_name not in ox.settings.useful_tags_way:
            ox.settings.useful_tags_way += [tag_name]
    
    # Get the polygon of Copenhagen and Frederiksberg
    cop = ox.geocode_to_gdf("Copenhagen Municipality")
    fre = ox.geocode_to_gdf("Frederiksberg Municipality")
    polygon = shapely.ops.unary_union([cop['geometry'][0], fre['geometry'][0]])
    # Get the non-simplified graph with the extended list of attributes
    G = ox.graph_from_polygon(polygon, simplify=False)
    # Make dictionary of protected bicycle infrastructure
    protected_dict = dict()
    protected_dict["sidewalk:left:bicycle"] = "yes"
    protected_dict["sidewalk:left:right"] = "yes"
    protected_dict["cycleway:left"] = ["shared_lane", "shared_busway",
                                       "track"]
    protected_dict["cycleway:right"] = ["shared_lane", "shared_busway",
                                        "track"]
    protected_dict["cycleway:both"] = "lane"
    protected_dict["cycleway"] = ["shared_lane", "shared_busway",
                                  "opposite_lane", "opposite"]
    protected_dict["bicycle"] = ["designated", "yes", 
                                 "official", "use_sidepath"]
    protected_dict["highway"] = ["cycleway", "bridleway"]
    protected_dict["cyclestreet"] = "yes"
    protected_dict["bicycle_road"] = "yes"

    H = utils.add_edge_attribute(G, protected_dict, 'protected_bicycling')
    # Create new attribute to simplify it
    H = utils.add_edge_attribute(G, protected_dict, 'protected_bicycling')

    H_sim = simplification.simplify_graph(H, attributes='protected_bicycling')
    H_fin = simplification.multidigraph_to_graph(
        H_sim, attributes='protected_bicycling', verbose=True
        )
    # Count the number of protected edges and change bool into binary int
    count_protected = 0
    for edge in H_fin.edges:
        if H_fin.edges[edge]['protected_bicycling'] is True:
            H_fin.edges[edge]['protected_bicycling'] = 1
            count_protected += 1
        else:
            H_fin.edges[edge]['protected_bicycling'] = 0
    ratio = 1 - (
        (len(list(H_fin.edges))-count_protected) / len(list(H_fin.edges))
        )
    print("{}% of protected edges".format(round((ratio * 100), 2)))
    # Basic statistics
    print("""
          {} nodes and {} edges in original graph G \n
          {} nodes and {} edges in multilayer simplified graph H_sim \n
          {} nodes and {} edges in final graph H_fin
          """.format(len(list(G.nodes())), len(list(G.edges())),
          len(list(H_sim.nodes())), len(list(H_sim.edges())),
          len(list(H_fin.nodes())), len(list(H_fin.edges()))))

    # Use binary int for visualization
    ec = ox.plot.get_edge_colors_by_attr(H_fin, 'protected_bicycling',
                                         cmap='bwr')
    H_fin = nx.MultiGraph(H_fin) # osmnx plot graph don't support graph
    # Red is protected, blue unprotected
    ox.plot_graph(H_fin, figsize=(12, 8), bgcolor='w', 
                  node_color='black', node_size=10,
                  edge_color=ec, edge_linewidth = 1.5)