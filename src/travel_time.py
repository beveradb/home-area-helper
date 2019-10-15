#!/usr/bin/env python3
import logging
import os

from backoff import on_exception, expo
from ratelimit import RateLimitException, limits

from run_server import requests_cache, transient_cache
from src.utils import timeit


@timeit
@on_exception(expo, RateLimitException, max_tries=10)  # Backoff exponentially and retry if rate limit hit
@limits(calls=8, period=60)  # TravelTime only allows 10 requests per minute, and sends nag emails when near this...
def call_traveltime_api(url, body, headers):
    response = requests_cache.post(
        url,
        json=body,
        headers=headers,
    )

    if response.from_cache:
        logging.debug('Cache HIT - this response was fetched from the local SQLite DB without a new API call')
    else:
        logging.warning('Cache MISS - this response required a new API call')

    return response


@timeit
@transient_cache.cached()
def get_public_transport_isochrone_geometry(target_lng_lat, mode, max_travel_time_mins):
    traveltime_api_url = 'http://api.traveltimeapp.com/v4/time-map'
    public_transport_isochrone_request_headers = {
        'Content-Type': 'application/json',
        "X-Application-Id": os.environ['TRAVELTIME_APP_ID'],
        "X-Api-Key": os.environ['TRAVELTIME_API_KEY'],
    }

    public_transport_isochrone_request_body = {
        "departure_searches": [
            {
                "id": str(target_lng_lat) + "-" + mode + "-" + str(max_travel_time_mins),
                "coords": {"lng": target_lng_lat[0], "lat": target_lng_lat[1]},
                "transportation": {"type": mode},
                "departure_time": "2019-09-30T08:00:00+0000",
                "travel_time": int(max_travel_time_mins) * int(60)
            }
        ],
        "arrival_searches": []
    }

    logging.debug('Making HTTP request to TravelTime API for mode: %s with mins: %1.0f' % (
        mode, int(max_travel_time_mins)
    ))

    response = call_traveltime_api(
        traveltime_api_url,
        public_transport_isochrone_request_body,
        public_transport_isochrone_request_headers,
    )
    json_response = response.json()

    if response.status_code != 200:
        logging.debug("Attempted to request with body: " + str(public_transport_isochrone_request_body))
        logging.debug("Error response from API call: " + str(json_response))
        raise Exception(str(json_response))

    public_transport_isochrone_shapes = json_response['results'][0]['shapes']

    logging.log(logging.DEBUG,
                'Received response from TravelTime API with shapes: %1.0f' % len(public_transport_isochrone_shapes))

    return normalise_travel_time_shapes(public_transport_isochrone_shapes)


@timeit
def normalise_travel_time_shapes(shapes_list):
    shapes_list_normalised = []

    for singleShape in shapes_list:
        shape_coords_array = []

        for singleShellCoord in singleShape['shell']:
            shape_coords_array.append([singleShellCoord['lng'], singleShellCoord['lat']])

        shapes_list_normalised.append(shape_coords_array)

    return shapes_list_normalised
