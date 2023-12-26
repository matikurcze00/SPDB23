import psycopg2
import networkx as nx
import geopandas as gpd
from sqlalchemy import create_engine
from shapely.geometry import Point, LineString
import pyproj
import matplotlib.pyplot as plt
import folium
import pandas

    # Helper function to find the nearest node in the graph
def nearest_node(lon, lat, graph):
    distance_dict = {}
    for node in graph.nodes():
        point = Point(node)
        distance = point.distance(Point(lon, lat))
        distance_dict[node] = distance
    return min(distance_dict, key=distance_dict.get)

# Database parameters
db_host = "localhost"
db_port = "5432"
db_name = "postgres"
db_user = "postgres"
db_password = "postgres"

# Define the database URI
db_uri = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

#Starting parameters
start = Point(20.85950, 52.19354)
end = Point(19.4897, 51.801)
weight = 'travel_time'
stop_parameter = 1.3
# Create an SQLAlchemy engine and connect to the database
engine = create_engine(db_uri)


# Convert place A and place B coordinates to SRID 3857 (Web Mercator)
transformer = pyproj.Transformer.from_crs(4326, 3857, always_xy=True)

start_3857 = Point(transformer.transform(start.x, start.y))
end_3857 = Point(transformer.transform(end.x, end.y))

# Buffer distance around place A and place B to create a subset (adjust as needed)
buffer_distance = 10000  # in meters

# Create a bounding box around place A and place B in SRID 3857
bbox = (
    max(start_3857.x, end_3857.x) + buffer_distance,
    max(start_3857.y, end_3857.y) + buffer_distance,
    min(start_3857.x, end_3857.x) - buffer_distance,
    min(start_3857.y, end_3857.y) - buffer_distance,
)

# Load a subset of the road network as a GeoDataFrame using SQLAlchemy connection
query_nodes = f"""
    SELECT osm_id, name, highway, maxspeed, way
    FROM planet_osm_roads
    WHERE ST_Intersects(way, ST_MakeEnvelope(%s, %s, %s, %s, 3857));
"""

gdf = gpd.read_postgis(query_nodes, engine, geom_col='way', params=(bbox[0], bbox[1], bbox[2], bbox[3]))

# Create a graph representation of the road network
G = nx.Graph()

for idx, row in gdf.iterrows():
    geom = row['way']
    maxspeed = row['maxspeed']
    length = geom.length
    travel_time = length / 1000 / (maxspeed if not pandas.isna(maxspeed) else 50)
    G.add_edge(geom.coords[0], geom.coords[-1], travel_time=travel_time, maxspeed = maxspeed, length = length)

# Find the nearest nodes to place A and place B within the subset
start_node = nearest_node(start_3857.x, start_3857.y, G)
end_node = nearest_node(end_3857.x, end_3857.y, G)

# Find the shortest path
shortest_path = nx.shortest_path(G, source=start_node, target=end_node, weight=weight)

total_travel_time = 0.0
total_travel_length = 0.0
max_speed_total = 0.0
stop_node_id = 0
# Calculate the total travel time by summing the travel times of each edge in the path
for i in range(len(shortest_path) - 1):
    node1 = shortest_path[i]
    node2 = shortest_path[i + 1]

    # Get the travel time for the edge between node1 and node2
    edge_data = G.get_edge_data(node1, node2)
    edge_travel_time = edge_data['travel_time']
    edge_travel_length = edge_data['length']
    max_speed_total += edge_data['maxspeed'] if not pandas.isna(edge_data['maxspeed'] ) else 50
    total_travel_time += edge_travel_time
    total_travel_length += edge_travel_length

temp_travel_length = 0.0
for i in range (len(shortest_path) -1):
    node1 = shortest_path[i]
    node2 = shortest_path[i + 1]

    # Get the travel time for the edge between node1 and node2
    edge_data = G.get_edge_data(node1, node2)
    edge_travel_time = edge_data['travel_time']
    temp_travel_length += edge_travel_length

    if temp_travel_length > stop_parameter * 0.9 * 3600:
        stop_node_id = i
        break

print(f"Total Travel Time: {total_travel_time} seconds")
print(f"Total Travel Lenght: {total_travel_length} meters")
print(f"average max speed = {max_speed_total/(len(shortest_path) -1)}")

path_break = Point(shortest_path[stop_node_id+1])

query_poi = """WITH bbox AS (
    SELECT ST_Expand(ST_SetSRID(ST_MakePoint(%s, %s), 3857), 100000) AS search_area
)
SELECT osm_id, name,  amenity, ST_Distance(way, ST_SetSRID(st_makepoint(%s, %s),3857)), way 
FROM public.planet_osm_point x CROSS JOIN bbox
WHERE
    amenity IN ('atm', 'bar', 'fast_food', 'food', 'fuel', 'restaurant') AND ST_Within(way, bbox.search_area)
  order by ST_Distance(way, ST_SetSRID(st_makepoint(%s, %s),3857))
  limit 1;"""


gdf = gpd.read_postgis(query_poi, engine, geom_col='way', params=(path_break.x, path_break.y, path_break.x, path_break.y, path_break.x, path_break.y))

# Create a graph representation of the road network
poi_point = Point()
for idx, row in gdf.iterrows():
    geom = row['way']
    poi_point = Point(geom.coords[0])

poi_node = nearest_node(poi_point.x, poi_point.y, G)

shortest_path2 = nx.shortest_path(G, source=shortest_path[stop_node_id+1], target=poi_node, weight=weight)
shortest_path3 = nx.shortest_path(G, source=poi_node, target=end_node, weight=weight)

shortest_path = shortest_path[0:stop_node_id+1] + shortest_path2 + shortest_path3

map_center = [(start.y + end.y) / 2, (start.x + end.x) / 2]
m = folium.Map(location=map_center, zoom_start=9)

transformer = pyproj.Transformer.from_crs(3857, 4326)
shortest_path_coords = [transformer.transform(coord[0], coord[1]) for coord in shortest_path]

# Add the shortest path as a PolyLine to the map
folium.PolyLine(locations=shortest_path_coords, color='blue', weight=5).add_to(m)

# Save the map to an HTML file or display it
m.save("shortest_path_map.html")

# Close the SQLAlchemy engine
engine.dispose()

