#!/usr/bin/env python3
from functools import partial

import pyproj
import shapely.ops
from shapely.affinity import scale
from shapely.geometry import Point, MultiPoint, Polygon, LineString

from src.timeit import timeit


@timeit
def get_bounding_circle_for_point(target_lng_lat, bounding_box_radius_miles):
    # This is an ugly and inaccurate approximation of miles->degrees to avoid implementing a proper projection
    # It's good enough for now, and much easier than proper projection
    buffer_distance_degrees = bounding_box_radius_miles / 50
    target_bounding_circle = Point(target_lng_lat).buffer(buffer_distance_degrees, 6)

    # Scale the bounding circle to make up for the UK projection issue
    target_bounding_circle = scale(target_bounding_circle, xfact=1.0, yfact=0.65)

    return target_bounding_circle


@timeit
def filter_uk_multipoly_by_target_radius(multi_polygon_to_filter, target_lng_lat, max_distance_limit_miles):
    # For convenience, allow passing in a List of Polygons, or even a List of coordinate lists; convert to MultiPolygon
    multi_polygon_to_filter = convert_list_to_multi_polygon(multi_polygon_to_filter)

    wgs84_to_uk_project = partial(pyproj.transform, pyproj.Proj(init='epsg:4326'), pyproj.Proj(init='epsg:27700'))

    target_bounding_circle = get_bounding_circle_for_point(target_lng_lat, max_distance_limit_miles)
    target_bounding_circle_uk_project = reproject_polygon(wgs84_to_uk_project, target_bounding_circle)

    filtered_multipolygon = []
    for singlePolygon in multi_polygon_to_filter:
        if target_bounding_circle_uk_project.contains(singlePolygon.centroid):
            filtered_multipolygon.append(singlePolygon)

    return filtered_multipolygon


@timeit
def filter_uk_multipoly_by_bounding_box(multi_polygon_to_filter, wgs84_bounding_polygon):
    # For convenience, allow passing in a List of Polygons, or even a List of coordinate lists; convert to MultiPolygon
    multi_polygon_to_filter = convert_list_to_multi_polygon(multi_polygon_to_filter)

    wgs84_to_uk_project = partial(pyproj.transform, pyproj.Proj(init='epsg:4326'), pyproj.Proj(init='epsg:27700'))
    uk_bounds_polygon = reproject_polygon(wgs84_to_uk_project, wgs84_bounding_polygon)

    filtered_multipolygon = []
    for singlePolygon in multi_polygon_to_filter:
        if uk_bounds_polygon.contains(singlePolygon.centroid):
            filtered_multipolygon.append(singlePolygon)

    return filtered_multipolygon


@timeit
def simplify_multi(multi_polygon_to_simplify, simplification_factor):
    # For convenience, allow passing in a List of Polygons, or even a List of coordinate lists; convert to MultiPolygon
    multi_polygon_to_simplify = convert_list_to_multi_polygon(multi_polygon_to_simplify)

    if multi_polygon_to_simplify is Polygon:
        return multi_polygon_to_simplify.simplify(simplification_factor)

    try:
        for key, singlePolygon in enumerate(multi_polygon_to_simplify):
            multi_polygon_to_simplify[key] = simplify_polygon(singlePolygon, simplification_factor)
        return multi_polygon_to_simplify
    except TypeError as te:
        # Unsure why we're still getting here occasionally despite if statement above, but meh
        pass

    return multi_polygon_to_simplify


@timeit
def convert_multi_to_single_with_joining_lines(multi_polygon_to_join):
    # For convenience, allow passing in a List of Polygons, or even a List of coordinate lists; convert to MultiPolygon
    multi_polygon_to_join = convert_list_to_multi_polygon(multi_polygon_to_join)

    # Recursively join all polygons in this multipolygon with lines until it's no longer a multipolygon
    while hasattr(multi_polygon_to_join, 'geom_type') and multi_polygon_to_join.geom_type == 'MultiPolygon':
        multi_polygon_to_join = join_multi_with_connecting_lines(multi_polygon_to_join)

    return multi_polygon_to_join


@timeit
def join_multi_with_connecting_lines(multi_polygon_to_join):
    connecting_lines_array = get_connecting_lines_for_multi(multi_polygon_to_join)
    return union_polygons([multi_polygon_to_join, *connecting_lines_array])


@timeit
def get_connecting_lines_for_multi(multi_polygon_to_join):
    connecting_line_polygons = []
    rep_points_list = [polygon.centroid for polygon in multi_polygon_to_join]

    # For each polygon in this multipolygon, generate a line which connects it to the nearest /other/ polygon
    # by both of their representative points (for speed), and add that line to the above array
    for single_rep in rep_points_list:
        rep_points_list.remove(single_rep)

        single_connecting_line_polygon = get_line_connecting_single_point_to_others(single_rep, rep_points_list)
        connecting_line_polygons.append(single_connecting_line_polygon)

    return connecting_line_polygons


@timeit
def get_line_connecting_single_point_to_others(single_point, other_points):
    other_points_multipoint = MultiPoint(other_points)
    nearest_points = get_nearest_points(single_point, other_points_multipoint)

    single_connecting_line_polygon = get_connecting_line_polygon(
        nearest_points[0], nearest_points[1]
    )

    return single_connecting_line_polygon


@timeit
def get_line_connecting_single_polygon_to_others(single_polygon, other_polygons):
    nearest_polygon = get_nearest_polygon_from_list(single_polygon, other_polygons)

    single_connecting_line_polygon = get_connecting_line_polygon(
        single_polygon.representative_point(), nearest_polygon.representative_point()
    )

    return single_connecting_line_polygon


@timeit
def get_nearest_points_between_polygon_and_others(single_polygon, other_polygons):
    this_polygon_multipoint = MultiPoint(single_polygon.exterior.coords)

    nearest_polygon = get_nearest_polygon_from_list(single_polygon, other_polygons)
    nearest_polygon_multipoint = MultiPoint(nearest_polygon.exterior.coords)

    return get_nearest_points(this_polygon_multipoint, nearest_polygon_multipoint)


@timeit
def get_nearest_polygon_from_list(single_polygon, other_polygons):
    other_centroids_multipoint = MultiPoint([o.centroid for o in other_polygons])

    # Find the nearest centroid to this one
    nearest_points = get_nearest_points(single_polygon.centroid, other_centroids_multipoint)

    # Find the right polygon in the list again based on this centroid!
    nearest_polygon = next((x for x in other_polygons if x.centroid == nearest_points[1]), None)

    return nearest_polygon


@timeit
def get_multipoint_for_all_polygons_coords(polygons_list):
    coords_list = []
    if type(polygons_list) is Polygon:
        polygons_list = [polygons_list]

    for single_polygon in polygons_list:
        coords_list.extend(single_polygon.exterior.coords)

    return MultiPoint(coords_list)


@timeit
def get_connecting_line_polygon(point_1, point_2):
    return buffer_polygon(
        LineString([point_1, point_2]),
        0.0001
    )


@timeit
def convert_list_to_multi_polygon(multi_polygon_list):
    # If the object passed in isn't a list, assume it's already a MultiPolygon and do nothing, for easier recursion
    if type(multi_polygon_list) == list and len(multi_polygon_list) > 0:
        refined_polygons_list = refine_polygons(multi_polygon_list)

        # Once we have a buffered list of Polygons, combine into a single Polygon or MultiPolygon if there are gaps
        multi_polygon_list = union_polygons(refined_polygons_list)

    return multi_polygon_list


@timeit
def refine_polygons(polygons_list):
    # For each polygon in the list, ensure it is actually a Polygon object and buffer to remove self-intersections
    for key, single_polygon in enumerate(polygons_list):
        if type(single_polygon) is not Polygon:
            single_polygon = instanciate_polygon(single_polygon)
        single_polygon = simplify_polygon(single_polygon, 0.0000001)
        polygons_list[key] = buffer_polygon(single_polygon)
    return polygons_list


@timeit
def buffer_polygon(single_polygon, amount=0.0000001):
    # Buffer a polygon by a little to remove self-intersections
    return single_polygon.buffer(amount)


@timeit
def simplify_polygon(single_polygon, simplification_factor):
    # Simplify a polygon by a little to reduce number of points (and thus, detail)
    return single_polygon.simplify(simplification_factor)


@timeit
def instanciate_polygon(coords_list):
    # Create a Shapely / GEOS Polygon object from a list of coordinates
    return Polygon(coords_list)


@timeit
def union_polygons(multi_polygons):
    # Combine a list of polygons into either a single polygon, or a MultiPolygon if there are gaps
    return shapely.ops.unary_union(multi_polygons)


@timeit
def get_nearest_points(object_1, object_2):
    # Combine a list of polygons into either a single polygon, or a MultiPolygon if there are gaps
    return shapely.ops.nearest_points(object_1, object_2)


@timeit
def reproject_polygon(projection_transform, single_polygon):
    # Reproject a polygon from one coordinate system to another
    return shapely.ops.transform(projection_transform, single_polygon)
