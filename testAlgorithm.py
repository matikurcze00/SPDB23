import psycopg2
import networkx as nx
import geopandas as gpd
from sqlalchemy import create_engine
from shapely.geometry import Point, LineString
import pyproj

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

# Create an SQLAlchemy engine and connect to the database
engine = create_engine(db_uri)

# Define place A and place B coordinates (in SRID 4326 - WGS84)
lonA = 20.85950
latA = 52.19354
lonB = 20.80745
latB = 52.18021

# Convert place A and place B coordinates to SRID 3857 (Web Mercator)
transformer = pyproj.Transformer.from_crs(4326, 3857, always_xy=True)

lonA_3857, latA_3857 = transformer.transform(lonA, latA)
lonB_3857, latB_3857 = transformer.transform(lonB, latB)

# Buffer distance around place A and place B to create a subset (adjust as needed)
buffer_distance = 100  # in meters

# Create a bounding box around place A and place B in SRID 3857
bbox = (
    lonA_3857 + buffer_distance,
    latA_3857 + buffer_distance,
    lonB_3857 - buffer_distance,
    latB_3857 - buffer_distance,
)

# Load a subset of the road network as a GeoDataFrame using SQLAlchemy connection
query = f"""
    SELECT osm_id, name, highway, maxspeed, way
    FROM planet_osm_roads
    WHERE ST_Intersects(way, ST_MakeEnvelope(%s, %s, %s, %s, 3857));
"""

gdf = gpd.read_postgis(query, engine, geom_col='way', params=(bbox[0], bbox[1], bbox[2], bbox[3]))

# Create a graph representation of the road network
G = nx.Graph()

for idx, row in gdf.iterrows():
    geom = row['way']
    maxspeed = row['maxspeed']
    length = geom.length
    travel_time = length / (maxspeed if maxspeed else 50)  # Assume default speed if maxspeed is not specified
    G.add_edge(geom.coords[0], geom.coords[-1], weight=travel_time)

# Find the nearest nodes to place A and place B within the subset
nodeA = nearest_node(lonA_3857, latA_3857, G)
nodeB = nearest_node(lonB_3857, latB_3857, G)

# Find the shortest path
shortest_path = nx.shortest_path(G, source=nodeA, target=nodeB, weight='weight')

# Print the names of roads in the shortest path
for i in range(len(shortest_path) - 1):
    start_point = Point(shortest_path[i])
    end_point = Point(shortest_path[i + 1])
    road_segment = LineString([start_point, end_point])

    matching_row = gdf[gdf['way'] == road_segment]
    if not matching_row.empty:
        name = matching_row.iloc[0]['name']
        print(f"Road Name: {name}")

# Close the SQLAlchemy engine
engine.dispose()

