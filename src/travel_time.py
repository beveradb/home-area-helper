#!/usr/bin/env python3
import json
import os
import urllib.request


def get_public_transport_isochrone_geometry(target_lng_lat, max_public_transport_travel_time_mins):
    public_transport_isochrone_request_headers = {
        'Content-Type': 'application/json',
        "X-Application-Id": os.environ['TRAVELTIME_APP_ID'],
        "X-Api-Key": os.environ['TRAVELTIME_API_KEY'],
    }

    public_transport_isochrone_request_body_j_s_o_n = json.dumps({
        "departure_searches": [
            {
                "id": "first request",
                "coords": {"lng": target_lng_lat[0], "lat": target_lng_lat[1]},
                "transportation": {"type": "public_transport"},
                "departure_time": "2019-09-30T08:00:00+0000",
                "travel_time": int(max_public_transport_travel_time_mins) * int(60)
            }
        ],
        "arrival_searches": []
    })

    public_transport_isochrone_request = urllib.request.Request(
        'http://api.traveltimeapp.com/v4/time-map',
        public_transport_isochrone_request_body_j_s_o_n.encode("utf-8"),
        public_transport_isochrone_request_headers
    )

    public_transport_isochrone_response_object = json.load(
        urllib.request.urlopen(public_transport_isochrone_request)
    )

    public_transport_isochrone_shapes = public_transport_isochrone_response_object['results'][0]['shapes']

    return normalise_travel_time_shapes(public_transport_isochrone_shapes)


def normalise_travel_time_shapes(shapes_list):
    shapes_list_normalised = []

    for singleShape in shapes_list:
        shape_coords_array = []

        for singleShellCoord in singleShape['shell']:
            shape_coords_array.append([singleShellCoord['lng'], singleShellCoord['lat']])

        shapes_list_normalised.append(shape_coords_array)

    return shapes_list_normalised
