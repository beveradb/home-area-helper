#!/usr/bin/env python3
import json
import logging

from shapely.geometry import mapping

from src import google_maps
from src.multi_polygons import get_bounding_circle_for_point, join_multi_to_single_poly
from src.utils import timeit


def get_target_cities(params: dict):
    city_center_coords = google_maps.get_centre_point_lng_lat_for_address(
        str(params['countryInput'])
    )

    city_polygon = get_bounding_circle_for_point(city_center_coords, 2)

    return [
        {
            'label': str(params['countryInput']),
            'coords': city_center_coords,
            'polygon': city_polygon
        }
    ]


@timeit
def get_target_cities_data_json(params: dict):
    response_object = {
        'targets_results': [],
        'result_intersection': None
    }

    target_cities_polygons = []
    target_cities = get_target_cities(params)

    for target_city in target_cities:
        response_object['targets_results'].append({
            'target': {
                'label': target_city['label'],
                'coords': target_city['coords']
            }
        })
        target_cities_polygons.append(target_city['polygon'])

    if target_cities_polygons:
        logging.debug(target_cities_polygons)
        joined_cities = join_multi_to_single_poly(target_cities_polygons)

        response_object['results_combined'] = {
            'label': 'All Cities Combined',
            'bounds': joined_cities.bounds,
            'centroid': mapping(joined_cities.centroid)['coordinates'],
            'polygon': mapping(joined_cities)
        }

    return json.dumps(response_object)
