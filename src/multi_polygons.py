#!/usr/bin/env python3
import json
import logging
from functools import partial

import pyproj
import shapely.ops
from shapely.affinity import scale
from shapely.geometry import Point, MultiPoint, Polygon, LineString, mapping, MultiPolygon

from run_server import cache
from src.utils import timeit


@timeit
@cache.cached()
def get_bounding_square_for_point(target_lng_lat, bounding_box_radius_miles):
    if bounding_box_radius_miles == 0:
        return None

    circle = get_bounding_circle_for_point(target_lng_lat, bounding_box_radius_miles)
    return Polygon.from_bounds(*circle.bounds).simplify(0.00001)


@timeit
@cache.cached()
def get_bounding_circle_for_point(target_lng_lat, bounding_box_radius_miles):
    if bounding_box_radius_miles == 0:
        return None

    # This is an ugly and inaccurate approximation of miles->degrees to avoid implementing a proper projection
    # It's good enough for now, and much easier than proper projection
    buffer_distance_degrees = bounding_box_radius_miles / 50
    target_bounding_circle = Point(target_lng_lat).buffer(buffer_distance_degrees, 6)

    # Scale the bounding circle to make up for the UK projection issue
    target_bounding_circle = scale(target_bounding_circle, xfact=1.0, yfact=0.65)

    return target_bounding_circle


@timeit
@cache.cached()
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
@cache.cached()
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
@cache.cached()
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
@cache.cached()
def join_multi_to_single_poly(multi_polygon_to_join):
    # logging.debug("join_multi_to_single_poly called with " + str(type(multi_polygon_to_join)))

    # For convenience, allow passing in a List of Polygons, or even a List of coordinate lists; convert to MultiPolygon
    multi_polygon_to_join = convert_list_to_multi_polygon(multi_polygon_to_join)

    # Recursively join all polygons in this multipolygon with lines until it's no longer a multipolygon
    # If the object doesn't have a "geoms" property, it must already be a single Polygon object anyway
    while hasattr(multi_polygon_to_join, 'geoms') and len(multi_polygon_to_join) > 0:
        multi_polygon_to_join = join_multi_with_connecting_lines(multi_polygon_to_join)

    return multi_polygon_to_join


@timeit
@cache.cached()
def join_multi_with_connecting_lines(multi_polygon_to_join):
    # logging.debug("join_multi_with_connecting_lines called with " + str(type(multi_polygon_to_join)))

    if hasattr(multi_polygon_to_join, 'geoms'):
        previous_length = len(multi_polygon_to_join.geoms)
    else:
        previous_length = 1

    # First, try simply unioning it, as it's possible this may be a multipoly which doesn't need any more loines
    multi_polygon_to_join = union_polygons(multi_polygon_to_join)

    connecting_lines_array = []
    if hasattr(multi_polygon_to_join, 'geoms'):
        connecting_lines_array = get_connecting_lines_for_multi(multi_polygon_to_join)
        multi_polygon_to_join = union_polygons([multi_polygon_to_join, *connecting_lines_array])
        multi_polygon_to_join = union_polygons(multi_polygon_to_join)

    if hasattr(multi_polygon_to_join, 'geoms'):
        new_length = len(multi_polygon_to_join.geoms)
    else:
        new_length = 1

    logging.debug("Length of MultiPolygon before join: " + str(previous_length) + " - after: " + str(new_length))

    if new_length == previous_length:
        logging.warning("Connecting lines: ")
        for connecting_line in connecting_lines_array:
            logging.warning(json.dumps(mapping(connecting_line)))
        logging.warning("Result MultiPolygon: " + json.dumps(mapping(multi_polygon_to_join)))

        logging.warning("Joining MultiPolygon with connecting lines failed to decrease length of geoms!")

        for single_geom in multi_polygon_to_join.geoms:
            logging.warning("Geom length: " + str(single_geom.area))

    return multi_polygon_to_join


@timeit
@cache.cached()
def get_connecting_lines_for_multi(multi_polygon_to_join):
    # logging.debug("get_connecting_lines_for_multi called with " + str(type(multi_polygon_to_join)))

    logging.debug("get_connecting_lines_for_multi multi_polygon_to_join length: " + str(len(multi_polygon_to_join)))

    connecting_line_polygons = []
    rep_points_list = [polygon.representative_point() for polygon in multi_polygon_to_join]

    logging.debug("get_connecting_lines_for_multi rep_points_list length: " + str(len(rep_points_list)))
    logging.debug(rep_points_list)

    # For each polygon in this multipolygon, generate a line which connects it to the nearest /other/ polygon
    # by both of their representative points (for speed), and add that line to the above array
    for single_rep in rep_points_list:
        rep_points_list.remove(single_rep)

        single_connecting_line_polygon = get_line_connecting_single_point_to_others(single_rep, rep_points_list)
        connecting_line_polygons.append(single_connecting_line_polygon)

    logging.debug("get_connecting_lines_for_multi returning connecting_line_polygons with length: " + str(
        len(connecting_line_polygons)))

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
@cache.cached()
def get_nearest_points_between_polygon_and_others(single_polygon, other_polygons):
    this_polygon_multipoint = MultiPoint(single_polygon.exterior.coords)

    nearest_polygon = get_nearest_polygon_from_list(single_polygon, other_polygons)
    nearest_polygon_multipoint = MultiPoint(nearest_polygon.exterior.coords)

    return get_nearest_points(this_polygon_multipoint, nearest_polygon_multipoint)


@timeit
@cache.cached()
def get_nearest_polygon_from_list(single_polygon, other_polygons):
    other_centroids_multipoint = MultiPoint([o.centroid for o in other_polygons])

    # Find the nearest centroid to this one
    nearest_points = get_nearest_points(single_polygon.centroid, other_centroids_multipoint)

    # Find the right polygon in the list again based on this centroid!
    nearest_polygon = next((x for x in other_polygons if x.centroid == nearest_points[1]), None)

    return nearest_polygon


@timeit
@cache.cached()
def get_multipoint_for_all_polygons_coords(polygons_list):
    coords_list = []
    if type(polygons_list) is Polygon:
        polygons_list = [polygons_list]

    for single_polygon in polygons_list:
        coords_list.extend(single_polygon.exterior.coords)

    return MultiPoint(coords_list)


@timeit
def get_connecting_line_polygon(point_1, point_2):
    return simplify_polygon(buffer_polygon(
        LineString([point_1, point_2]),
        0.0000000001
    ), 0.0000000001)


@timeit
@cache.cached()
def convert_list_to_multi_polygon(multi_polygon_list):
    # logging.debug("convert_list_to_multi_polygon called with " + str(type(multi_polygon_list)))

    # If the object passed in isn't a list, assume it's already a MultiPolygon and do nothing, for easier recursion
    if type(multi_polygon_list) == list and len(multi_polygon_list) > 0:
        multi_polygon_list = instanciate_multipolygons(multi_polygon_list)
        logging.info("Multi list after instanciate_multipolygons length: " +
                     str(len(multi_polygon_list)))

        if type(multi_polygon_list[0]) is list:
            multi_polygon_list = [item for sublist in multi_polygon_list for item in sublist]
            logging.info("Squashed list of multis after instanciate_multipolygon into single list. New length: " +
                         str(len(multi_polygon_list)))

        refined_polygons_list = refine_polygons(multi_polygon_list)

        # Once we have a buffered list of Polygons, combine into a single Polygon or MultiPolygon if there are gaps
        multi_polygon_list = union_polygons(refined_polygons_list)

    return multi_polygon_list


@timeit
@cache.cached()
def filter_multipoly_by_polygon(multi_polygon_to_filter, filter_polygon):
    multi_polygon_to_filter = convert_list_to_multi_polygon(multi_polygon_to_filter)

    if hasattr(multi_polygon_to_filter, 'geoms'):
        logging.debug("Length of MultiPolygon before filter: " + str(len(multi_polygon_to_filter.geoms)))

        filtered_polygons_list = []
        for single_polygon in multi_polygon_to_filter:
            if filter_polygon.contains(single_polygon.representative_point()):
                filtered_polygons_list.append(single_polygon)

        multi_polygon_to_filter = union_polygons(filtered_polygons_list)

        if hasattr(multi_polygon_to_filter, 'geoms'):
            new_length = len(multi_polygon_to_filter.geoms)
        else:
            new_length = 1

        logging.debug("Length of MultiPolygon after filter: " + str(new_length))

    return multi_polygon_to_filter


@timeit
def filter_multipoly_by_min_area(multi_polygon_to_filter, min_area_miles):
    multi_polygon_to_filter = convert_list_to_multi_polygon(multi_polygon_to_filter)

    if hasattr(multi_polygon_to_filter, 'geoms'):
        logging.debug("Length of MultiPolygon before area filter: " + str(len(multi_polygon_to_filter.geoms)))

        filtered_polygons_list = []
        for single_polygon in multi_polygon_to_filter:
            if single_polygon.area > min_area_miles:
                logging.debug("Keeping large enough single_polygon.area = " + str("{0:.6f}".format(single_polygon.area)))
                filtered_polygons_list.append(single_polygon)
            else:
                logging.debug("Excluding small single_polygon.area = " + str("{0:.6f}".format(single_polygon.area)))

        multi_polygon_to_filter = union_polygons(filtered_polygons_list)

        if hasattr(multi_polygon_to_filter, 'geoms'):
            new_length = len(multi_polygon_to_filter.geoms)
        else:
            new_length = 1

        logging.debug("Length of MultiPolygon after area filter: " + str(new_length))

    return multi_polygon_to_filter


@timeit
@cache.cached()
def instanciate_multipolygons(polygons_list):
    if type(polygons_list) is not list:
        raise Exception("instanciate_multipolygons expected a list, was given a " + str(type(polygons_list)))
    if type(polygons_list[0]) is Polygon:
        logging.warning("instanciate_multipolygons given a list of Polygons already, simply returning")
        return polygons_list

    # For each polygon in the list, ensure it is actually a Polygon object and buffer to remove self-intersections
    for key, single_polygon in enumerate(polygons_list):
        if type(single_polygon) is list and \
                type(single_polygon[0]) is list and \
                type(single_polygon[0][0]) is list:
            logging.info("Found nested multi polygon list in list, calling instanciate_multipolygons recursively")
            polygons_list[key] = instanciate_multipolygons(single_polygon)
        else:
            polygons_list[key] = instanciate_polygon(single_polygon)

    return polygons_list


@timeit
@cache.cached()
def refine_polygons(polygons_list):
    if type(polygons_list) is MultiPolygon:
        logging.warning("refine_polygons was given a MultiPolygon - simply returning")
        return polygons_list
    if type(polygons_list) is Polygon:
        logging.warning("refine_polygons was given a Polygon - simply returning")
        return polygons_list
    if type(polygons_list) is not list:
        raise Exception("refine_polygons expected a list, was given a " + str(type(polygons_list)))
    if type(polygons_list[0]) is MultiPolygon:
        logging.warning("refine_polygons was given a list of MultiPolygons - simply returning")
        return polygons_list
    if type(polygons_list[0]) is not Polygon:
        raise Exception("refine_polygons expected a list of Polygons, but elem 0 was a " + str(type(polygons_list[0])))

    # For each polygon in the list, buffer to remove self-intersections and simplify slightly
    for key, single_polygon in enumerate(polygons_list):
        single_polygon = simplify_polygon(single_polygon, 0.0000001)
        single_polygon = buffer_polygon(single_polygon)
        polygons_list[key] = simplify_polygon(single_polygon, 0.0000001)
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
    # Create a Shapely / GEOS Polygon object from a list of coordinate
    if type(coords_list) is MultiPolygon:
        logging.warning("instanciate_polygon was given a MultiPolygon - simply returning")
        return coords_list
    if type(coords_list) is Polygon:
        logging.warning("instanciate_polygon was given a Polygon - simply returning")
        return coords_list
    if type(coords_list) is not list:
        raise Exception("instanciate_polygon expected a list, was given a " + str(type(coords_list)))
    if type(coords_list[0]) is Polygon:
        logging.warning("instanciate_polygon was given a list of instanciated Polygons - simply returning")
        return coords_list
    if type(coords_list[0]) is not list or type(coords_list[0][0]) is not float:
        raise Exception("instanciate_polygon was given a list in the wrong format. expected list of float tuple pairs, "
                        + "but element 0 in the list was: " + str(type(coords_list[0])) + " - " + str(coords_list[0]))

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
