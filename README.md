# POI PathFinder

## Install requirements
```bash
sudo apt-get install python3-tk
pip install -r requirements.txt

# Install osm2pgsql
sudo apt-get install osm2pgsql # For Debian/Ubuntu    
```
## Connect to the postgres DB and set up PostGIS extension
```sql
CREATE EXTENSION postgis;
```

## Import data using osm2pgsql
```bash
export PGPASSWORD='your_password'
osm2pgsql -c -d your_database_name -U your_username -H your_host -S /path/to/default.style /path/to/your/data.osm.pbf
```

## Run program
```bash
python poi_pathfinder.py
```
