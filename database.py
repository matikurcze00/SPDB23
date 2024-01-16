# Database parameters
db_host = "localhost"
db_port = "5432"
db_name = "postgres"
db_user = "postgres"
db_password = "postgres"

# Define the database URI
db_uri = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

graph_query = """
        SELECT osm_id, name, highway, maxspeed, way
        FROM planet_osm_line
        WHERE ST_Intersects(way, ST_MakeEnvelope(%s, %s, %s, %s, 3857))
        AND highway IN ('bridleway', 'motorway', 'motorway_link', 'primary', 'primary_link', 'road', 'secondary', 'secondary_link', 'tertiary', 'tertiary_link', 'trunk', 'trunk_link') ;
    """

poi_query = """WITH bbox AS (
        SELECT ST_Expand(ST_SetSRID(ST_MakePoint(%s, %s), 3857), 30000) AS search_area
    )
    SELECT osm_id, name,  amenity, ST_Distance(way, ST_SetSRID(st_makepoint(%s, %s),3857)), way 
    FROM public.planet_osm_point x CROSS JOIN bbox
    WHERE
        amenity IN %s AND ST_Within(way, bbox.search_area)
    order by ST_Distance(way, ST_SetSRID(st_makepoint(%s, %s),3857))
    limit 10;"""