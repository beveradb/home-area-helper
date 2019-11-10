#!/usr/bin/env python3
import itertools
import logging

import fiona
from shapely.geometry import MultiPolygon, shape, Polygon
from shapely.ops import transform

from run_server import static_cache, transient_cache
from src.multi_polygons import filter_multipoly_by_bounding_box
from src.utils import timeit

rank_type_properties = {
    'deprivation': {'england': 'IMDDec0', 'scotland': 'Decile'},
    'income': {'england': 'IncDec', 'scotland': 'IncRank'},
    'crime': {'england': 'CriDec', 'scotland': 'CrimeRank'},
    'health': {'england': 'HDDDec', 'scotland': 'HlthRank'},
    'education': {'england': 'EduDec', 'scotland': 'EduRank'},
    'services': {'england': 'GBDec', 'scotland': 'GAccRank'},
    'environment': {'england': 'EnvDec', 'scotland': 'HouseRank'}
}


# This file assumes all input shapefiles are already in WGS84 projection.
# If we wish to use a new source dataset, to avoid needing to do any reprojection in this code, it is much more
# efficient to reproject the source dataset first. For example, to reproject a UK shapefile to WGS84, run:
# ogr2ogr -f "ESRI Shapefile" output-wgs84.shp input-ukproj.shp -s_srs EPSG:27700 -t_srs EPSG:4326

@timeit
def get_polygon_for_least_deprived_zones_england(rank_type, min_rank_value):
    # Metadata as per https://www.arcgis.com/home/item.html?id=5e1c399d787e48c0902e5fe4fc1ccfe3
    filtered_zones_polygons = []
    with fiona.open('datasets/uk/IMD_2019_WGS.shp') as allZones:
        # logging.debug("Total IMD data zones: " + str(len(allZones)))

        for singleZone in allZones:
            if singleZone['properties'][
                rank_type_properties[rank_type]['england']
            ] >= min_rank_value:
                filtered_zones_polygons.append(shape(singleZone['geometry']))

    return MultiPolygon(filtered_zones_polygons)


@timeit
def get_polygon_for_least_deprived_zones_scotland(rank_type, min_rank_value):
    filtered_zones_polygons = []
    with fiona.open('datasets/uk/SG_SIMD_2016_WGS.shp') as allZones:
        # logging.debug("Total SIMD data zones: " + str(len(allZones)))

        for singleZone in allZones:
            # All of the other comparison properties in the Scotland dataset are
            # actually Ranks, not Deciles - the shapefile doesn't contain Decile values for all
            # the other specific values, grrrr. So, this is a manual mapping of Decile -> Rank,
            # as per the SIMD16-Rank-Decile-Mapping-00504608.xlsx dataset info spreadsheet
            if rank_type != 'deprivation':
                if min_rank_value == 2:
                    min_rank_value = 698
                if min_rank_value == 3:
                    min_rank_value = 1396
                if min_rank_value == 4:
                    min_rank_value = 2093
                if min_rank_value == 5:
                    min_rank_value = 2791
                if min_rank_value == 6:
                    min_rank_value = 3489
                if min_rank_value == 7:
                    min_rank_value = 4186
                if min_rank_value == 8:
                    min_rank_value = 4884
                if min_rank_value == 9:
                    min_rank_value = 5581
                if min_rank_value == 10:
                    min_rank_value = 6279

            if singleZone['properties'][
                rank_type_properties[rank_type]['scotland']
            ] >= min_rank_value:
                filtered_zones_polygons.append(shape(singleZone['geometry']))

    return MultiPolygon(filtered_zones_polygons)


@timeit
@static_cache.cached()
def get_polygon_for_least_deprived_zones_uk(rank_type, min_rank_value):
    # Hah, guess you aren't a Scottish Independence voter ;)
    return MultiPolygon(itertools.chain(
        get_polygon_for_least_deprived_zones_scotland(rank_type, min_rank_value),
        get_polygon_for_least_deprived_zones_england(rank_type, min_rank_value)
    ))


@timeit
@transient_cache.cached()
def reproject_multipolygon(multipoly, proj_partial):
    # proj_uk_to_wgs84 = partial(pyproj.transform, pyproj.Proj(init='epsg:27700'), pyproj.Proj(init='epsg:4326'))

    reproj_polygons_list = []
    total_polygons = len(multipoly.geoms)

    for single_polygon in multipoly:
        logging.debug("Reprojecting polygon " + str(len(reproj_polygons_list)) + " out of " + str(total_polygons))
        reproj_polygons_list.append(reproject_single_polygon(single_polygon, proj_partial))

    return MultiPolygon(reproj_polygons_list)


@timeit
@transient_cache.cached()
def reproject_single_polygon(single_polygon, proj_partial):
    return transform(proj_partial, single_polygon)


@timeit
def get_world_min_deprivation_rank_wgs84_multipoly(rank_type, min_rank_value):
    uk_multipoly_wgs84 = get_polygon_for_least_deprived_zones_uk(rank_type, min_rank_value)

    return uk_multipoly_wgs84


@timeit
@transient_cache.cached()
def get_bounded_min_rank_multipoly(input_bounds, rank_type, min_rank_value):
    min_rank_poly = get_world_min_deprivation_rank_wgs84_multipoly(rank_type, min_rank_value)

    input_multipoly_bounds = Polygon.from_bounds(*input_bounds).buffer(0.001)

    return filter_multipoly_by_bounding_box(min_rank_poly,
                                            input_multipoly_bounds)


@timeit
def intersect_multipoly_by_min_rank(input_multipoly, rank_type, min_rank_value):
    min_rank_poly = get_bounded_min_rank_multipoly(input_multipoly.bounds, rank_type, min_rank_value)

    input_multipoly = min_rank_poly.intersection(input_multipoly)

    return input_multipoly
