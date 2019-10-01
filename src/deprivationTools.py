#!/usr/bin/env python3
import matplotlib.pyplot as plt
from descartes import PolygonPatch
from shapely.geometry import Polygon, MultiPolygon, shape
from shapely.ops import unary_union, transform
from functools import partial
import pyproj
import fiona
import itertools
from src import multiPolygonTools

def getPolygonForLeastDeprivedZonesEngland(minimumDeprivationRank):
    # Metadata as per https://www.arcgis.com/home/item.html?id=5e1c399d787e48c0902e5fe4fc1ccfe3
    filteredZonesPolygons = []
    with fiona.open('datasets/IMD_2019/IMD_2019.shp') as allZones:
        # print("Total IMD data zones: " + str(len(allZones)))
        
        for singleZone in allZones:
            if singleZone['properties']['IMDDec0'] >= minimumDeprivationRank:
                filteredZonesPolygons.append(shape(singleZone['geometry']))

    return MultiPolygon(filteredZonesPolygons)

def getPolygonForLeastDeprivedZonesScotland(minimumDeprivationRank):
    filteredZonesPolygons = []
    with fiona.open('datasets/SG_SIMD_2016/SG_SIMD_2016.shp') as allZones:
        # print("Total SIMD data zones: " + str(len(allZones)))
        
        for singleZone in allZones:
            if singleZone['properties']['Decile'] >= minimumDeprivationRank:
                filteredZonesPolygons.append(shape(singleZone['geometry']))
    
    return MultiPolygon(filteredZonesPolygons)

def getPolygonForLeastDeprivedZonesUK(minimumDeprivationRank):
    # Hah, guess you aren't a Scottish Independence voter ;)
    return MultiPolygon(itertools.chain(
        getPolygonForLeastDeprivedZonesScotland(minimumDeprivationRank),
        getPolygonForLeastDeprivedZonesEngland(minimumDeprivationRank)
    ))

def getSimplifiedClippedUKDeprivationPolygon(minDeprivationScore, targetLngLat, clipDistanceMiles):
    imdFilterMultiPolygon = getPolygonForLeastDeprivedZonesUK(minDeprivationScore)
    # print("imdFilterMultiPolygons after deprivation filter: " + str(len(imdFilterMultiPolygon)))

    imdFilterMultiPolygon = multiPolygonTools.filterUKMultiPolygonByMaxDistanceMiles(imdFilterMultiPolygon, targetLngLat, clipDistanceMiles)
    # print("imdFilterMultiPolygons after distance filter: " + str(len(imdFilterMultiPolygon)))

    imdFilterMultiPolygon = multiPolygonTools.simplify(imdFilterMultiPolygon, 0.001)
    imdFilterCombinedPolygon = multiPolygonTools.convertMultiToSingleWithJoiningLines(imdFilterMultiPolygon)
    
    UKtoWGS84Project = partial(pyproj.transform, pyproj.Proj(init='epsg:27700'), pyproj.Proj(init='epsg:4326'))

    return transform(UKtoWGS84Project, imdFilterCombinedPolygon)
