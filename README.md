Get the Census's TIGER/Line roads database for the District of Columbia and convert it into GeoJSON:

	wget ftp://ftp2.census.gov/geo/tiger/TIGER2013/ROADS/tl_2013_11001_roads.zip
	unzip tl_2013_11001_roads.zip
	ogr2ogr -f geojson dcroads2.geojson tl_2013_11001_roads.shp

You could also get road data from the DC Data Catalog, but [their roads database](http://data.dc.gov/Main_DataCatalog.aspx?id=85) doesn't seem to have labels to distinguish which roads are which, the file is considerably larger, and the coordinates come in Maryland State Plane coordinates and need to be converted to latitude/longutide... like so:

	wget -O RoadPly.ZIP http://dcatlas.dcgis.dc.gov/catalog/download.asp?downloadID=82&downloadTYPE=ESRI
	unzip RoadPly.ZIP
	ogr2ogr -f geojson -t_srs EPSG:4326 dcroads.geojson RoadPly.shp


	pip3 install astral