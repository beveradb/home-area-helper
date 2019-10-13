#!/usr/bin/env python3
import json
import logging

import matplotlib.pyplot as plt
from shapely.geometry import Polygon, mapping

from run_server import cache
from src import imd_tools
from src import mapbox
from src import multi_polygons
from src import travel_time
from src.utils import timeit


@timeit
@cache.cached()
def get_target_area_polygons(
        target_location_address: str,
        max_walking_time_mins: int,
        max_cycling_time_mins: int,
        max_bus_time_mins: int,
        max_coach_time_mins: int,
        max_train_time_mins: int,
        max_driving_time_mins: int,
        min_deprivation_score: int,
        min_area_miles: float,
        max_radius_miles: float,
        simplify_factor: float,
        buffer_factor: float
) -> dict:
    return_object = {}

    target_lng_lat = mapbox.get_centre_point_lng_lat_for_address(
        target_location_address
    )
    return_object['target'] = {
        'label': 'Target: ' + target_location_address,
        'coords': target_lng_lat
    }

    travel_isochrones_to_combine = []
    max_radius_polygon = multi_polygons.get_bounding_circle_for_point(target_lng_lat, max_radius_miles)
    result_intersection = max_radius_polygon

    if max_radius_polygon is not None:
        return_object['radius'] = {
            'label': str(max_radius_miles) + ' mile Radius',
            'polygon': max_radius_polygon
        }

    transport_modes = [
        {"mode": "walking", "max_time": max_walking_time_mins, "label": '%s min Walk'},
        {"mode": "cycling", "max_time": max_cycling_time_mins, "label": '%s min Cycle'},
        {"mode": "bus", "max_time": max_bus_time_mins, "label": '%s min Bus'},
        {"mode": "coach", "max_time": max_coach_time_mins, "label": '%s min Coach'},
        {"mode": "train", "max_time": max_train_time_mins, "label": '%s min Train'},
        {"mode": "driving", "max_time": max_driving_time_mins, "label": '%s min Drive'}
    ]

    for transport in transport_modes:
        transport_poly = fetch_transport_mode_multipoly(
            target_lng_lat, transport['mode'], transport['max_time'], max_radius_polygon)

        if transport_poly is not None:
            travel_isochrones_to_combine.append(transport_poly)
            transport_poly = multi_polygons.join_multi_to_single_poly(transport_poly)

            return_object[transport['mode']] = {
                'label': transport['label'] % str(transport['max_time']),
                'polygon': transport_poly
            }

    combined_transport_poly = multi_polygons.join_multi_to_single_poly(travel_isochrones_to_combine)

    if type(combined_transport_poly) is not list:
        # Buffer to remove any self-intersections
        combined_transport_poly = combined_transport_poly.buffer(0.00001)

        return_object['combined_transport'] = {
            'label': 'Combined Transport',
            'polygon': combined_transport_poly
        }

        if max_radius_polygon is not None:
            combined_transport_poly = combined_transport_poly.intersection(max_radius_polygon)

        combined_transport_box_poly = Polygon.from_bounds(*combined_transport_poly.bounds).buffer(0.001)
        return_object['combined_transport_box'] = {
            'label': 'Transport Bounding Box',
            'polygon': combined_transport_box_poly,
            'bounds': combined_transport_box_poly.bounds
        }

        if min_deprivation_score > 0:
            imd_filter_limited_polygon = imd_tools.get_simplified_clipped_uk_deprivation_polygon(
                min_deprivation_score, combined_transport_box_poly
            )

            return_object['deprivation'] = {
                'label': 'Deprivation Score > ' + str(min_deprivation_score),
                'polygon': imd_filter_limited_polygon
            }

            imd_filter_limited_polygon = imd_filter_limited_polygon.buffer(0.00001)
            result_intersection = combined_transport_poly.intersection(imd_filter_limited_polygon)

            result_intersection = multi_polygons.join_multi_to_single_poly(result_intersection)
        else:
            result_intersection = combined_transport_poly

        if simplify_factor > 0:
            return_object['pre_simplify_result'] = {
                'label': 'Result pre-simplify: ' + str(simplify_factor),
                'polygon': result_intersection
            }

            # Simplify resulting polygon somewhat as URL can't be too long or Zoopla throws HTTP 414 error
            result_intersection = result_intersection.buffer(buffer_factor)
            result_intersection = result_intersection.simplify(simplify_factor)

    return_object['result_intersection'] = {
        'label': 'Intersection',
        'polygon': result_intersection
    }

    return return_object


@timeit
@cache.cached()
def fetch_single_transport_mode_poly(target_lng_lat, mode, max_time_mins, filter_polygon=None):
    if max_time_mins > 0:
        transport_poly = fetch_transport_mode_multipoly(target_lng_lat, mode, max_time_mins, filter_polygon)

        if hasattr(transport_poly, '__len__') and len(transport_poly) > 0:
            transport_poly = multi_polygons.join_multi_to_single_poly(transport_poly)
            return transport_poly

        if type(transport_poly) is Polygon:
            return transport_poly

    return None


@timeit
def fetch_transport_mode_multipoly(target_lng_lat, mode, max_time_mins, filter_polygon=None):
    if max_time_mins > 0:
        transport_poly = travel_time.get_public_transport_isochrone_geometry(target_lng_lat, mode, max_time_mins)

        poly_len = 1
        if hasattr(transport_poly, '__len__'):
            poly_len = len(transport_poly)

        logging.debug("Total polygons in " + mode + " multipolygon: " + str(poly_len))

        if filter_polygon is not None:
            transport_poly = multi_polygons.filter_multipoly_by_polygon(transport_poly, filter_polygon)

        return transport_poly

    return None


@timeit
def get_target_areas_polygons_json(targets_params: list):
    response_object = {
        'targets_results': [],
        'result_intersection': None
    }
    intersections_to_combine = []

    for target_index, params in enumerate(targets_params):
        target_results = get_target_area_polygons(
            target_location_address=str(params['target']),
            min_deprivation_score=int(params['deprivation']),
            max_walking_time_mins=int(params['walking']),
            max_cycling_time_mins=int(params['cycling']),
            max_bus_time_mins=int(params['bus']),
            max_coach_time_mins=int(params['coach']),
            max_train_time_mins=int(params['train']),
            max_driving_time_mins=int(params['driving']),
            max_radius_miles=float(params['radius']),
            min_area_miles=float(params['minarea']),
            simplify_factor=float(params['simplify']),
            buffer_factor=float(params['buffer'])
        )

        intersections_to_combine.append(target_results['result_intersection']['polygon'])

        # Convert all of the response Polygon objects to GeoJSON
        for key, value in target_results.items():
            if 'polygon' in value and type(value['polygon']) is Polygon:
                target_results[key]['polygon'] = mapping(value['polygon'])

        response_object['targets_results'].append(target_results)

    # Add result_intersection to response object, with bounds and centroid
    joined_intersections = multi_polygons.join_multi_to_single_poly(intersections_to_combine)

    response_object['result_intersection'] = {
        'label': 'Combined Result',
        'bounds': joined_intersections.bounds,
        'centroid': mapping(joined_intersections.centroid)['coordinates'],
        'polygon': mapping(joined_intersections)
    }

    return json.dumps(response_object)


@timeit
@cache.cached()
def plot_target_area_polygons_mpl(intersection_results):
    for key, value in intersection_results.items():
        if 'polygon' in value:
            plt.plot(*value['polygon'].exterior.xy, label=value['label'])
        if 'coords' in value:
            plt.plot(*value['coords'], label=value['label'])
    plt.legend()
    plt.show()
