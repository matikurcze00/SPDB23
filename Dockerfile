FROM postgres:15.1
RUN apt-get update \
	&& apt-get install -y postgis postgresql-15-postgis-3