# -*- coding: utf-8 -*-
"""
New functions and original and modified functions from OSMnx in order to
simplify the graph by removing interstitial nodes and by going from a
multidigraph to a graph.
"""

import numpy as np
import shapely
from shapely.geometry import LineString
from shapely.geometry import Point
import networkx as nx
from haversine import haversine
from haversine import Unit
import osmnx as ox

def get_every_edge_attributes(G, ignore_key=[]):
    """
    Get all the possible value for all attributes for edges of the graph
    except the ones on a given ignore list.
    See also get_specific_edge_attributes

    Parameters
    ----------
    G : networkx Graph/DiGraph/MultiGraph/MultiDiGraph/...
        Graph where we want to simplify an attribute.

    ignore_key : list or singleton, optional
        Key we want to ignore. The default is [].

    Returns
    -------
    attr_dict : dict
        Dictionary of every possible values for every attributes except the
        ignored ones.

    """
    attr_dict = dict()
    for edge in G.edges:
        for attr in list(G.edges[edge].keys()):
            if isinstance(ignore_key, list):
                if attr in ignore_key:
                    pass
                elif attr in attr_dict:
                    if G.edges[edge][attr] in attr_dict[attr]:
                        pass
                    else:
                        attr_dict[attr].append(G.edges[edge][attr])
                else:
                    attr_dict[attr] = [G.edges[edge][attr]]
            else:
                if attr is ignore_key:
                    pass
                elif attr in attr_dict:
                    if G.edges[edge][attr] in attr_dict[attr]:
                        pass
                    else:
                        attr_dict[attr].append(G.edges[edge][attr])
                else:
                    attr_dict[attr] = [G.edges[edge][attr]]
    return attr_dict


def get_specific_edge_attributes(G, take_key_list):
    """
    Get all the possible value for specific attributes for edges of the graph.
    See also get_every_edge_attributes

    Parameters
    ----------
    G : networkx Graph/DiGraph/MultiGraph/MultiDiGraph/...
        Graph where we want to simplify an attribute.
    take_key_list : list of str or str
        List of the key we want to get.

    Returns
    -------
    attr_dict : dict
        Dictionary of every possible values for specified attributes.

    """
    attr_dict = dict()
    if isinstance(take_key_list, list):
        for key in take_key_list:
            attr_dict[key] = []
        for edge in G.edges:
            for attr in list(G.edges[edge].keys()):
                if attr in take_key_list:
                    if G.edges[edge][attr] in attr_dict[attr]:
                        pass
                    else:
                        attr_dict[attr].append(G.edges[edge][attr])
    else:
        attr_dict[take_key_list] = []
        for edge in G.edges:
            if take_key_list in list(G.edges[edge].keys()):
                if G.edges[edge][take_key_list] in attr_dict[take_key_list]:
                    pass
                else:
                    attr_dict[take_key_list].append(
                        G.edges[edge][take_key_list])
    return attr_dict


def simplify_edge_attribute_name(G, key, name_list, simple_name):
    """
    Simplify an arbitrary list of name values for a given key into one.

    Parameters
    ----------
    G : networkx Graph/DiGraph/MultiGraph/MultiDiGraph/...
        Graph where we want to simplify an attribute.
    key : str
        Name of the edges' attributes.
    name_list : list
        List of values for the given attribute we want to merge into one.
    simple_name : str
        Name for the fusion of every values in the given list.

    Returns
    -------
    G : networkx Graph/DiGraph/MultiGraph/MultiDiGraph/...
        Graph with the modified attribute.

    """
    G = G.copy()
    for edge in G.edges:
        if key in list(G.edges[edge].keys()):
            if G.edges[edge][key] in name_list:
                G.edges[edge][key] = simple_name
    return G


def add_edge_attribute(G, attr_dict, name, bool_response=True):
    """
    Add an edge attribute where the value are binary bool based on
    whether the edge have a specific value for a given attribute,
    given as a dictionary.

    Parameters
    ----------
    G : networkx Graph/DiGraph/MultiGraph/MultiDiGraph/...
        Graph on which we want to add an attribute.
    attr_dict : dict
        Dictionary where the key are the key of the edges' attributes
        and values are the values of those attributes that we want to
        take into account.
    name : str
        Name of the new attribute.
    bool_response : bool, optional
        Bool response if we find one of the values on one of the
        attributes of the edges from the dictionary.
        The default is True.

    Raises
    ------
    NameError
        Raised if the name is already an attribute of an edge
        of the graph, in order to avoid unintended mix.

    Returns
    -------
    G : networkx Graph/DiGraph/MultiGraph/MultiDiGraph/...
        Graph with the new binary attribute.

    """
    G = G.copy()
    for edge in G.edges:
        if name in G.edges[edge]:
            raise NameError(
                "New attribute {} already in edge {}, use a new name".format(
                    name, edge)
                )
        for key in list(attr_dict.keys()):
            if key in list(G.edges[edge].keys()):
                if G.edges[edge][key] in attr_dict[key]:
                    G.edges[edge][name] = bool_response
                    break # otherwise next key can replace the value
                else:
                    G.edges[edge][name] = not bool_response
    return G



# New function
def multidigraph_to_graph(G, attributes=None,
                          verbose=False, debug=False):
    """
    Transform a MultiDiGraph into an undirected Graph by first removing
    the direction, making a MultiGraph, and then making it a Graph by
    making sure that there is no multiple edges : for self-loop we create
    two nodes within the geometry of the edge, for node with multiple
    edges we create one node within each geometry of the edge. We avoid
    to merge directed edges without the same arbitrary attributes.

    Parameters
    ----------
    G : networkx.classes.multidigraph.MultiDiGraph
        MultiDiGraph we want to transform.
    attributes : list or str or number, optional
        Key to the attributes we want to discriminate.
        The default is None.
    verbose : bool, optional
        If True, give the number of self-loop and multiple path found,
        and the nodes with multiple straight edge between
        (sign of bad OSM practice). The default is False.
    debug : bool, optional
        If True, return a dictionary with every osmid and geometry of
        self-loop and multiple path. The default is False.

    Returns
    -------
    G : networkx.classes.graph.Graph
        Undirected graph made from the initial MultiDiGraph.
    debug_dict : dict
        Dictionary of every osmid and geometry of self-loop and multiple
        path to return only if debug is True.

    """
    if verbose is True:
        self_loop_count = 0
        multiple_path_count = dict()
    if debug is True:
        debug_dict = dict()
        debug_dict['self-loop'] = []
        debug_dict['multiple-path'] = []
    G = get_undirected(G, attributes=attributes) # make it undirected
    initial_node_list = list(G.nodes()) # to avoid issue with changing
    for node in initial_node_list: # number of node during the process
        neighbors = np.transpose(list(G.edges(node)))[1]
        if node in neighbors: # then self_loop, need 2 artifical nodes
            for k in list(G.get_edge_data(node, node).keys()):
                if verbose is True:
                    self_loop_count +=1
                if debug is True:
                    debug_dict['self-loop'].append([
                        G.edges[node, node, k]['osmid'],
                        G.edges[node, node, k]['geometry']])
                G = _solve_self_loop(G, node, k)
        for neigh in neighbors:
            if G.number_of_edges(node, neigh) > 1: #then multiple path, need 1
                if verbose is True:
                    if G.number_of_edges(node, neigh) in multiple_path_count:
                        multiple_path_count[
                            G.number_of_edges(node, neigh)] += 1
                    else:
                        multiple_path_count[
                            G.number_of_edges(node, neigh)] = 1
                if debug is True:
                    for k in list(G.get_edge_data(node, neigh).keys()):
                        debug_dict['multiple-path'].append([
                            G.edges[node, neigh, k]['osmid'],
                            G.edges[node, neigh, k]['geometry']])
                G = _solve_multiple_path(G, node, neigh, verbose=verbose)
    G = nx.Graph(G) #if no multiple edges, simply change the type
    if verbose is True:
        print("""
              Number of self-loop found : {} \n
              Number of multiple path between nodes found : {}
              """.format(self_loop_count, multiple_path_count)
              )
    if debug is True:
        return G, debug_dict
    return G


# New function
def _solve_self_loop(G, node, key):
    """
    Transform a loop where a node is connected to itself by adding two 
    nodes in the geometry of the loop, in order to make it simple
    (no multiple edges)

    Parameters
    ----------
    G : networkx.MultiGraph
        MultiGraph we want to transform.
    node : int
        Node's ID where there is a self-loop.
    key : int
        Key of the edge, needed because the graph is a MultiGraph

    Returns
    -------
    G : networkx.MultiGraph
        MultiGraph with the self-loop resolved.

    """
    edge_attributes = dict(G.edges[node, node, key]) # take attributes
    geom = list(edge_attributes['geometry'].coords[:])
    edge_attributes.pop('geometry') # remove geometry
    edge_attributes.pop('length') # remove length
    G.remove_edge(node, node, key)
    f_num = node + 1 # find unique ID not already in the graph
    while f_num in G.nodes():
        f_num += 1
    s_num = f_num + 1
    while s_num in G.nodes():
        s_num += 1
    # TODO : add street_count to nodes ?
    # Add nodes as the first and last point in the LineString geometry
    # if we don't count the original node of the self-loop
    G.add_node(f_num, x=geom[1][0], y=geom[1][1])
    G.add_node(s_num, x=geom[-2][0], y=geom[-2][1])
    # Connect them with edges keeping the attributes and having in total
    # the same geometry as before
    G.add_edge(node, f_num, key=0, **edge_attributes,
               geometry=LineString(geom[:2]),
               length=_get_length(G, node, f_num))
    G.add_edge(node, s_num, key=0, **edge_attributes,
               geometry=LineString(geom[-2:]),
               length=_get_length(G, node, s_num))
    G.add_edge(f_num, s_num, key=0, **edge_attributes,
               geometry=LineString(geom[1:-1]),
               length=_get_length(G, s_num, f_num))
    return G

# New function
def _solve_multiple_path(G, node, other_node, verbose=False):
    """
    Transform multiple paths between nodes by adding artifical nodes on every
    path but one, in order to make it simple (no multiple edges)

    Parameters
    ----------
    G : networkx.classes.multidigraph.MultiDiGraph
        MultiDiGraph we want to transform.
    node : int
        First node's ID.
    other_node : int
        Second node's ID.
    verbose : bool, optional
        If True, give  the nodes with multiple straight edge between
        (sign of bad OSM practice) and their keys. The default is False.

    Returns
    -------
    G : networkx.classes.multidigraph.MultiDiGraph
        MultiDiGraph with the multiple path issue solved.

    """
    # for every path but one, to add as little number of node as needed
    count = 0
    straigth_key = []
    initial_n_edges = G.number_of_edges(node, other_node)
    initial_key_list = list(G.get_edge_data(node, other_node).keys())
    for i in initial_key_list:
        if count == initial_n_edges - 1:
            break
        elif len(list(
                G.edges[node, other_node, i]['geometry'].coords[:]
                )) > 2:
            # take attributes
            edge_attributes = dict(G.edges[node, other_node, i])
            geom = list(edge_attributes['geometry'].coords[:])
            edge_attributes.pop('geometry') #remove geometry
            edge_attributes.pop('length') # remove length
            G.remove_edge(node, other_node, i)
            p_num = node + 1 # find ID that is not already in the graph
            while p_num in G.nodes():
                p_num += 1
            # add node as the first point of the geometry
            G.add_node(p_num, x=geom[1][0], y=geom[1][1])
            # Connect it with edges keeping the attributes and having in total
            # the same geometry as before
            G.add_edge(node, p_num, key=0, **edge_attributes,
                       geometry = LineString(geom[:2]),
                       length=_get_length(G, node, p_num))
            G.add_edge(p_num, other_node, key=0, **edge_attributes,
                       geometry=LineString(geom[1:]),
                       length=_get_length(G, other_node, p_num))
            count += 1
        else: #if straight line
            straigth_key.append(i)
    if count < G.number_of_edges(node, other_node) - 1:
        if verbose is True:
            print("""
                  Multiple straight path between node {} and {} 
                  at the keys {}
                  """.format(node, other_node, straigth_key))
        while count < G.number_of_edges(node, other_node) - 1:
            f_key = straigth_key[0]
            edge_attributes = dict(G.edges[node, other_node, f_key])
            geom = list(edge_attributes['geometry'].coords[:])
            edge_attributes.pop('geometry') #remove geometry
            edge_attributes.pop('length') # remove length
            mid_x = (geom[0][0]+geom[1][0]) / 2. # take middle coordinates
            mid_y = (geom[0][1]+geom[1][1]) / 2.
            geom.insert(1, (mid_x, mid_y)) # insert it into the geometry
            G.remove_edge(node, other_node, f_key)
            p_num = node + 1# find ID that is not already in the graph
            while p_num in G.nodes():
                p_num += 1
            # add node as the first point of the geometry
            G.add_node(p_num, x=geom[1][0], y=geom[1][1])
            # Connect it with edges keeping the attributes and having in total
            # the same geometry as before
            G.add_edge(node, p_num, key=0, **edge_attributes,
                       geometry=LineString(geom[:2]),
                       length=_get_length(G, node, p_num))
            G.add_edge(p_num, other_node, key=0, **edge_attributes,
                       geometry=LineString(geom[1:]),
                       length=_get_length(G, other_node, p_num))
            straigth_key.remove(f_key)
            count += 1
    return G

# New function
def _get_length(G, f_node, s_node):
    """Return the haversine length in meters between two nodes like OSM."""
    f_point = [G.nodes[f_node]['y'], G.nodes[f_node]['x']] #[lat, lon]
    s_point = [G.nodes[s_node]['y'], G.nodes[s_node]['x']]
    return round(haversine(f_point, s_point, unit=Unit.METERS), 3)

# Modified function
def get_undirected(G, attributes=None):
    """
    Convert MultiDiGraph to undirected MultiGraph.

    Maintains parallel edges only if their geometries or other selected
    attributes differ. Note: see also `get_digraph` to convert 
    MultiDiGraph to DiGraph.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        input graph

    Returns
    -------
    networkx.MultiGraph
    """
    # make a copy to not mutate original graph object caller passed in
    G = G.copy()

    for u, v, d in G.edges(data=True):
        # add geometry if missing, to compare parallel edges' geometries
        if "geometry" not in d:
            point_u = (G.nodes[u]["x"], G.nodes[u]["y"])
            point_v = (G.nodes[v]["x"], G.nodes[v]["y"])
            d["geometry"] = LineString([point_u, point_v])

    # increment parallel edges' keys so we don't retain only one edge of sets
    # of true parallel edges when we convert from MultiDiGraph to MultiGraph
    G = ox._update_edge_keys(G)

    # convert MultiDiGraph to MultiGraph, retaining edges in both directions
    # of parallel edges and self-loops for now
    H = nx.MultiGraph(**G.graph)
    H.add_nodes_from(G.nodes(data=True))
    H.add_edges_from(G.edges(keys=True, data=True))

    # the previous operation added all directed edges from G as undirected
    # edges in H. we now have duplicate edges for every bidirectional parallel
    # edge or self-loop. so, look through the edges and remove any duplicates.
    duplicate_edges = set()
    for u1, v1, key1, data1 in H.edges(keys=True, data=True):

        # if we haven't already flagged this edge as a duplicate
        if (u1, v1, key1) not in duplicate_edges:

            # look at every other edge between u and v, one at a time
            for key2 in H[u1][v1]:

                # don't compare this edge to itself
                if key1 != key2:

                    # compare the first edge's data to the second's
                    # if they match up, flag the duplicate for removal
                    data2 = H.edges[u1, v1, key2]
                    if _is_duplicate_edge(data1, data2, attributes=attributes):
                        duplicate_edges.add((u1, v1, key2))

    H.remove_edges_from(duplicate_edges)
    return H

# Modified function
def _is_duplicate_edge(data1, data2, attributes=None):
    """
    Check if two graph edge data dicts have the same osmid and geometry.

    Parameters
    ----------
    data1: dict
        the first edge's data
    data2 : dict
        the second edge's data

    Returns
    -------
    is_dupe : bool
    """
    is_dupe = False

    # if either edge's osmid contains multiple values (due to simplification)
    # compare them as sets to see if they contain the same values
    osmid1 = set(data1["osmid"]) if isinstance(data1["osmid"], list) else data1["osmid"]
    osmid2 = set(data2["osmid"]) if isinstance(data2["osmid"], list) else data2["osmid"]

    # if they contain the same osmid or set of osmids (due to simplification)
    if osmid1 == osmid2:

        # if both edges have geometry attributes and they match each other
        if ("geometry" in data1) and ("geometry" in data2):
            if ox._is_same_geometry(data1["geometry"], data2["geometry"]):
                is_dupe = True

        # if neither edge has a geometry attribute
        elif ("geometry" not in data1) and ("geometry" not in data2):
            is_dupe = True

        # if one edge has geometry attribute but the other doesn't:
        # not dupes
        else:
            pass

        if attributes is None:
            pass
        elif isinstance(attributes, list):
            for attr in attributes:
                if data1[attr] != data2[attr]:
                    is_dupe = False
                else:
                    pass
        else:
            if data1[attributes] != data2[attributes]:
                is_dupe = False

    return is_dupe


# Modified function
def momepy_simplify_graph(G, attributes=None,
                          strict=True, remove_rings=True):
    """
    Same as simplify_graph, but geometry is not taken into account in the same
    way : here it can take into account places where a geometry attribute
    already exist for edges.
    Simplify a graph's topology by removing interstitial nodes.

    Simplifies graph topology by removing all nodes that are not intersections
    or dead-ends. Create an edge directly between the end points that
    encapsulate them, but retain the geometry of the original edges, saved as
    a new `geometry` attribute on the new edge. Note that only simplified
    edges receive a `geometry` attribute. Some of the resulting consolidated
    edges may comprise multiple OSM ways, and if so, their multiple attribute
    values are stored as a list.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        input graph
    strict : bool
        if False, allow nodes to be end points even if they fail all other
        rules but have incident edges with different OSM IDs. Lets you keep
        nodes at elbow two-way intersections, but sometimes individual blocks
        have multiple OSM IDs within them too.
    remove_rings : bool
        if True, remove isolated self-contained rings that have no endpoints

    Returns
    -------
    G : networkx.MultiDiGraph
        topologically simplified graph, with a new `geometry` attribute on
        each simplified edge
    """
    if "simplified" in G.graph and G.graph["simplified"]:
        raise Exception("This graph has already been simplified, cannot simplify it again.")

    # define edge segment attributes to sum upon edge simplification
    attrs_to_sum = {"length", "travel_time"}

    # make a copy to not mutate original graph object caller passed in
    G = G.copy()
    all_nodes_to_remove = []
    all_edges_to_add = []
    

    # generate each path that needs to be simplified
    for path in ox._get_paths_to_simplify(G, attributes=attributes,
                                       strict=strict):
        # add the interstitial edges we're removing to a list so we can retain
        # their spatial geometry
        path_attributes = dict()
        geometry_batch = []
        for u, v in zip(path[:-1], path[1:]):

            # there should rarely be multiple edges between interstitial nodes
            # usually happens if OSM has duplicate ways digitized for just one
            # street... we will keep only one of the edges (see below)

            # get edge between these nodes: if multiple edges exist between
            # them (see above), we retain only one in the simplified graph
            edge_data = G.edges[u, v, 0]
            geometry_batch.append(edge_data['geometry'])
            for attr in edge_data:
                if attr == 'geometry':
                    pass
                if attr in path_attributes:
                    # if this key already exists in the dict, append it to the
                    # value list
                    path_attributes[attr].append(edge_data[attr])
                else:
                    # if this key doesn't already exist, set the value to a list
                    # containing the one value
                    path_attributes[attr] = [edge_data[attr]]

        # consolidate the path's edge segments' attribute values
        for attr in path_attributes:
            # we want to make a flat list to be able to hash it
            temp = path_attributes[attr]
            for i in range(len(temp)):
                if isinstance(temp[i],list):
                    pass
                else:
                    temp[i] = [temp[i]]
            temp = [item for sublist in temp for item in sublist]
            path_attributes[attr] = temp
            if attr in attrs_to_sum:
                # if this attribute must be summed, sum it now
                path_attributes[attr] = sum(path_attributes[attr])
            elif attr == 'geometry':
                pass
            elif len(set(path_attributes[attr])) == 1:
                # if there's only 1 unique value in this attribute list,
                # consolidate it to the single value (the zero-th):
                path_attributes[attr] = path_attributes[attr][0]
            else:
                # otherwise, if there are multiple values, keep one of each
                path_attributes[attr] = list(set(path_attributes[attr]))
                
        # construct the geometry and sum the lengths of the segments
        multi_line = shapely.geometry.MultiLineString(geometry_batch)
        path_attributes["geometry"] = shapely.ops.linemerge(multi_line)

        # add the nodes and edges to their lists for processing at the end
        all_nodes_to_remove.extend(path[1:-1])
        all_edges_to_add.append(
            {"origin": path[0], "destination": path[-1],
             "attr_dict": path_attributes}
        )
 
    # for each edge to add in the list we assembled, create a new edge between
    # the origin and destination
    for edge in all_edges_to_add:
        G.add_edge(edge["origin"], edge["destination"], **edge["attr_dict"])

    # finally remove all the interstitial nodes between the new edges
    G.remove_nodes_from(set(all_nodes_to_remove))

    if remove_rings:
        # remove any connected components that form a self-contained ring
        # without any endpoints
        wccs = nx.weakly_connected_components(G)
        nodes_in_rings = set()
        for wcc in wccs:
            if not any(ox._is_endpoint(G, n) for n in wcc):
                nodes_in_rings.update(wcc)
        G.remove_nodes_from(nodes_in_rings)

    # mark graph as having been simplified
    G.graph["simplified"] = True
    return G


def add_geometry_attribute(G):
    """Add geometry attribute for non-simplified edges"""
    G = G.copy()
    for edge in G.edges:
        if 'geometry' not in G.edges[edge]:
            f_node = [G.nodes[edge[0]]['x'], G.nodes[edge[0]]['y']]
            s_node = [G.nodes[edge[1]]['x'], G.nodes[edge[1]]['y']]
            G.edges[edge]['geometry'] = LineString([Point(*f_node),
                                                   Point(*s_node)])
    return G