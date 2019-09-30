#!/usr/bin/env python3
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from shapely.ops import unary_union, transform
from functools import partial
import pyproj

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
minDeprivationScore = 10
maxWalkingTimeMins = "15"
maxPublicTransportTravelTimeMins = "30"
rental = True
sharedAccommodation = False
minPrice = ""
maxPrice = "1300"
minBeds = "1"
maxBeds = ""
customKeywords = ""

UKtoWGS84Project = partial(pyproj.transform, pyproj.Proj(init='epsg:27700'), pyproj.Proj(init='epsg:4326'))
WGS84toUKProject = partial(pyproj.transform, pyproj.Proj(init='epsg:4326'), pyproj.Proj(init='epsg:27700'))

targetLngLat = mapboxTools.getCentrePointLngLatForAddress(targetLocationAddress)

walkingIsochroneGeom = mapboxTools.getWalkingIsochroneGeometry(targetLngLat, maxWalkingTimeMins)
walkingIsochronePolygon = transform(WGS84toUKProject, Polygon(walkingIsochroneGeom))

# plt.plot(*walkingIsochronePolygon.exterior.xy)
# mapboxTools.viewPolygonInBrowser(walkingIsochroneGeom)

publicTransportIsochroneGeom = travelTimeTools.getPublicTransportIsochroneGeometry(targetLngLat, maxPublicTransportTravelTimeMins)
publicTransportIsochroneGeom = multiPolygonTools.convertMultiToSingleWithJoiningLines(publicTransportIsochroneGeom)
publicTransportIsochronePolygon = transform(WGS84toUKProject, Polygon(publicTransportIsochroneGeom))

# plt.plot(*publicTransportIsochronePolygon.exterior.xy)
# mapboxTools.viewPolygonInBrowser(publicTransportIsochroneGeom)

combinedIsochronesPolygon = multiPolygonTools.convertMultiToSingleWithJoiningLines([walkingIsochronePolygon, publicTransportIsochronePolygon])
# plt.plot(*combinedIsochronesPolygon.exterior.xy)

deprivationFilterMultiPolygon = deprivationTools.getPolygonForLeastDeprivedZonesEngland(minDeprivationScore)
print("deprivationFilterMultiPolygon type pre-filter: " + str(type(deprivationFilterMultiPolygon)))
print("deprivationFilterMultiPolygon length pre-filter: " + str(len(deprivationFilterMultiPolygon)))

# for deprivationFilterSinglePolygon in deprivationFilterMultiPolygon:
#    plt.plot(*Polygon(deprivationFilterSinglePolygon).exterior.xy)

combinedIntersectionPolygon = combinedIsochronesPolygon.intersection(deprivationFilterMultiPolygon)
combinedIntersectionPolygon = multiPolygonTools.convertMultiToSingleWithJoiningLines(combinedIntersectionPolygon)
# plt.plot(*combinedIntersectionPolygon.exterior.xy)
# plt.show()
# exit()

combinedIntersectionPolygon = transform(UKtoWGS84Project, combinedIntersectionPolygon)

# Simplify resulting polygon somewhat as URL can't be too long or Zoopla throws HTTP 414 error
combinedIntersectionPolygon = combinedIntersectionPolygon.simplify(0.0005)

# Useful when debugging this to find the ideal simplification factor:
# print("Zoopla URL Length: " + str(len(zooplaTools.buildPropertyQueryURL(rental, minPrice, maxPrice, minBeds, maxBeds, sharedAccommodation, customKeywords, combinedIntersectionPolygon))))

# Plot on mapbox leaflet map for easier debugging polygons
# mapboxTools.viewPolygonInBrowser(combinedIntersectionPolygon)

# Plot on matplotlib graph for further debugging polygons
# plt.plot(*combinedIntersectionPolygon.exterior.xy)
# plt.show()

zooplaTools.launchPropertyQueryInBrowser(rental, minPrice, maxPrice, minBeds, maxBeds, sharedAccommodation, customKeywords, combinedIntersectionPolygon)
