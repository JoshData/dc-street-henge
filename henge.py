#!/usr/bin/python3

#Get the Census's TIGER/Line roads database for the District of Columbia and convert it into GeoJSON:
#
#	wget ftp://ftp2.census.gov/geo/tiger/TIGER2013/ROADS/tl_2013_11001_roads.zip
#	unzip tl_2013_11001_roads.zip
#	ogr2ogr -f geojson dcroads2.geojson tl_2013_11001_roads.shp

import sys, json, datetime, math

from astral import Astral

astral = Astral()

def main():
	city = astral["Washington DC"]

	# Load in the JSON data containing roads.
	road_data = json.load(sys.stdin)

	# For the next 365 days, show the best henge-road.
	for day_shift in range(366):
		date = (datetime.datetime.now() + datetime.timedelta(days=day_shift)).date()
		print(date, end="\t")

		for sunrise_sunset in ("sunrise", "sunset"):
			time, target_vector = get_solar_vector(date, city, sunrise_sunset)

			roads = []
			for feature in road_data["features"]:
				roadname = feature["properties"]["FULLNAME"]
				if roadname is None: continue
				if feature["geometry"]["type"] != "LineString": continue # There is one MultiLineString, for Moreland St NW, which we'll ignore.
				for length, location in get_road_segments(feature, target_vector):
					roads.append((length, roadname, location))

			# Get the road segment of the longest length.
			if len(roads) == 0:
				print("NONE")
				continue

			roads.sort(reverse=True)
			road = roads[0]

			print (road[1], "http://suncalc.net/#/%f,%f,14/%s/%s" % (road[2][1], road[2][0],
				date.isoformat().replace("-", "."), str(time.strftime("%H:%M"))),
				end='\n\t\t')

		print()

def get_solar_vector(date, city, sunrise_sunset):
	# Gets a vector in lng/lat coordinates pointing toward either sunrise or sunset
	# on the given date.

	# Get the azimuth.
	if sunrise_sunset == "sunrise":
		time = city.sunrise(date=date, local=True)+datetime.timedelta(minutes=40)
		azimuth = astral.solar_azimuth(time, city.latitude, city.longitude)
	elif sunrise_sunset == "sunset":
		time = city.sunset(date=date, local=True)-datetime.timedelta(minutes=30)
		azimuth = astral.solar_azimuth(time, city.latitude, city.longitude)
	else:
		raise ValueError()

	# Convert the azimuths (in clockwise degrees from north) into a vector on the lng/lat plane.
	from math import sin, cos, radians
	return (time, (sin(radians(azimuth)), cos(radians(azimuth))))

def haversine(p1, p2):
	# We'll need to compute distances. The haversine function computes the great
	# circle distance between two points (given in decimal degree lat/long). The
	# return value is in kilometers.
	# http://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points
    from math import radians, cos, sin, asin, sqrt
    lon1, lat1, lon2, lat2 = map(radians, [p1[0], p1[1], p2[0], p2[1]]) # deg => rad
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    km = 6367 * c # 6367 km is the radius of the Earth
    return km 

# And we'll need to get the cosine of the angle between two vectors.
def vector_dot(v1, v2):
	return (v1[0]*v2[0] + v1[1]*v2[1])
def vector_cosine(v1, v2):
	from math import sqrt
	return vector_dot(v1, v2) / sqrt( vector_dot(v1,v1) * vector_dot(v2,v2) )

def middle(x):
	return x[int(len(x)/2)]

def get_road_segments(feature, target_vector):
	# Each road is made up of a number of line segments. It may not be straight.
	# Return tuples of (length, location) for segments of this road that are
	# pointed toward the target vector.

	segments = []

	pt0 = None
	for pt1 in feature["geometry"]["coordinates"]:
		if pt0 is None:
			pt0 = pt1
			if len(segments) == 0 or segments[-1] != 0.0:
				# reset
				segments.append([0.0,[]])
			continue

		# Restrict to 2 km around Columbia Heights metro.
		if haversine(pt1, (-77.0326,38.9288)) > 2:
			# reset
			pt0 = None
			continue

		# Get the length of this segment.
		seg_length = haversine(pt0, pt1)

		# Instead of getting the angle of the segment and subtracting it from
		# the solar azimuth, we'll go directly to computing the cosine of the
		# angle between the azimuth and the road. Roads pointing exactly toward
		# or away from the azimuth will have cosines of +1 and -1. Whether it's
		# toward or away is meaningless, so take the absolute value.
		v = (pt1[0]-pt0[0], pt1[1]-pt0[1])
		seg_angle = abs(vector_cosine(v, target_vector))

		# We want segments very close to +1.
		if seg_angle > .9999:
			segments[-1][0] += seg_length
			segments[-1][1].append(pt1)
		elif segments[-1] != 0.0:
			# reset
			segments.append([0.0,[]])

		pt0 = pt1

	# Return non-zero-length segments, and the middle point in the segment. 
	segments = [
		(x[0], middle(x[1]))
		for x in segments if x[0] > .05]
	return segments


main()
