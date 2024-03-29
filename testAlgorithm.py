import time
import psycopg2
import networkx as nx
import geopandas as gpd
from sqlalchemy import create_engine
from shapely.geometry import Point
import pyproj
import matplotlib.pyplot as plt
import folium
import pandas
from graph_builder import build_graph, find_stop_node, nearest_node, path_length, find_new_path_with_poi
from database import db_uri


#Starting parameters
# Warszawa- Łódź
start = Point(20.85950, 52.19354)
end = Point(19.4897, 51.801)
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
poi_type = ('atm' ,'fast_food', 'bar', 'food', 'fuel', 'restaurant') #'atm' ,'fast_food', 'bar', 'food', 'fuel', 'restaurant'
# Create an SQLAlchemy engine and connect to the database
# stop_values = [1, 2]
start_time = time.time()

engine = create_engine(db_uri)


# Convert place A and place B coordinates to SRID 3857 (Web Mercator)
transformer = pyproj.Transformer.from_crs(4326, 3857, always_xy=True)

start_3857 = Point(transformer.transform(start.x, start.y))
end_3857 = Point(transformer.transform(end.x, end.y))

# Buffer distance around place A and place B to create a subset (adjust as needed)
buffer_distance = 10000  # in meters

graph = build_graph(start_3857, end_3857, buffer_distance, engine)

# Find the nearest nodes to place A and place B within the subset
start_node = nearest_node(start_3857.x, start_3857.y, graph)
end_node = nearest_node(end_3857.x, end_3857.y, graph)

# Find the shortest path

end_time = time.time()
elapsed_time_graph = end_time - start_time

start_time = time.time()
shortest_path = nx.shortest_path(graph, source=start_node, target=end_node, weight=weight)

end_time = time.time()
elapsed_time1 = end_time - start_time





# for stop_value in stop_values:
start_time2 = time.time()

stop_node_id = find_stop_node(shortest_path, stop_weight, stop_value, graph, is_reversed)



#FINDING NEW SHORTEST PATH

shortest_path_with_poi = find_new_path_with_poi(shortest_path, stop_node_id, engine, graph, start_node, end_node, weight, max_extend, weight_extend, poi_type)

end_time2 = time.time()
elapsed_time2 = end_time2 - start_time2
    # Calculate the total travel time by summing the travel times of each edge in the path

# print(f"Graph was generated: {elapsed_time_graph} seconds")
print(f"Start point : {start.y, start.x}. End point: {end.y, end.x}")

print('New path')
print(f'Total time {path_length(shortest_path_with_poi, graph, "travel_time")}')
print(f'Total Length {path_length(shortest_path_with_poi, graph, "length")}')     
print(f"New Path was fined in : {elapsed_time2} seconds")

# print('Old path')
# print(f'Total time {path_length(shortest_path, graph, "travel_time")}')
# print(f'Total Length {path_length(shortest_path, graph, "length")}')
# print(f"First path was fined in : {elapsed_time1} seconds")


#
# MAP
#

map_center = [(start.y + end.y) / 2, (start.x + end.x) / 2]
m = folium.Map(location=map_center, zoom_start=9)

transformer = pyproj.Transformer.from_crs(3857, 4326)
shortest_path_coords = [transformer.transform(coord[0], coord[1]) for coord in shortest_path_with_poi]

# Add the shortest path as a PolyLine to the map
folium.PolyLine(locations=shortest_path_coords, color='blue', weight=5).add_to(m)

# Save the map to an HTML file or display it
# m.save("shortest_path_map_szcz.html")
m.save("shortest_path_map_szcz_kra.html")

shortest_path_coords = [transformer.transform(coord[0], coord[1]) for coord in shortest_path]

m = folium.Map(location=map_center, zoom_start=9)
# Add the shortest path as a PolyLine to the map
folium.PolyLine(locations=shortest_path_coords, color='blue', weight=5).add_to(m)

# Save the map to an HTML file or display it
m.save("shortest_path_map_szcz_kra_no_poi.html")
# Close the SQLAlchemy engine
engine.dispose()

