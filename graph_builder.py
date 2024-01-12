import time
import geopandas as gpd
import networkx as nx
import pandas as pd
from shapely.geometry import Point, LineString
from database import graph_query,poi_query


def build_graph(start_3857, end_3857, buffer_distance, engine):
    # Create a bounding box around place A and place B in SRID 3857
    bbox = (
        max(start_3857.x, end_3857.x) + buffer_distance,
        max(start_3857.y, end_3857.y) + buffer_distance,
        min(start_3857.x, end_3857.x) - buffer_distance,
        min(start_3857.y, end_3857.y) - buffer_distance,
    )

    # Load a subset of the road network as a GeoDataFrame using SQLAlchemy connection
    
    #AND highway NOT IN ('track', 'service', 'cycleway', 'pedestrian', 'footway', 'steps', 'living_street', 'path', 'construction', 'proposed', 'rest_area', 'raceway', 'planned', 'platform', 'services')
    gdf = gpd.read_postgis(graph_query, engine, geom_col='way', params=(bbox[0], bbox[1], bbox[2], bbox[3]))
    gdf = gdf.to_crs(epsg=3857)
    # Create a graph representation of the road network
    G = nx.Graph()
    for idx, row in gdf.iterrows():
        geom = row['way']
        maxspeed = row['maxspeed'] if not pd.isna(row['maxspeed']) and row['maxspeed'] > 19 else 90
        length = geom.length / 1000
        travel_time = length / maxspeed
        G.add_edge(geom.coords[0], geom.coords[-1], travel_time=travel_time, maxspeed=maxspeed, length=length)

    return G
def segments(curve):
    return list(map(LineString, zip(curve.coords[:-1], curve.coords[1:])))
    # Helper function to find the nearest node in the graph
def nearest_node(lon, lat, graph):
    distance_dict = {}
    for node in graph.nodes():
        point = Point(node)
        distance = point.distance(Point(lon, lat))
        distance_dict[node] = distance
    return min(distance_dict, key=distance_dict.get)

def find_stop_node(shortest_path, stop_weight, stop_value, graph, is_reversed ):
    temp_travel_length = 0.0
    if is_reversed:
        total_path_length = path_length(shortest_path, graph, stop_weight)
        stop_value = total_path_length - stop_value * 1.1

    else:
        stop_value = stop_value * 0.9

    for i in range (len(shortest_path) -1):
            node1 = shortest_path[i]
            node2 = shortest_path[i + 1]

            # Get the travel time for the edge between node1 and node2
            edge_data = graph.get_edge_data(node1, node2)
            temp_travel_length += edge_data[stop_weight]

            if temp_travel_length > stop_value :
                return i   
            
def path_length(shortest_path, graph, weight):
    total_length = 0
    for i in range(len(shortest_path) - 1):
        node1 = shortest_path[i]
        node2 = shortest_path[i + 1]

        # Get the travel time for the edge between node1 and node2
        edge_data = graph.get_edge_data(node1, node2)
        total_length += edge_data[weight]
    return total_length

def find_new_path_with_poi(shortest_path, stop_node_id, engine, graph, start_node, end_node, weight, max_extend, weight_extend, poi_type):
    primary_length = path_length(shortest_path, graph, weight_extend)
    while(stop_node_id>0):
        path_break = Point(shortest_path[stop_node_id])
        
        gdf = gpd.read_postgis(poi_query, engine, geom_col='way', params=(path_break.x, path_break.y, path_break.x, path_break.y,poi_type, path_break.x, path_break.y))

        # Create a graph representation of the road network
        poi_point = Point()
        for idx, row in gdf.iterrows():
            geom = row['way']
            poi_point = Point(geom.coords[0])
            poi_node = nearest_node(poi_point.x, poi_point.y, graph)
            try:
                shortest_path_to_poi = nx.shortest_path(graph, source=start_node, target=poi_node, weight=weight)
                shortest_path_from_poi = nx.shortest_path(graph, source=poi_node, target=end_node, weight=weight)
                
                shortest_path_with_poi = shortest_path_to_poi + shortest_path_from_poi[1:len(shortest_path_from_poi)]
                new_length = path_length(shortest_path_with_poi, graph, weight_extend)
                print(f"extend: {new_length - primary_length}")
                if new_length - primary_length < max_extend:
                    return shortest_path_with_poi
                else :
                    continue
            except nx.NetworkXNoPath:
                print("POI is outside the graph")
                continue
        stop_node_id = stop_node_id - 1

    return shortest_path_with_poi