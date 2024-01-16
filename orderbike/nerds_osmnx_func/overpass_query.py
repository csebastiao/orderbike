# -*- coding: utf-8 -*-
"""
Functions in order to make complex overpass query through osmnx. Use
get_filter_graphs to get graph for specific filter, then create the union
with compose_graph. Is a proxy of the lack of "or" syntax between keys,
only able to make "or" inside keys or "and" between keys.
"""

import osmnx as ox
import networkx as nx
import shapely
from tqdm import tqdm


def get_filtered_graphs(polygon, filter_dict):
    """
    Get every filtered graph coming from a polygon, based on value given as
    a dictionary.

    Parameters
    ----------
    polygon : shapely.MultiPolygon
        Polygon where we will search for with osmnx.graph_from_polygon.
    filter_dict : dict
        Dictionary composed of dictionaries with the following structure :
            {'name1' : {'custom_filter' : filter1},
             'name2' : {'network_type'} : type2}
        The dictionary for every key have either 'custom_filter' or
        'network_type' as a key, and the following filter or type as a value.

    Returns
    -------
    graph_dict : dict
        Dictionary of every graph.

    """
    graph_dict = dict()
    for filter_info in filter_dict.values(): # add useful tag way into
        if 'custom_filter' in filter_info: # the osmnx settings to get them
            _add_tag_way(filter_info['custom_filter'])
    for filter_id, filter_info in tqdm(filter_dict.items(), #tqdm show progress
                                       desc='Networks', leave=True):
        for i in range(0, 10): # retry
            try: # either custom_filter or network_type, get graph with osmnx
                if 'custom_filter' in filter_info:
                    graph_dict[filter_id] = ox.graph_from_polygon(
                        polygon,
                        custom_filter=(filter_info['custom_filter']),
                        retain_all=True,
                        simplify=False
                        )
                elif 'network_type' in filter_info:
                    graph_dict[filter_id] = ox.graph_from_polygon(
                        polygon,
                        network_type = (filter_info['network_type']),
                        retain_all=True,
                        simplify=False
                        )
            except ValueError: # for empty graph because of the filter used
                graph_dict[filter_id] = nx.empty_graph(
                    create_using=nx.MultiDiGraph
                    )
                break
            except:
                continue
            break
    return graph_dict


def _add_tag_way(filter_string):
    """Add way's tag if not present in the osmnx settings"""
    split_string = filter_string.split(']') # mark end of one attribute
    for i in range(len(split_string) - 1): # avoid last void value
        split_string[i] = split_string[i].split('"')
        split_string[i] = split_string[i][1] # avoid first [ string
    for tag_name in split_string[:-1]: # avoid last void string
        if tag_name not in  ox.settings.useful_tags_way:
            ox.settings.useful_tags_way += [tag_name]


def compose_graph(graph_dict, composed_name, name_list):
    """
    Compose multiple graph together coming from a dictionary under a new
    entry of the dictionary.

    Parameters
    ----------
    graph_dict : dict
        Dictionary of every graph.
    composed_name : str
        Name of the new key of graph_dict with the composed graph.
    name_list : list of str
        Keys of the graph we want to merge.

    Raises
    ------
    ValueError
        If the number of key is inferior to 2, can't merge one graph.

    Returns
    -------
    graph_dict : dict
        Dictionary of every graph.

    """
    if len(name_list) < 2: # can't compose
        raise ValueError('Not enough subgraph to compose, need at least 2')
    elif len(name_list) == 2: # if exactly 2 use networkx.compose
        graph_dict[composed_name] = nx.compose(graph_dict[name_list[0]],
                                               graph_dict[name_list[1]])
    else: # more than 2 use networkx.compose_all
        subgraph_list = []
        for name in name_list:
            subgraph_list.append(graph_dict[name])
        graph_dict[composed_name] = nx.compose_all(subgraph_list)
    return graph_dict


if __name__ == "__main__":
    cop = ox.geocode_to_gdf("Copenhagen Municipality")
    fre = ox.geocode_to_gdf("Frederiksberg Municipality")
    location = shapely.ops.unary_union([cop['geometry'][0],
                                          fre['geometry'][0]])

    osmnxparameters = {'car30': {'custom_filter':
                                 '["maxspeed"~"^30$|^20$|^15$|^10$|^5$|^20 mph|^15 mph|^10 mph|^5 mph"]'},
                       'carall': {'network_type':
                                  'drive'},
                   'bike_cyclewaytrack': {'custom_filter':
                                          '["cycleway"~"track"]'},
                   'bike_highwaycycleway': {'custom_filter':
                                            '["highway"~"cycleway"]'},
                   'bike_designatedpath': {'custom_filter':
                                           '["highway"~"path"]["bicycle"~"designated"]'},
                   'bike_cyclewayrighttrack': {'custom_filter':
                                               '["cycleway:right"~"track"]'},
                   'bike_cyclewaylefttrack': {'custom_filter':
                                              '["cycleway:left"~"track"]'},
                   'bike_cyclestreet': {'custom_filter':
                                        '["cyclestreet"]'},
                   'bike_bicycleroad': {'custom_filter':
                                        '["bicycle_road"]'},
                   'bike_livingstreet': {'custom_filter':
                                         '["highway"~"living_street"]'}
                  }

    Gs = get_filtered_graphs(location, osmnxparameters)

    Gs = compose_graph(Gs, 'biketrack', ['bike_cyclewaylefttrack',
                                         'bike_cyclewaytrack',
                                         'bike_highwaycycleway',
                                         'bike_bicycleroad',
                                         'bike_cyclewayrighttrack',
                                         'bike_designatedpath',
                                         'bike_cyclestreet'])
    Gs = compose_graph(Gs, 'bikeable', ['biketrack',
                                        'car30',
                                        'bike_livingstreet'])
    Gs = compose_graph(Gs, 'biketrackcarall', ['biketrack',
                                               'carall'])
    #nx.write_graphml(Gs['biketrack'], 'copenhagen_biketrack.graphml')
    nx.write_gpickle(Gs['biketrack'], 'copenhagen_biketrack.pickle')
