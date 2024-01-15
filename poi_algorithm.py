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

    # DO POPRAWY TODO TODO TODO
    # max_time_ext = parameters["max_time_ext"]
    # max_road_ext = parameters["max_road_ext"]
    # poi_requirements_type = parameters["poi_requirements_type"]
    # poi_from_begin_road = parameters["poi_from_begin_road"]
    # poi_from_end_road = parameters["poi_from_end_road"]
    # poi_from_begin_time = parameters["poi_from_begin_time"]
    # poi_from_end_time = parameters["poi_from_end_time"]
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

    #Starting parameters
    # Warszawa- Łódź
    # start = Point(20.85950, 52.19354)
    # end = Point(19.4897, 51.801)
    # krakow - Gdańsk
    # start = Point(19.9450, 50.0647)
    # end = Point(18.6466, 54.3520)
    # #bialystok - Mrągowo
    # start = Point(23.1688, 53.1325)
    # end = Point(21.3049, 53.8642)

    weight = 'length' 
    stop_weight = 'travel_time'
    stop_value = 1.3
    weight_extend = 'travel_time'
    max_extend = 30
    is_reversed = False
    # stop_values = [1, 2]
    
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

    # for stop_value in stop_values:
    start_time2 = time.time()

    stop_node_id = find_stop_node(shortest_path, stop_weight, stop_value, graph, is_reversed)

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

    # Folium map
    # map_center = [(start_point.y + end_point.y) / 2, (start_point.x + end_point.x) / 2]
    # m = folium.Map(location = map_center, zoom_start = 9)

    # shortest_path_coords = [transformer_to_4326.transform(coord[0], coord[1]) for coord in shortest_path_with_poi]

    # # Add the shortest path as a PolyLine to the map
    # folium.PolyLine(locations = shortest_path_coords, color = 'blue', weight = 5).add_to(m)

    # # Save the map to an HTML file or display it
    # # m.save("shortest_path_map_szcz.html")
    # # m.save("shortest_path_map_szcz_kra.html")

    # shortest_path_coords = [transformer_to_4326.transform(coord[0], coord[1]) for coord in shortest_path]

    # m = folium.Map(location = map_center, zoom_start = 9)
    # # Add the shortest path as a PolyLine to the map
    # folium.PolyLine(locations=shortest_path_coords, color='blue', weight=5).add_to(m)

    # # Save the map to an HTML file or display it
    # m.save("shortest_path_map_szcz_kra_no_poi.html")

    # Close the SQLAlchemy engine
    engine.dispose()

    return shortest_path_with_poi, poi_point

