#!/usr/bin/env python3
from functools import partial

import pyproj
import shapely.ops
from shapely.geometry import Point, MultiPoint, Polygon, LineString


def get_bounding_circle_for_point(target_lng_lat, bounding_box_radius_miles):
    # Yes, this is an ugly and inaccurate approximation.
    # It's good enough for now, and much easier than proper projection
    buffer_distance_degrees = bounding_box_radius_miles / 50
    target_bounding_circle = Point(target_lng_lat).buffer(buffer_distance_degrees, 6)

    return target_bounding_circle


def filter_uk_multipoly_by_target_radius(multi_polygon_to_filter, target_lng_lat, max_distance_limit_miles):
    multi_polygon_to_filter = convert_list_to_multi_polygon(multi_polygon_to_filter)

    w_g_s84to_uk_project = partial(pyproj.transform, pyproj.Proj(init='epsg:4326'), pyproj.Proj(init='epsg:27700'))

    target_bounding_circle = get_bounding_circle_for_point(target_lng_lat, max_distance_limit_miles)
    target_bounding_circle_uk_project = shapely.ops.transform(w_g_s84to_uk_project, target_bounding_circle)

    filtered_multipolygon = []
    for singlePolygon in multi_polygon_to_filter:
        if target_bounding_circle_uk_project.contains(singlePolygon.centroid):
            filtered_multipolygon.append(singlePolygon)

    return filtered_multipolygon


def simplify(multi_polygon_to_simplify, simplification_factor):
    multi_polygon_to_simplify = convert_list_to_multi_polygon(multi_polygon_to_simplify)

    if multi_polygon_to_simplify is Polygon:
        return multi_polygon_to_simplify.simplify(simplification_factor)

    simplified_multipolygon = []
    for singlePolygon in multi_polygon_to_simplify:
        simplified_single_polygon = singlePolygon.simplify(simplification_factor)
        simplified_multipolygon.append(simplified_single_polygon)

    return simplified_multipolygon


def convert_multi_to_single_with_joining_lines(multi_polygon_to_join):
    multi_polygon_to_join = convert_list_to_multi_polygon(multi_polygon_to_join)

    while hasattr(multi_polygon_to_join, 'geom_type') and multi_polygon_to_join.geom_type == 'MultiPolygon':
        connecting_line_polygons_array = []

        for currentPolygonIndex, singlePolygonToConnect in enumerate(multi_polygon_to_join):
            this_polygon_multipoint = MultiPoint(singlePolygonToConnect.exterior.coords)

            other_polygons = [otherSinglePolygon for index, otherSinglePolygon in enumerate(multi_polygon_to_join) if
                              index != currentPolygonIndex]

            other_polygons = shapely.ops.unary_union(other_polygons)
            other_polygons_coords_list = []
            if type(other_polygons) is Polygon:
                other_polygons = [other_polygons]

            for singleOtherPolygon in other_polygons:
                other_polygons_coords_list.extend(singleOtherPolygon.exterior.coords)
            other_polygons_coords_list = MultiPoint(other_polygons_coords_list)

            nearest_connecting_points = shapely.ops.nearest_points(this_polygon_multipoint, other_polygons_coords_list)

            single_connecting_line_polygon = LineString(
                [nearest_connecting_points[0], nearest_connecting_points[1]]).buffer(
                0.0001)

            connecting_line_polygons_array.append(single_connecting_line_polygon)

        connecting_lines_polygon = shapely.ops.unary_union(connecting_line_polygons_array)

        multi_polygon_to_join = shapely.ops.unary_union([multi_polygon_to_join, connecting_lines_polygon])

    return multi_polygon_to_join


def convert_list_to_multi_polygon(multi_polygon_list):
    if type(multi_polygon_list) == list and len(multi_polygon_list) > 0:
        if type(multi_polygon_list[0]) is not Polygon:
            polygons_list = [Polygon(singlePolygonList) for singlePolygonList in multi_polygon_list]
        else:
            polygons_list = multi_polygon_list

        multi_polygon_list = shapely.ops.unary_union(polygons_list)

    return multi_polygon_list
