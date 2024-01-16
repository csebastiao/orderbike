# -*- coding: utf-8 -*-
"""
Useful functions to manipulate edge attributes of a networkx graph.
"""

import networkx as nx

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

