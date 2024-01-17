"""Get the simplified network of Copenhagen, keeping the bicycle network in a single boolean attribute."""
import osmnx as ox
import shapely


def add_edge_attribute(G, attr_dict, name):
    """
    Add an attribute from a dictionary.
    """
    G = G.copy()
    for edge in G.edges:
        if name in G.edges[edge]:
            err = f"{name} already in edge {edge}, use a new name"
            raise NameError(err)
        for key in list(attr_dict.keys()):
            if key in list(G.edges[edge].keys()):
                if G.edges[edge][key] in attr_dict[key]:
                    G.edges[edge][name] = 1
                    break
                G.edges[edge][name] = 0
    return G


# First add every necessary tag on the tag_list so we can filter with them
tag_list = [
    "sidewalk:left:bicycle",
    "sidewalk:right:bicycle",
    "cycleway:left",
    "cycleway:right",
    "cycleway",
    "cycleway:both",
    "cyclestreet",
    "bicycle",
    "bicycle_road",
]
for tag_name in tag_list:
    if tag_name not in ox.settings.useful_tags_way:
        ox.settings.useful_tags_way += [tag_name]

# Get the polygon of Copenhagen and Frederiksberg
cop = ox.geocode_to_gdf("Copenhagen Municipality")
fre = ox.geocode_to_gdf("Frederiksberg Municipality")
polygon = shapely.ops.unary_union([cop["geometry"][0], fre["geometry"][0]])
# Get the non-simplified graph with the extended list of attributes
G = ox.graph_from_polygon(polygon, simplify=False)
# Make dictionary of protected bicycle infrastructure
protected_dict = {}
protected_dict["sidewalk:left:bicycle"] = "yes"
protected_dict["sidewalk:left:right"] = "yes"
protected_dict["cycleway:left"] = ["shared_lane", "shared_busway", "track"]
protected_dict["cycleway:right"] = ["shared_lane", "shared_busway", "track"]
protected_dict["cycleway:both"] = "lane"
protected_dict["cycleway"] = [
    "shared_lane",
    "shared_busway",
    "opposite_lane",
    "opposite",
]
protected_dict["bicycle"] = ["designated", "yes", "official", "use_sidepath"]
protected_dict["highway"] = ["cycleway", "bridleway"]
protected_dict["cyclestreet"] = "yes"
protected_dict["bicycle_road"] = "yes"
# Add as boolean attribute for all values and simplify the network with it
G = add_edge_attribute(G, protected_dict, "protected_bicycling")
G = ox.simplify_graph(G, attributes=["protected_bicycling"])
ec = ox.plot.get_edge_colors_by_attr(G, "protected_bicycling", cmap="bwr")
# Red is protected, blue unprotected
ox.plot_graph(
    G,
    figsize=(12, 8),
    bgcolor="w",
    node_color="black",
    node_size=10,
    edge_color=ec,
    edge_linewidth=1.5,
)
