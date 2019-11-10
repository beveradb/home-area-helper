#!/usr/bin/env python3

import matplotlib.pyplot as plt

from src import mapbox
from src import travel_time
from src.imd_tools import *
from src.multi_polygons import *
from src.utils import timeit


@timeit
@transient_cache.cached()
def get_target_area_polygons(
        target_location_address: str,
        max_walking_time_mins: int,
        max_cycling_time_mins: int,
        max_bus_time_mins: int,
        max_coach_time_mins: int,
        max_train_time_mins: int,
        max_driving_time_mins: int,
        min_deprivation_rank: int,
        min_income_rank: int,
        min_crime_rank: int,
        min_health_rank: int,
        min_education_rank: int,
        min_services_rank: int,
        min_environment_rank: int,
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

    result_polygons = []
    max_radius_polygon = get_bounding_circle_for_point(target_lng_lat, max_radius_miles)
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
            result_polygons.append(transport_poly)
            transport_poly = join_multi_to_single_poly(transport_poly)

            return_object[transport['mode']] = {
                'label': transport['label'] % str(transport['max_time']),
                'polygon': transport_poly
            }

    logging.info("Total result_polygons with all transports: " + str(len(result_polygons)))

    if min_area_miles > 0:
        result_polygons = filter_multipoly_by_min_area(result_polygons, min_area_miles)

    result_polygons_length = 1 if not hasattr(result_polygons, 'geoms') else len(result_polygons.geoms)
    logging.info("Total result_polygons after transport min area filter: " + str(result_polygons_length))

    if result_polygons_length > 0:
        # combined_transport_poly = join_multi_to_single_poly(result_polygons)
        #
        # if type(combined_transport_poly) is not list and combined_transport_poly.bounds:
        #     # Buffer to remove any self-intersections
        #     combined_transport_poly = combined_transport_poly.buffer(0.00001)
        #
        #     return_object['combined_transport'] = {
        #         'label': 'Combined Transport',
        #         'polygon': combined_transport_poly
        #     }

        deprivation_filter_values = {
            'deprivation': {'label': 'Deprivation Rank', 'value': min_deprivation_rank},
            'income': {'label': 'Income Rank', 'value': min_income_rank},
            'crime': {'label': 'Crime Rank', 'value': min_crime_rank},
            'health': {'label': 'Health Rank', 'value': min_health_rank},
            'education': {'label': 'Education Rank', 'value': min_education_rank},
            'services': {'label': 'Access to Services Rank', 'value': min_services_rank},
            'environment': {'label': 'Living Environment Rank', 'value': min_environment_rank},
        }

        for filter_name, filter_obj in deprivation_filter_values.items():
            if filter_obj['value'] > 0:
                imd_multipoly = get_bounded_min_rank_multipoly(result_polygons.bounds, filter_name, filter_obj['value'])
                imd_multipoly_joined = join_multi_to_single_poly(imd_multipoly)
                return_object[filter_name] = {
                    'label': filter_obj['label'] + ' >= ' + str(filter_obj['value']),
                    'polygon': imd_multipoly_joined
                }

                result_polygons = intersect_multipoly_by_min_rank(result_polygons, filter_name, filter_obj['value'])

                result_polygons_length = 1 if not hasattr(result_polygons, 'geoms') else len(result_polygons.geoms)
                logging.info("Total result_polygons after " + filter_name + " filter: " + str(result_polygons_length))

        if result_polygons_length > 0:
            if min_area_miles > 0:
                result_polygons = filter_multipoly_by_min_area(result_polygons, min_area_miles)

            result_polygons_length = 1 if not hasattr(result_polygons, 'geoms') else len(result_polygons.geoms)
            logging.info(
                "Total result_polygons after post-intersection min area filter: " + str(result_polygons_length))

        if result_polygons_length > 0:
            result_polygons = refine_multipolygon(result_polygons,
                                                  simplify_factor,
                                                  buffer_factor)

            result_intersection = join_multi_to_single_poly(result_polygons)

    return_object['result_intersection'] = {
        'label': 'Intersection',
        'polygon': result_intersection
    }

    return return_object


@timeit
@transient_cache.cached()
def fetch_single_transport_mode_poly(target_lng_lat, mode, max_time_mins, filter_polygon=None):
    if max_time_mins > 0:
        transport_poly = fetch_transport_mode_multipoly(target_lng_lat, mode, max_time_mins, filter_polygon)

        if hasattr(transport_poly, '__len__') and len(transport_poly) > 0:
            transport_poly = join_multi_to_single_poly(transport_poly)
            return transport_poly

        if type(transport_poly) is Polygon:
            return transport_poly

    return None


@timeit
@transient_cache.cached()
def fetch_transport_mode_multipoly(target_lng_lat, mode, max_time_mins, filter_polygon=None):
    if max_time_mins > 0:
        transport_poly = travel_time.get_public_transport_isochrone_geometry(target_lng_lat, mode, max_time_mins)

        poly_len = 1
        if hasattr(transport_poly, '__len__'):
            poly_len = len(transport_poly)

        logging.debug("Total polygons in " + mode + " multipolygon: " + str(poly_len))

        if filter_polygon is not None:
            transport_poly = filter_multipoly_by_polygon(transport_poly, filter_polygon)

        return transport_poly

    return None


@timeit
@transient_cache.cached()
def get_target_areas_polygons_json(targets_params: list):
    response_object = {
        'targets_results': [],
        'result_intersection': None
    }
    intersections_to_combine = []

    for target_index, params in enumerate(targets_params):
        target_results = get_target_area_polygons(
            target_location_address=str(params['target']),
            min_deprivation_rank=int(params['deprivation']),
            min_income_rank=int(params['income']),
            min_crime_rank=int(params['crime']),
            min_health_rank=int(params['health']),
            min_education_rank=int(params['education']),
            min_services_rank=int(params['services']),
            min_environment_rank=int(params['environment']),
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

        if target_results['result_intersection']['polygon'] and \
                target_results['result_intersection']['polygon'] is not None:
            intersections_to_combine.append(target_results['result_intersection']['polygon'])

        # Convert all of the response Polygon objects to GeoJSON
        for key, value in target_results.items():
            if 'polygon' in value and type(value['polygon']) is Polygon:
                target_results[key]['polygon'] = mapping(value['polygon'])

        response_object['targets_results'].append(target_results)

    if intersections_to_combine:
        logging.debug(intersections_to_combine)
        # Add result_intersection to response object, with bounds and centroid
        joined_intersections = join_multi_to_single_poly(intersections_to_combine)

        response_object['result_intersection'] = {
            'label': 'All Targets Combined',
            'bounds': joined_intersections.bounds,
            'centroid': mapping(joined_intersections.centroid)['coordinates'],
            'polygon': mapping(joined_intersections)
        }

    return json.dumps(response_object)


@timeit
@transient_cache.cached()
def plot_target_area_polygons_mpl(intersection_results):
    for key, value in intersection_results.items():
        if 'polygon' in value:
            plt.plot(*value['polygon'].exterior.xy, label=value['label'])
        if 'coords' in value:
            plt.plot(*value['coords'], label=value['label'])
    plt.legend()
    plt.show()
