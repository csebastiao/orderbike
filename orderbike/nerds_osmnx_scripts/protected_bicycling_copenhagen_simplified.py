# -*- coding: utf-8 -*-
"""
Make a simplified graph of Copenhagen (and Frederiksberg) by removing
every non-necessary interstitial nodes and discriminating roads with
protected bicycling infrastructure (or safe place) and others, based on 
the criterion of bikewgrowth.
"""

import nerds_osmnx.simplification as simplification
import nerds_osmnx.utils as utils
import osmnx as ox
import shapely
import networkx as nx
import geopandas as gpd

if __name__ == "__main__":
    # First add every necessary tag on the tag_list so we can filter with them
    tag_list = ["cycleway", "bicycle", "cycleway:right",
                "cycleway:left", "cyclestreet", "bicycle_road"]
    for tag_name in tag_list:
        if tag_name not in ox.settings.useful_tags_way:
            ox.settings.useful_tags_way += [tag_name]
    
    # # Get the polygon of Copenhagen and Frederiksberg
    # #TODO: Find a geocode for Copenhagen, old one doesn't work anymore
    # cop = ox.geocode_to_gdf("Copenhagen Municipality")
    # fre = ox.geocode_to_gdf("Frederiksberg Municipality")
    cop = gpd.read_file("polygon_copenhagen.geojson")
    fre = gpd.read_file("polygon_frederiksberg.geojson")
    polygon = shapely.ops.unary_union([cop['geometry'][0], fre['geometry'][0]])
    
    # Get the non-simplified graph with the extended list of attributes
    G = ox.graph_from_polygon(polygon, simplify=False)
    
    # REGION_COORD = [55.716, 55.555, 12.489, 12.681]
    # G = ox.graph_from_bbox(*REGION_COORD, simplify=False)
    G_sim = simplification.simplify_graph(G)
    G_com = ox.simplify_graph(G)
    
    # Use to get at look a edges attributes we get with this query
    # ignore_attr = ['length', 'width', 'osmid', 'ref', 'name']
    # edge_attr = utils.get_every_edge_attributes(G, ignore_key_list=ignore_attr)
    
    # Make dictionary of protected bicycle infrastructure
    protected_dict = dict()
    protected_dict["cycleway"] = "track"
    protected_dict["cycleway:right"] = "track"
    protected_dict["cycleway:left"] = "track"
    protected_dict["bicycle_road"] = "yes"
    protected_dict["bicycle"] = "designated"
    protected_dict["highway"] = "cycleway"
    
    # Create new attribute to simplify it
    H = utils.add_edge_attribute(G, protected_dict, 'protected_bicycling')
    
    H_sim = simplification.simplify_graph(H, attributes='protected_bicycling')
    H_fin = simplification.multidigraph_to_graph(
        H_sim, attributes='protected_bicycling', verbose=True
        )
    H_mul = H_fin.copy()
    # Count the number of protected edges and change bool into binary int
    count_protected = 0
    for edge in H_mul.edges:
        if H_mul.edges[edge]['protected_bicycling'] is True:
            H_mul.edges[edge]['protected_bicycling'] = 1
            count_protected += 1
        else:
            H_mul.edges[edge]['protected_bicycling'] = 0
    num_edges = len(list(H_mul.edges))
    ratio = 1 - (num_edges - count_protected) / num_edges
    print("{}% of protected edges".format(round((ratio * 100), 2)))

    # Basic statistics
    print("""
          {} nodes and {} edges in original graph G \n
          {} nodes and {} edges in traditional simplified graph G_sim \n
          {} nodes and {} edges in OSMnx simplified graph G_com \n
          {} nodes and {} edges in multilayer simplified graph H_sim \n
          {} nodes and {} edges in final graph H_fin
          """.format(len(list(G.nodes())), len(list(G.edges())),
          len(list(G_sim.nodes())), len(list(G_sim.edges())),
          len(list(G_com.nodes())), len(list(G_com.edges())),
          len(list(H_sim.nodes())), len(list(H_sim.edges())),
          len(list(H_fin.nodes())), len(list(H_fin.edges()))))

    # Use binary int for visualization
    ec = ox.plot.get_edge_colors_by_attr(H_mul, 'protected_bicycling',
                                         cmap='bwr')
    H_mul = nx.MultiGraph(H_mul)
    # Red is protected, blue unprotected
    ox.plot_graph(H_mul, figsize = (12, 8), bgcolor='w',
                  node_color='black', node_size=5,
                  edge_color=ec, edge_linewidth=2)

    # nx.write_gpickle(H_fin, "copenhagen_graph_simplified.gpickle")
    
    
    