#!/usr/bin/env python3
import os

import googlemaps

from run_server import transient_cache
from src.utils import timeit


@timeit
@transient_cache.cached()
def get_centre_point_lng_lat_for_address(address_string):
    gmaps = googlemaps.Client(key=os.environ['GMAPS_API_KEY'])

    geocode_result = gmaps.geocode(address_string)

    return [
        geocode_result[0]['geometry']['location']['lng'],
        geocode_result[0]['geometry']['location']['lat']
    ]
