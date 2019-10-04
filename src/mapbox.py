#!/usr/bin/env python3
import json
import os
import time
import urllib.request
import webbrowser

import jinja2
from mapbox import Geocoder
from shapely.geometry import Polygon


def get_centre_point_lng_lat_for_address(address_string):
    geocoder = Geocoder()
    target_location_geocode = geocoder.forward(address_string)
    target_location_geocode_feature = target_location_geocode.geojson()['features'][0]
    return target_location_geocode_feature['geometry']['coordinates']


def get_walking_isochrone_geometry(target_lng_lat, max_walking_time_mins):
    walking_isochrone_url = "https://api.mapbox.com/isochrone/v1/mapbox/walking/"
    walking_isochrone_url += str(target_lng_lat[0]) + "," + str(target_lng_lat[1])
    walking_isochrone_url += "?contours_minutes=" + str(max_walking_time_mins)
    walking_isochrone_url += "&access_token=" + os.environ['MAPBOX_ACCESS_TOKEN']

    walking_isochrone_response_object = json.load(
        urllib.request.urlopen(walking_isochrone_url)
    )

    return walking_isochrone_response_object['features'][0]['geometry']['coordinates']


def view_polygon_in_browser(single_polygon):
    if type(single_polygon) is not Polygon:
        single_polygon = Polygon(single_polygon)

    single_polygon_exterior = single_polygon.exterior

    if hasattr(single_polygon_exterior, 'coords'):
        # Debug polygon object by plotting on Leaflet map in web browser by rendering to an HTML file
        single_polygon_coords = []
        for coord in list(zip(*single_polygon_exterior.coords.xy)):
            single_polygon_coords.append([coord[0], coord[1]])

        single_poly_rep = single_polygon.representative_point()

        temp_map_plot_filename = "mapbox-polygon-temp.html"
        jinja2.Template(open("src/mapbox-polygon-template.html").read()).stream(
            MAPBOX_ACCESS_TOKEN=os.environ['MAPBOX_ACCESS_TOKEN'],
            MAP_CENTER_POINT_COORD="[" + str(single_poly_rep.x) + "," + str(single_poly_rep.y) + "]",
            MAP_LAYER_GEOJSON=[single_polygon_coords]
        ).dump(temp_map_plot_filename)

        webbrowser.open_new("file://" + os.getcwd() + "/" + temp_map_plot_filename)
        time.sleep(3)
        os.remove(temp_map_plot_filename)
