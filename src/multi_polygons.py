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

    wgs84_to_uk_project = partial(pyproj.transform, pyproj.Proj(init='epsg:4326'), pyproj.Proj(init='epsg:27700'))

    target_bounding_circle = get_bounding_circle_for_point(target_lng_lat, max_distance_limit_miles)
    target_bounding_circle_uk_project = shapely.ops.transform(wgs84_to_uk_project, target_bounding_circle)

    filtered_multipolygon = []
    for singlePolygon in multi_polygon_to_filter:
        if target_bounding_circle_uk_project.contains(singlePolygon.centroid):
            filtered_multipolygon.append(singlePolygon)

    return filtered_multipolygon


def filter_uk_multipoly_by_bounding_box(multi_polygon_to_filter, wgs84_bounding_polygon):
    multi_polygon_to_filter = convert_list_to_multi_polygon(multi_polygon_to_filter)

    wgs84_to_uk_project = partial(pyproj.transform, pyproj.Proj(init='epsg:4326'), pyproj.Proj(init='epsg:27700'))
    uk_bounds_polygon = shapely.ops.transform(wgs84_to_uk_project, wgs84_bounding_polygon)

    filtered_multipolygon = []
    for singlePolygon in multi_polygon_to_filter:
        if uk_bounds_polygon.contains(singlePolygon.centroid):
            filtered_multipolygon.append(singlePolygon)

    return filtered_multipolygon


def simplify_multi(multi_polygon_to_simplify, simplification_factor):
    multi_polygon_to_simplify = convert_list_to_multi_polygon(multi_polygon_to_simplify)

    if multi_polygon_to_simplify is Polygon:
        return multi_polygon_to_simplify.simplify(simplification_factor)

    try:
        simplified_multipolygon = []
        for singlePolygon in multi_polygon_to_simplify:
            simplified_single_polygon = singlePolygon.simplify(simplification_factor)
            simplified_multipolygon.append(simplified_single_polygon)
        return simplified_multipolygon
    except TypeError as te:
        # Unsure why we're still getting here occasionally despite if statement above, but meh
        pass

    return multi_polygon_to_simplify


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
    # If the object passed in isn't a list, assume it's already a MultiPolygon and do nothing for easier recursion
    if type(multi_polygon_list) == list and len(multi_polygon_list) > 0:
        # For each polygon in the list, ensure it is actually a Polygon object and buffer to remove self-intersections
        refined_polygons_list = []
        for single_polygon in multi_polygon_list:
            if type(single_polygon) is not Polygon:
                single_polygon = Polygon(single_polygon)
            refined_polygons_list.append(single_polygon.buffer(0.0000001))

        # Once we have a buffered list of Polygons, combine into a single Polygon or MultiPolygon if there are gaps
        multi_polygon_list = shapely.ops.unary_union(refined_polygons_list)

    return multi_polygon_list
