#!/usr/bin/env python3
import logging
import os
import time
import webbrowser

import jinja2
from backoff import on_exception, expo
from mapbox import Geocoder
from ratelimit import RateLimitException, limits
from shapely.geometry import Polygon

from run_server import requests_cache
from src.utils import timeit


@timeit
@on_exception(expo, RateLimitException, max_tries=10)  # Backoff exponentially and retry if rate limit hit
@limits(calls=300, period=60)  # Mapbox allow 300 (!) requests per minute
def call_mapbox_api(url):
    response = requests_cache.get(url)

    if response.from_cache:
        logging.log(logging.DEBUG,
                    'Cache HIT - this response was fetched from the local SQLite DB without a new API call')
    else:
        logging.debug('Cache MISS - this response required a new API call')

    return response


@timeit
def get_centre_point_lng_lat_for_address(address_string):
    geocoder = Geocoder()
    target_location_geocode = geocoder.forward(address_string)
    target_location_geocode_feature = target_location_geocode.geojson()['features'][0]
    return target_location_geocode_feature['geometry']['coordinates']


@timeit
def get_isochrone_geometry(target_lng_lat, max_travel_time_mins, travel_mode):
    isochrone_url = "https://api.mapbox.com/isochrone/v1/mapbox/" + travel_mode + "/"
    isochrone_url += str(target_lng_lat[0]) + "," + str(target_lng_lat[1])
    isochrone_url += "?contours_minutes=" + str(max_travel_time_mins)
    isochrone_url += "&access_token=" + os.environ['MAPBOX_ACCESS_TOKEN']

    logging.debug('Making HTTP request to Mapbox API for mode: %s with mins: %1.0f' % (
        travel_mode,
        int(max_travel_time_mins)
    ))

    json_response = call_mapbox_api(isochrone_url).json()

    coords = json_response['features'][0]['geometry']['coordinates']

    logging.debug('Received response from Mapbox API with coords: %1.0f' % len(coords))

    return coords


@timeit
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
        jinja2.Template(open("templates/single-polygon.html").read()).stream(
            MAPBOX_ACCESS_TOKEN=os.environ['MAPBOX_ACCESS_TOKEN'],
            MAP_CENTER_POINT_COORD="[" + str(single_poly_rep.x) + "," + str(single_poly_rep.y) + "]",
            MAP_LAYER_GEOJSON=[single_polygon_coords]
        ).dump(temp_map_plot_filename)

        webbrowser.open_new("file://" + os.getcwd() + "/" + temp_map_plot_filename)
        time.sleep(3)
        os.remove(temp_map_plot_filename)
