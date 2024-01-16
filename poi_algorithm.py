import time
import psycopg2
import networkx as nx
from sqlalchemy import create_engine
from shapely.geometry import Point
import pyproj
import matplotlib.pyplot as plt
import folium
from graph_builder import build_graph, find_stop_node, nearest_node, path_length, find_new_path_with_poi
from database import db_uri

from geopy.geocoders import Nominatim

transformer_to_3857 = pyproj.Transformer.from_crs(4326, 3857, always_xy = True)
transformer_to_4326 = pyproj.Transformer.from_crs(3857, 4326, always_xy = True)

def run_poi_pathfinder_algorithm(parameters):
    # Extract parameters
    starting_loc = parameters["start_location"]
    end_loc = parameters["end_location"]
    max_ext_type = parameters["max_ext_type"]
    max_time_ext = parameters["max_time_ext"]
    max_road_ext = parameters["max_road_ext"]
    poi_requirements_type = parameters["poi_requirements_type"] # "time" or "road"
    poi_from_type = parameters["poi_from_type"] # "begin" or "end"
    poi_from_val = parameters["poi_from_val"]

    # Set algorithm's parameters
    weight = "length" # 
    weight_extend = "travel_time" if max_ext_type == "time" else "length"
    max_extend = max_time_ext if weight_extend == "travel_time" else max_road_ext
    stop_weight = "travel_time" if poi_requirements_type == "time" else "length"
    stop_value = poi_from_val

    is_reversed = False if poi_from_type == "begin" else True
    poi_types = tuple(parameters["poi_types"])

    geolocator = Nominatim(user_agent = "poi_pathfinder_app")
    start_loc_coords = geolocator.geocode(parameters["start_location"])
    end_loc_coords = geolocator.geocode(parameters["end_location"])
    start_point = None
    end_point = None

    if start_loc_coords and end_loc_coords:
        print(f"Start point: {starting_loc} ({start_loc_coords.longitude}, {start_loc_coords.latitude})")
        print(f"End point: {end_loc} ({end_loc_coords.longitude}, {end_loc_coords.latitude})")
        start_point = Point(start_loc_coords.longitude, start_loc_coords.latitude)
        end_point = Point(end_loc_coords.longitude, end_loc_coords.latitude)
    else:
        print("[ERROR] Start or end point could not be localized.")
        return None
    
    # Create an SQLAlchemy engine and connect to the database
    engine = create_engine(db_uri)

    # Convert place A and place B coordinates to SRID 3857 (Web Mercator)
    start_time = time.time()
    start_3857 = Point(transformer_to_3857.transform(start_point.x, start_point.y))
    end_3857 = Point(transformer_to_3857.transform(end_point.x, end_point.y))

    # Buffer distance around place A and place B to create a subset (adjust as needed)
    buffer_distance = 10000  # in meters

    graph = build_graph(start_3857, end_3857, buffer_distance, engine)

    # Find the nearest nodes to place A and place B within the subset
    start_node = nearest_node(start_3857.x, start_3857.y, graph)
    end_node = nearest_node(end_3857.x, end_3857.y, graph)

    end_time = time.time()
    elapsed_time_graph = end_time - start_time

    # Find the shortest path
    start_time = time.time()
    shortest_path = nx.shortest_path(graph, source = start_node, target = end_node, weight = weight)
    end_time = time.time()
    elapsed_time1 = end_time - start_time

    start_time2 = time.time()

    stop_node_id = find_stop_node(shortest_path, stop_weight, stop_value, graph, is_reversed)
    if stop_node_id == None:
        return None, None

    # Find the new shortest path
    shortest_path_with_poi, poi_point = find_new_path_with_poi(
        shortest_path,
        stop_node_id,
        engine,
        graph,
        start_node,
        end_node,
        weight,
        max_extend,
        weight_extend,
        poi_types
    )

    end_time2 = time.time()
    elapsed_time2 = end_time2 - start_time2

    # Calculate the total travel time by summing the travel times of each edge in the path
    if shortest_path_with_poi != None:
        print(f"Start point : {start_point.y, start_point.x}. End point: {end_point.y, end_point.x}")
        print('Old path')
        print(f'Total time {path_length(shortest_path, graph, "travel_time")}')
        print(f'Total Length {path_length(shortest_path, graph, "length")}')
        print(f"First path was fined in : {elapsed_time1} seconds")
        print('New path')
        print(f'Total time {path_length(shortest_path_with_poi, graph, "travel_time")}')
        print(f'Total Length {path_length(shortest_path_with_poi, graph, "length")}')     
        print(f"New Path was fined in: {elapsed_time2} seconds")
        print(f"Graph was generated: {elapsed_time_graph} seconds")

    # Close the SQLAlchemy engine
    engine.dispose()

    return shortest_path_with_poi, poi_point

