#!/usr/bin/env python3
import itertools
from functools import partial

import fiona
import pyproj
from shapely.geometry import MultiPolygon, shape
from shapely.ops import transform

from src import multi_polygons
from src.timeit import timeit


@timeit
def get_polygon_for_least_deprived_zones_england(minimum_deprivation_rank):
    # Metadata as per https://www.arcgis.com/home/item.html?id=5e1c399d787e48c0902e5fe4fc1ccfe3
    filtered_zones_polygons = []
    with fiona.open('datasets/IMD_2019/IMD_2019.shp') as allZones:
        # print("Total IMD data zones: " + str(len(allZones)))

        for singleZone in allZones:
            if singleZone['properties']['IMDDec0'] >= minimum_deprivation_rank:
                filtered_zones_polygons.append(shape(singleZone['geometry']))

    return MultiPolygon(filtered_zones_polygons)


@timeit
def get_polygon_for_least_deprived_zones_scotland(minimum_deprivation_rank):
    filtered_zones_polygons = []
    with fiona.open('datasets/SG_SIMD_2016/SG_SIMD_2016.shp') as allZones:
        # print("Total SIMD data zones: " + str(len(allZones)))

        for singleZone in allZones:
            if singleZone['properties']['Decile'] >= minimum_deprivation_rank:
                filtered_zones_polygons.append(shape(singleZone['geometry']))

    return MultiPolygon(filtered_zones_polygons)


@timeit
def get_polygon_for_least_deprived_zones_uk(minimum_deprivation_rank):
    # Hah, guess you aren't a Scottish Independence voter ;)
    return MultiPolygon(itertools.chain(
        get_polygon_for_least_deprived_zones_scotland(minimum_deprivation_rank),
        get_polygon_for_least_deprived_zones_england(minimum_deprivation_rank)
    ))


@timeit
def get_simplified_clipped_uk_deprivation_polygon(min_deprivation_score, bounding_poly):
    imd_filter_multi_polygon = get_polygon_for_least_deprived_zones_uk(min_deprivation_score)
    # print("imdFilterMultiPolygons after deprivation filter: " + str(len(imdFilterMultiPolygon)))

    imd_filter_multi_polygon = multi_polygons.filter_uk_multipoly_by_bounding_box(imd_filter_multi_polygon,
                                                                                  bounding_poly)
    # print("imdFilterMultiPolygons after bounds filter: " + str(len(imdFilterMultiPolygon)))

    imd_filter_multi_polygon = multi_polygons.simplify_multi(imd_filter_multi_polygon, 0.001)
    imd_filter_combined_polygon = multi_polygons.convert_multi_to_single_with_joining_lines(imd_filter_multi_polygon)

    u_kto_w_g_s84_project = partial(pyproj.transform, pyproj.Proj(init='epsg:27700'), pyproj.Proj(init='epsg:4326'))

    return transform(u_kto_w_g_s84_project, imd_filter_combined_polygon)
