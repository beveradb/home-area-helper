#!/usr/bin/env python3
import json
import logging

import matplotlib.pyplot as plt
from shapely.geometry import Polygon, mapping

from src import imd_tools
from src import mapbox
from src import multi_polygons
from src import travel_time
from src.multi_polygons import union_polygons
from src.utils import timeit


@timeit
def get_target_area_polygons(
        target_location_address: str,
        max_walking_time_mins: int,
        max_cycling_time_mins: int,
        max_bus_time_mins: int,
        max_coach_time_mins: int,
        max_train_time_mins: int,
        max_driving_time_mins: int,
        min_deprivation_score: int,
        max_radius_miles: float,
        simplify_factor: float
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
    max_radius_polygon = None

    if max_radius_miles > 0:
        max_radius_polygon = multi_polygons.get_bounding_circle_for_point(target_lng_lat, max_radius_miles)

    if max_walking_time_mins > 0:
        walking_isochrone_geom = mapbox.get_isochrone_geometry(
            target_lng_lat, max_walking_time_mins, "walking"
        )

        walking_isochrone_polygon = Polygon(walking_isochrone_geom)
        travel_isochrones_to_combine.append(walking_isochrone_polygon)

        return_object['walkingIsochrone'] = {
            'label': str(max_walking_time_mins) + ' min Walk',
            'polygon': walking_isochrone_polygon
        }

    if max_cycling_time_mins > 0:
        pt_iso_geom = travel_time.get_public_transport_isochrone_geometry(
            target_lng_lat, "cycling", max_cycling_time_mins)

        pt_iso_geom = multi_polygons.convert_multi_to_single_with_joining_lines(
            pt_iso_geom)

        public_transport_isochrone_polygon = Polygon(pt_iso_geom)
        travel_isochrones_to_combine.append(public_transport_isochrone_polygon)

        return_object['cyclingIsochrone'] = {
            'label': str(max_cycling_time_mins) + ' min Cycling',
            'polygon': public_transport_isochrone_polygon
        }

    if max_bus_time_mins > 0:
        pt_iso_geom = travel_time.get_public_transport_isochrone_geometry(
            target_lng_lat, "bus", max_bus_time_mins)

        pt_iso_geom = multi_polygons.convert_multi_to_single_with_joining_lines(
            pt_iso_geom)

        public_transport_isochrone_polygon = Polygon(pt_iso_geom)
        travel_isochrones_to_combine.append(public_transport_isochrone_polygon)

        return_object['busIsochrone'] = {
            'label': str(max_bus_time_mins) + ' min Bus',
            'polygon': public_transport_isochrone_polygon
        }

    if max_coach_time_mins > 0:
        pt_iso_geom = travel_time.get_public_transport_isochrone_geometry(
            target_lng_lat, "coach", max_coach_time_mins)

        pt_iso_geom = multi_polygons.convert_multi_to_single_with_joining_lines(
            pt_iso_geom)

        public_transport_isochrone_polygon = Polygon(pt_iso_geom)
        travel_isochrones_to_combine.append(public_transport_isochrone_polygon)

        return_object['coachIsochrone'] = {
            'label': str(max_coach_time_mins) + ' min Coach',
            'polygon': public_transport_isochrone_polygon
        }

    if max_train_time_mins > 0:
        pt_iso_geom = travel_time.get_public_transport_isochrone_geometry(
            target_lng_lat, "train", max_train_time_mins)

        if hasattr(pt_iso_geom, 'geoms'):
            logging.debug("Total polygons in train multipolygon: " + str(len(pt_iso_geom)))

        if max_radius_polygon is not None:
            filtered_multipolygon = []
            for single_polygon in pt_iso_geom:
                single_polygon = Polygon(single_polygon)
                if max_radius_polygon.contains(single_polygon.representative_point()):
                    filtered_multipolygon.append(single_polygon)
            pt_iso_geom = union_polygons(filtered_multipolygon)

            if hasattr(pt_iso_geom, 'geoms'):
                logging.debug("Total polygons in train multipolygon after radius filter: " + str(len(pt_iso_geom)))

        pt_iso_geom = multi_polygons.convert_multi_to_single_with_joining_lines(pt_iso_geom)

        public_transport_isochrone_polygon = Polygon(pt_iso_geom)
        travel_isochrones_to_combine.append(public_transport_isochrone_polygon)

        return_object['trainIsochrone'] = {
            'label': str(max_train_time_mins) + ' min Train',
            'polygon': public_transport_isochrone_polygon
        }

    if max_driving_time_mins > 0:
        driving_isochrone_geom = travel_time.get_public_transport_isochrone_geometry(
            target_lng_lat, "driving", max_driving_time_mins)

        driving_isochrone_geom = multi_polygons.convert_multi_to_single_with_joining_lines(
            driving_isochrone_geom)

        driving_isochrone_polygon = Polygon(driving_isochrone_geom)
        travel_isochrones_to_combine.append(driving_isochrone_polygon)

        return_object['drivingIsochrone'] = {
            'label': str(max_driving_time_mins) + ' min Drive',
            'polygon': driving_isochrone_polygon
        }

    combined_iso_poly = multi_polygons.convert_multi_to_single_with_joining_lines(
        travel_isochrones_to_combine
    )

    return_object['combinedTransportIsochrone'] = {
        'label': 'Combined Transport',
        'polygon': combined_iso_poly
    }

    if max_radius_polygon is not None:
        combined_iso_poly = combined_iso_poly.intersection(max_radius_polygon)

        return_object['radiusIsochrone'] = {
            'label': str(max_radius_miles) + ' mile Radius',
            'polygon': max_radius_polygon
        }

    target_bounding_box_poly = Polygon.from_bounds(*combined_iso_poly.bounds).buffer(0.001)
    return_object['targetBoundingBox'] = {
        'label': 'Bounding Box',
        'polygon': target_bounding_box_poly,
        'bounds': target_bounding_box_poly.bounds
    }

    combined_intersection_polygon = combined_iso_poly

    if min_deprivation_score > 0:
        imd_filter_limited_polygon = imd_tools.get_simplified_clipped_uk_deprivation_polygon(
            min_deprivation_score, target_bounding_box_poly
        )

        return_object['imdFilterLimited'] = {
            'label': 'Deprivation Score > ' + str(min_deprivation_score),
            'polygon': imd_filter_limited_polygon
        }

        combined_iso_poly = combined_iso_poly.buffer(0.00001)
        imd_filter_limited_polygon = imd_filter_limited_polygon.buffer(0.00001)
        combined_intersection_polygon = combined_iso_poly.intersection(imd_filter_limited_polygon)

        combined_intersection_polygon = multi_polygons.convert_multi_to_single_with_joining_lines(
            combined_intersection_polygon)

    if simplify_factor > 0:
        return_object['preSimplify'] = {
            'label': 'Result pre-simplify: ' + str(simplify_factor),
            'polygon': combined_intersection_polygon
        }

        # Simplify resulting polygon somewhat as URL can't be too long or Zoopla throws HTTP 414 error
        combined_intersection_polygon = combined_intersection_polygon.simplify(simplify_factor)

    return_object['combinedIntersection'] = {
        'label': 'Combined Result',
        'polygon': combined_intersection_polygon
    }

    return return_object


@timeit
def get_target_area_polygons_json(params: dict):
    polygon_results = get_target_area_polygons(
        target_location_address=str(params['target']),
        min_deprivation_score=int(params['deprivation']),
        max_walking_time_mins=int(params['walking']),
        max_cycling_time_mins=int(params['cycling']),
        max_bus_time_mins=int(params['bus']),
        max_coach_time_mins=int(params['coach']),
        max_train_time_mins=int(params['train']),
        max_driving_time_mins=int(params['driving']),
        max_radius_miles=float(params['radius']),
        simplify_factor=float(params['simplify'])
    )

    # Convert all of the response Polygon objects to GeoJSON
    for key, value in polygon_results.items():
        if 'polygon' in value:
            polygon_results[key]['polygon'] = mapping(value['polygon'])

    return json.dumps(polygon_results)


@timeit
def plot_target_area_polygons_mpl(intersection_results):
    for key, value in intersection_results.items():
        if 'polygon' in value:
            plt.plot(*value['polygon'].exterior.xy, label=value['label'])
        if 'coords' in value:
            plt.plot(*value['coords'], label=value['label'])
    plt.legend()
    plt.show()
