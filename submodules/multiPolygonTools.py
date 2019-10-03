#!/usr/bin/env python3
from shapely.geometry import Point, MultiPoint, Polygon, LineString
from shapely.ops import unary_union, nearest_points, transform
from geopy.distance import lonlat, distance
from functools import partial
import pyproj
import matplotlib.pyplot as plt

def getBoundingCircleForPoint(targetLngLat, boundingBoxRadiusMiles):
    # Yes, this is an ugly and inaccurate approximation. It's good enough for now, and much easier than proper projection
    bufferDistanceDegrees = boundingBoxRadiusMiles / 50
    targetBoundingCircle = Point(targetLngLat).buffer(bufferDistanceDegrees, 6)

    return targetBoundingCircle

def filterUKMultiPolygonByMaxDistanceMiles(multiPolygonToFilter, targetLngLat, maxDistanceLimitMiles):
    multiPolygonToFilter = convertListToMultiPolygon(multiPolygonToFilter)

    WGS84toUKProject = partial(pyproj.transform, pyproj.Proj(init='epsg:4326'), pyproj.Proj(init='epsg:27700'))
    
    targetBoundingCircle = getBoundingCircleForPoint(targetLngLat, maxDistanceLimitMiles)
    targetBoundingCircleUKProject = transform(WGS84toUKProject, targetBoundingCircle)

    filteredMultipolygon = []
    for singlePolygon in multiPolygonToFilter:
        if targetBoundingCircleUKProject.contains(singlePolygon.centroid):
            filteredMultipolygon.append(singlePolygon)

    return filteredMultipolygon

def simplify(multiPolygonToSimplify, simplificationFactor):
    multiPolygonToSimplify = convertListToMultiPolygon(multiPolygonToSimplify)

    if multiPolygonToSimplify is Polygon:
        return multiPolygonToSimplify.simplify(simplificationFactor)

    simplifiedMultipolygon = []
    for singlePolygon in multiPolygonToSimplify:
        simplifiedSinglePolygon = singlePolygon.simplify(simplificationFactor)
        simplifiedMultipolygon.append(simplifiedSinglePolygon)

    return simplifiedMultipolygon

def convertMultiToSingleWithJoiningLines(multiPolygonToJoin):
    multiPolygonToJoin = convertListToMultiPolygon(multiPolygonToJoin)

    while hasattr(multiPolygonToJoin, 'geom_type') and multiPolygonToJoin.geom_type == 'MultiPolygon':
        connectingLinePolygonsArray = []

        for currentPolygonIndex, singlePolygonToConnect in enumerate(multiPolygonToJoin):
            thisPolygonMultipoint = MultiPoint(singlePolygonToConnect.exterior.coords)

            otherPolygons = [otherSinglePolygon for index, otherSinglePolygon in enumerate(multiPolygonToJoin) if index!=currentPolygonIndex]

            otherPolygons = unary_union(otherPolygons)
            otherPolygonsCoordsList = []
            if type(otherPolygons) is Polygon: otherPolygons = [otherPolygons]
            
            for singleOtherPolygon in otherPolygons:
                otherPolygonsCoordsList.extend(singleOtherPolygon.exterior.coords)
            otherPolygonsCoordsList = MultiPoint(otherPolygonsCoordsList)

            nearestConnectingPoints = nearest_points(thisPolygonMultipoint, otherPolygonsCoordsList)

            singleConnectingLinePolygon = LineString([nearestConnectingPoints[0], nearestConnectingPoints[1]]).buffer(0.0001)

            connectingLinePolygonsArray.append(singleConnectingLinePolygon)

        connectingLinesPolygon = unary_union(connectingLinePolygonsArray)
        
        multiPolygonToJoin = unary_union([multiPolygonToJoin, connectingLinesPolygon])

    return multiPolygonToJoin

def convertListToMultiPolygon(multiPolygonList):
    if type(multiPolygonList) == list and len(multiPolygonList) > 0:
        if type(multiPolygonList[0]) is not Polygon:
            polygonsList = [Polygon(singlePolygonList) for singlePolygonList in multiPolygonList]
        else:
            polygonsList = multiPolygonList

        multiPolygonList = unary_union(polygonsList)
    
    return multiPolygonList