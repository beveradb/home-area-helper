#!/usr/bin/env python3
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import unary_union, transform
from functools import partial
import pyproj
from geopy.distance import lonlat, distance

from src import multiPolygonTools
from src import zooplaTools
from src import travelTimeTools
from src import mapboxTools
from src import deprivationTools

# This script requires you have environment variables set with your personal API keys:
# MAPBOX_ACCESS_TOKEN from https://docs.mapbox.com/help/how-mapbox-works/access-tokens/
# TRAVELTIME_APP_ID from https://docs.traveltimeplatform.com/overview/introduction
# TRAVELTIME_API_KEY from https://docs.traveltimeplatform.com/overview/introduction

# Parameters for where to search and what to search for!
targetLocationAddress = "WC1A 2TH, London, UK"
# targetLocationAddress = "69 Morrison Street, Edinburgh, UK"

minDeprivationScore = 6
maxWalkingTimeMins = "15"
maxPublicTransportTravelTimeMins = "20"
rental = True
sharedAccommodation = False
minPrice = ""
maxPrice = "1300"
minBeds = "1"
maxBeds = ""
customKeywords = ""
searchRadiusLimitMiles = 3

# Enable this to plot various polygons as matplotlib graph too for help understanding the results
plotDebugGraph = False

UKtoWGS84Project = partial(pyproj.transform, pyproj.Proj(init='epsg:27700'), pyproj.Proj(init='epsg:4326'))
WGS84toUKProject = partial(pyproj.transform, pyproj.Proj(init='epsg:4326'), pyproj.Proj(init='epsg:27700'))

targetLngLat = mapboxTools.getCentrePointLngLatForAddress(targetLocationAddress)
if plotDebugGraph:
    plt.plot(*targetLngLat, marker='*', label='Target: '+targetLocationAddress)

if plotDebugGraph:
    targetBoundingBox = multiPolygonTools.getBoundingCircleForPoint(targetLngLat, searchRadiusLimitMiles)
    plt.plot(*targetBoundingBox.exterior.xy, label=str(searchRadiusLimitMiles)+' mile Search Radius')

walkingIsochroneGeom = mapboxTools.getWalkingIsochroneGeometry(targetLngLat, maxWalkingTimeMins)
walkingIsochronePolygon = Polygon(walkingIsochroneGeom)
# if plotDebugGraph:
    # plt.plot(*walkingIsochronePolygon.exterior.xy, label=maxWalkingTimeMins + 'min Walking Isochrone')

publicTransportIsochroneGeom = travelTimeTools.getPublicTransportIsochroneGeometry(targetLngLat, maxPublicTransportTravelTimeMins)
publicTransportIsochroneGeom = multiPolygonTools.convertMultiToSingleWithJoiningLines(publicTransportIsochroneGeom)
publicTransportIsochronePolygon = Polygon(publicTransportIsochroneGeom)
# if plotDebugGraph:
    # plt.plot(*publicTransportIsochronePolygon.exterior.xy, label=maxPublicTransportTravelTimeMins + 'min Public Transport Isochrone')

combinedIsochronesPolygon = multiPolygonTools.convertMultiToSingleWithJoiningLines([walkingIsochronePolygon, publicTransportIsochronePolygon])
if plotDebugGraph:
    plt.plot(*combinedIsochronesPolygon.exterior.xy, label='Combined '+maxPublicTransportTravelTimeMins+'min Transport / '+maxWalkingTimeMins+'min Walking Isochrone')

imdFilterCombinedPolygon = deprivationTools.getSimplifiedClippedUKDeprivationPolygon(minDeprivationScore, targetLngLat, searchRadiusLimitMiles)
if plotDebugGraph:
    plt.plot(*imdFilterCombinedPolygon.exterior.xy, label='Deprivation Score > ' + str(minDeprivationScore))

combinedIntersectionPolygon = combinedIsochronesPolygon.intersection(imdFilterCombinedPolygon)
combinedIntersectionPolygon = multiPolygonTools.convertMultiToSingleWithJoiningLines(combinedIntersectionPolygon)

# Simplify resulting polygon somewhat as URL can't be too long or Zoopla throws HTTP 414 error
combinedIntersectionPolygon = combinedIntersectionPolygon.simplify(0.0005)

if plotDebugGraph:
    plt.plot(*combinedIntersectionPolygon.exterior.xy, label='Resulting Intersection')

# Useful when debugging this to find the ideal simplification factor:
# print("Zoopla URL Length: " + str(len(zooplaTools.buildPropertyQueryURL(rental, minPrice, maxPrice, minBeds, maxBeds, sharedAccommodation, customKeywords, combinedIntersectionPolygon))))

if plotDebugGraph:
    # Also plot resulting polygon on mapbox leaflet map for easier debugging
    mapboxTools.viewPolygonInBrowser(combinedIntersectionPolygon)

    plt.legend()
    plt.show()

zooplaTools.launchPropertyQueryInBrowser(rental, minPrice, maxPrice, minBeds, maxBeds, sharedAccommodation, customKeywords, combinedIntersectionPolygon)
