import psycopg2
import networkx as nx
import geopandas as gpd
from sqlalchemy import create_engine
from shapely.geometry import Point, LineString
import pyproj

from tkinter import *
import tkintermapview

# Helper function to find the nearest node in the graph
def nearest_node(lon, lat, graph):
    distance_dict = {}
    for node in graph.nodes():
        point = Point(node)
        distance = point.distance(Point(lon, lat))
        distance_dict[node] = distance
    return min(distance_dict, key = distance_dict.get)

# Database parameters
db_host = "localhost"
db_port = "5432"
db_name = "postgres"
db_user = "postgres"
db_password = "postgres"

# Define the database URI
db_uri = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Create an SQLAlchemy engine and connect to the database
engine = create_engine(db_uri)

# Define place A and place B coordinates (in SRID 4326 - WGS84)
lonA = 19.455850
latA = 51.759283

lonB = 21.005694
latB = 52.228516


# Convert place A and place B coordinates to SRID 3857 (Web Mercator)
transformer_to_3857 = pyproj.Transformer.from_crs(4326, 3857, always_xy = True)
transformer_to_4326 = pyproj.Transformer.from_crs(3857, 4326, always_xy = True)

lonA_3857, latA_3857 = transformer_to_3857.transform(lonA, latA)
lonB_3857, latB_3857 = transformer_to_3857.transform(lonB, latB)

# Buffer distance around place A and place B to create a subset (adjust as needed)
buffer_distance = 10000  # in meters

# Create a bounding box around place A and place B in SRID 3857
bbox = (
    lonA_3857 - buffer_distance,
    latA_3857 - buffer_distance,
    lonB_3857 + buffer_distance,
    latB_3857 + buffer_distance,
)

# Load a subset of the road network as a GeoDataFrame using SQLAlchemy connection
query = f"""
    SELECT osm_id, name, highway, way
    FROM planet_osm_roads
    WHERE ST_Intersects(way, ST_MakeEnvelope(%s, %s, %s, %s, 3857));
"""

gdf = gpd.read_postgis(query, engine, geom_col='way', params=(bbox[0], bbox[1], bbox[2], bbox[3]))

# Create a graph representation of the road network
G = nx.Graph()

for idx, row in gdf.iterrows():
    geom = row['way']
    # maxspeed = row['maxspeed']
    length = geom.length
    travel_time = length / 50  # Assume default speed if maxspeed is not specified
    G.add_edge(geom.coords[0], geom.coords[-1], weight = travel_time)

# Find the nearest nodes to place A and place B within the subset
nodeA = nearest_node(lonA_3857, latA_3857, G)
nodeB = nearest_node(lonB_3857, latB_3857, G)

nodeA_4326 = transformer_to_4326.transform(lonA_3857, latA_3857)
nodeB_4326 = transformer_to_4326.transform(lonB_3857, latB_3857)

root = Tk()
root.title("Map")
root.geometry("900x700")

my_label = LabelFrame(root)
my_label.pack(pady = 20)

map_widget = tkintermapview.TkinterMapView(my_label, width = 800, height = 600, corner_radius = 0)
map_widget.pack()

map_widget.set_position(nodeA_4326[1], nodeA_4326[0])
map_widget.set_zoom(9)

# Find the shortest path
shortest_path = nx.shortest_path(G, source = nodeA, target = nodeB, weight = 'weight')

# Marking the whole road on the map
road_cords = list()
for i in range(len(shortest_path)):
    point = Point(shortest_path[i])
    point_x_coord, point_y_coord = transformer_to_4326.transform(point.x, point.y)
    road_cords.append((point_y_coord, point_x_coord))

path = map_widget.set_path(road_cords)


# Print the names of roads in the shortest path
# for i in range(len(shortest_path) - 1):
#     start_point = Point(shortest_path[i])
#     end_point = Point(shortest_path[i + 1])
#     road_segment = LineString([start_point, end_point])

#     matching_row = gdf[gdf['way'] == road_segment]
#     if not matching_row.empty:
#         name = matching_row.iloc[0]['name']
#         print(f"Road Name: {name}")

# Close the SQLAlchemy engine
engine.dispose()

# Marking start and end point on the map
start_point = Point(shortest_path[0])
end_point = Point(shortest_path[-1])

start_x_coord, start_y_coord = transformer_to_4326.transform(start_point.x, start_point.y)
end_x_coord, end_y_coord = transformer_to_4326.transform(end_point.x, end_point.y)

marker_1 = map_widget.set_marker(start_y_coord, start_x_coord)
marker_1.set_position(start_y_coord, start_x_coord)
marker_2 = map_widget.set_marker(end_y_coord, end_x_coord)
marker_2.set_position(end_y_coord, end_x_coord)

map_widget.set_position((start_y_coord + end_y_coord) / 2, (start_x_coord + end_x_coord) / 2)

root.mainloop()
