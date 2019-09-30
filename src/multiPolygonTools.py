#!/usr/bin/env python3
from shapely.geometry import Point, MultiPoint, Polygon, LineString
from shapely.ops import unary_union, nearest_points

def convertMultiToSingleWithJoiningLines(multiPolygonToJoin):
    if type(multiPolygonToJoin) == list:
        if type(multiPolygonToJoin[0]) is not Polygon:
            polygonsList = [Polygon(singlePolygonList) for singlePolygonList in multiPolygonToJoin]
        else:
            polygonsList = multiPolygonToJoin
        multiPolygonToJoin = unary_union(polygonsList)

    while multiPolygonToJoin.geom_type == 'MultiPolygon':
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
