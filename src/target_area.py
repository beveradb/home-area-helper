#!/usr/bin/env python3
from shapely.geometry import Polygon
import matplotlib.pyplot as plt

from src import deprivation
from src import mapbox
from src import multi_polygons
from src import travel_time


def get_target_location_polygons(
        target_location_address: str,
        search_radius_limit_miles: int,
        max_walking_time_mins: int,
        max_public_transport_travel_time_mins: int,
        min_deprivation_score: int
) -> dict:
    return_object = {}

    target_lng_lat = mapbox.get_centre_point_lng_lat_for_address(
        target_location_address
    )
    return_object['target'] = {
        'label': 'Target: ' + target_location_address,
        'coords': target_lng_lat
    }

    target_bounding_box = multi_polygons.get_bounding_circle_for_point(
        target_lng_lat, search_radius_limit_miles
    )

    return_object['targetBoundingBox'] = {
        'label': str(search_radius_limit_miles) + ' mile Search Radius',
        'polygon': target_bounding_box
    }

    travel_isochrones_to_combine = []

    combined_iso_poly_label = []

    if max_walking_time_mins > 0:
        walking_isochrone_geom = mapbox.get_walking_isochrone_geometry(
            target_lng_lat, max_walking_time_mins
        )

        walking_isochrone_polygon = Polygon(walking_isochrone_geom)
        travel_isochrones_to_combine.append(walking_isochrone_polygon)
        combined_iso_poly_label.append(str(max_walking_time_mins) + 'min Walk')

    if max_public_transport_travel_time_mins > 0:
        pt_iso_geom = travel_time.get_public_transport_isochrone_geometry(
            target_lng_lat, max_public_transport_travel_time_mins)

        pt_iso_geom = multi_polygons.convert_multi_to_single_with_joining_lines(
            pt_iso_geom)

        public_transport_isochrone_polygon = Polygon(pt_iso_geom)
        travel_isochrones_to_combine.append(public_transport_isochrone_polygon)

        combined_iso_poly_label.append(
            str(max_public_transport_travel_time_mins) + 'min Public Transport')

    combined_iso_poly = travel_isochrones_to_combine[0]

    if len(travel_isochrones_to_combine) > 1:
        combined_iso_poly = multi_polygons.convert_multi_to_single_with_joining_lines(
            [travel_isochrones_to_combine[0], travel_isochrones_to_combine[1]])

    return_object['combinedTransportIsochrone'] = {
        'label': ' / '.join(combined_iso_poly_label),
        'polygon': combined_iso_poly
    }

    imd_filter_limited_polygon = deprivation.get_simplified_clipped_uk_deprivation_polygon(
        min_deprivation_score, target_lng_lat, search_radius_limit_miles)

    return_object['imdFilterLimited'] = {
        'label': 'Deprivation Score > ' + str(min_deprivation_score),
        'polygon': imd_filter_limited_polygon
    }

    combined_intersection_polygon = combined_iso_poly.intersection(imd_filter_limited_polygon)

    combined_intersection_polygon = multi_polygons.convert_multi_to_single_with_joining_lines(
        combined_intersection_polygon)

    # Simplify resulting polygon somewhat as URL can't be too long or Zoopla throws HTTP 414 error
    combined_intersection_polygon = combined_intersection_polygon.simplify(0.0005)

    return_object['combinedIntersection'] = {
        'label': 'Combined Intersection',
        'polygon': combined_intersection_polygon
    }

    return return_object


def plot_target_area_polygons_mpl(intersection_results):
    for key, value in intersection_results.items():
        if 'polygon' in value:
            plt.plot(*value['polygon'].exterior.xy, label=value['label'])
        if 'coords' in value:
            plt.plot(*value['coords'], label=value['label'])
    plt.legend()
    plt.show()
