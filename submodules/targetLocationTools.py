#!/usr/bin/env python3
from shapely.geometry import Polygon

from submodules import deprivationTools
from submodules import mapboxTools
from submodules import multiPolygonTools
from submodules import travelTimeTools


def getTargetLocationPolygons(
        targetLocationAddress: str,
        searchRadiusLimitMiles: int,
        maxWalkingTimeMins: int,
        maxPublicTransportTravelTimeMins: int,
        minDeprivationScore: int
) -> dict:
    returnObject = {}

    targetLngLat = mapboxTools.getCentrePointLngLatForAddress(
        targetLocationAddress
    )
    returnObject['targetLngLat'] = targetLngLat

    targetBoundingBox = multiPolygonTools.getBoundingCircleForPoint(
        targetLngLat, searchRadiusLimitMiles
    )

    returnObject['targetBoundingBox'] = {
        'label': str(searchRadiusLimitMiles) + ' mile Search Radius',
        'polygon': targetBoundingBox
    }

    travelIsochronesToCombine = []

    combinedIsoPolyLabel = []

    if maxWalkingTimeMins > 0:
        walkingIsochroneGeom = mapboxTools.getWalkingIsochroneGeometry(
            targetLngLat, maxWalkingTimeMins
        )

        walkingIsochronePolygon = Polygon(walkingIsochroneGeom)
        travelIsochronesToCombine.append(walkingIsochronePolygon)
        combinedIsoPolyLabel.append(str(maxWalkingTimeMins) + 'min Walk')

    if maxPublicTransportTravelTimeMins > 0:
        ptIsoGeom = travelTimeTools.getPublicTransportIsochroneGeometry(
            targetLngLat, maxPublicTransportTravelTimeMins)

        ptIsoGeom = multiPolygonTools.convertMultiToSingleWithJoiningLines(
            ptIsoGeom)

        publicTransportIsochronePolygon = Polygon(ptIsoGeom)
        travelIsochronesToCombine.append(publicTransportIsochronePolygon)

        combinedIsoPolyLabel.append(
            str(maxPublicTransportTravelTimeMins) + 'min Public Transport')

    combinedIsoPoly = travelIsochronesToCombine[0]

    if len(travelIsochronesToCombine) > 1:
        combinedIsoPoly = multiPolygonTools.convertMultiToSingleWithJoiningLines(
            [travelIsochronesToCombine[0], travelIsochronesToCombine[1]])

    returnObject['combinedTransportIsochrone'] = {
        'label': ' / '.join(combinedIsoPolyLabel),
        'polygon': combinedIsoPoly
    }

    imdFilterLimitedPolygon = deprivationTools.getSimplifiedClippedUKDeprivationPolygon(
        minDeprivationScore, targetLngLat, searchRadiusLimitMiles)

    returnObject['imdFilterLimited'] = {
        'label': 'Deprivation Score > ' + str(minDeprivationScore),
        'polygon': imdFilterLimitedPolygon
    }

    combinedIntersectionPolygon = combinedIsoPoly.intersection(imdFilterLimitedPolygon)

    combinedIntersectionPolygon = multiPolygonTools.convertMultiToSingleWithJoiningLines(
        combinedIntersectionPolygon)

    # Simplify resulting polygon somewhat as URL can't be too long or Zoopla throws HTTP 414 error
    combinedIntersectionPolygon = combinedIntersectionPolygon.simplify(0.0005)

    returnObject['combinedIntersection'] = {
        'label': 'Combined Intersection',
        'polygon': combinedIntersectionPolygon
    }

    return returnObject
