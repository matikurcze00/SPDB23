import psycopg2
from shapely.geometry import Point, LineString
from shapely.wkt import loads

# Database parameters
db_host = "localhost"
db_port = "5432"
db_name = "postgres"
db_user = "postgres"
db_password = "postgres"

# Connect to the database
conn = psycopg2.connect(
    host=db_host, port=db_port, dbname=db_name, user=db_user, password=db_password
)

lon = 20.85950
lat = 52.19354
point = Point(lon, lat)

max_distance = 1

query = """
    SELECT osm_id, name, highway, ST_AsText(ST_Transform(way, 4326)) as way_geometry
    FROM planet_osm_roads
    WHERE ST_DWithin(ST_Transform(ST_SetSRID(ST_MakePoint(%s, %s), 4326), 3857), way, %s)
    ORDER BY ST_Distance(
        ST_Transform(ST_SetSRID(ST_MakePoint(%s, %s), 4326), 3857), way
    ) ASC
    LIMIT 1;
"""

with conn.cursor() as cursor:
    cursor.execute(query, (lon, lat, max_distance, lon, lat))
    row = cursor.fetchone()
    if row:
        osm_id, name, highway, way_geometry_wkt = row
        way_geometry = loads(way_geometry_wkt)
        
        print(f"OSM ID: {osm_id}")
        print(f"Name: {name}")
        print(f"Highway type: {highway}")
        print(f"Coordinates of the way: {way_geometry}")
        print(f"Point: ({lon}, {lat})")

conn.close()