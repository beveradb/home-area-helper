#!/usr/bin/env python3
import itertools
import logging

import fiona
from shapely.geometry import MultiPolygon, shape, Polygon
from shapely.ops import transform

from run_server import datacache
from src.multi_polygons import filter_multipoly_by_bounding_box
from src.utils import timeit


# This file assumes all input shapefiles are already in WGS84 projection.
# If we wish to use a new source dataset, to avoid needing to do any reprojection in this code, it is much more
# efficient to reproject the source dataset first. For example, to reproject a UK shapefile to WGS84, run:
# ogr2ogr -f "ESRI Shapefile" output-wgs84.shp input-ukproj.shp -s_srs EPSG:27700 -t_srs EPSG:4326

@timeit
@datacache.cached()
def get_polygon_for_least_deprived_zones_england(minimum_deprivation_rank):
    # Metadata as per https://www.arcgis.com/home/item.html?id=5e1c399d787e48c0902e5fe4fc1ccfe3
    filtered_zones_polygons = []
    with fiona.open('datasets/uk/IMD_2019/IMD_2019_WGS.shp') as allZones:
        # logging.debug("Total IMD data zones: " + str(len(allZones)))

        for singleZone in allZones:
            if singleZone['properties']['IMDDec0'] >= minimum_deprivation_rank:
                filtered_zones_polygons.append(shape(singleZone['geometry']))

    return MultiPolygon(filtered_zones_polygons)


@timeit
@datacache.cached()
def get_polygon_for_least_deprived_zones_scotland(minimum_deprivation_rank):
    filtered_zones_polygons = []
    with fiona.open('datasets/uk/SG_SIMD_2016/SG_SIMD_2016_WGS.shp') as allZones:
        # logging.debug("Total SIMD data zones: " + str(len(allZones)))

        for singleZone in allZones:
            if singleZone['properties']['Decile'] >= minimum_deprivation_rank:
                filtered_zones_polygons.append(shape(singleZone['geometry']))

    return MultiPolygon(filtered_zones_polygons)


@timeit
@datacache.cached()
def get_polygon_for_least_deprived_zones_uk(minimum_deprivation_rank):
    # Hah, guess you aren't a Scottish Independence voter ;)
    return MultiPolygon(itertools.chain(
        get_polygon_for_least_deprived_zones_scotland(minimum_deprivation_rank),
        get_polygon_for_least_deprived_zones_england(minimum_deprivation_rank)
    ))


@timeit
@datacache.cached()
def reproject_multipolygon(multipoly, proj_partial):
    # proj_uk_to_wgs84 = partial(pyproj.transform, pyproj.Proj(init='epsg:27700'), pyproj.Proj(init='epsg:4326'))

    reproj_polygons_list = []
    total_polygons = len(multipoly.geoms)

    for single_polygon in multipoly:
        logging.debug("Reprojecting polygon " + str(len(reproj_polygons_list)) + " out of " + str(total_polygons))
        reproj_polygons_list.append(reproject_single_polygon(single_polygon, proj_partial))

    return MultiPolygon(reproj_polygons_list)


@timeit
@datacache.cached()
def reproject_single_polygon(single_polygon, proj_partial):
    return transform(proj_partial, single_polygon)


@timeit
@datacache.cached()
def get_world_min_deprivation_rank_wgs84_multipoly(minimum_deprivation_rank):
    uk_multipoly_wgs84 = get_polygon_for_least_deprived_zones_uk(minimum_deprivation_rank)

    return uk_multipoly_wgs84


@timeit
@datacache.cached()
def get_bounded_min_rank_multipoly(input_bounds, min_deprivation_rank):
    min_rank_poly = get_world_min_deprivation_rank_wgs84_multipoly(min_deprivation_rank)

    input_multipoly_bounds = Polygon.from_bounds(*input_bounds).buffer(0.001)

    return filter_multipoly_by_bounding_box(min_rank_poly,
                                            input_multipoly_bounds)


@timeit
def intersect_multipoly_by_min_rank(input_multipoly, min_deprivation_rank):
    min_rank_poly = get_bounded_min_rank_multipoly(input_multipoly.bounds, min_deprivation_rank)

    input_multipoly = min_rank_poly.intersection(input_multipoly)

    return input_multipoly
