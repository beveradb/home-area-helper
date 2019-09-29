#!/usr/bin/env python3
import matplotlib.pyplot as plt
import multiPolygonTools
import zooplaTools
import travelTimeTools
import mapboxTools

# This script requires you have environment variables set with your personal API keys:
# MAPBOX_ACCESS_TOKEN from https://docs.mapbox.com/help/how-mapbox-works/access-tokens/
# TRAVELTIME_APP_ID from https://docs.traveltimeplatform.com/overview/introduction
# TRAVELTIME_API_KEY from https://docs.traveltimeplatform.com/overview/introduction

# Parameters for where to search and what to search for!
targetLocationAddress = "WC1A 2TH, London, UK"
maxWalkingTimeMins = "15"
maxPublicTransportTravelTimeMins = "30"
rental = True
sharedAccommodation = False
minPrice = ""
maxPrice = "1300"
minBeds = "1"
maxBeds = ""
customKeywords = ""

targetLngLat = mapboxTools.getCentrePointLngLatForAddress(targetLocationAddress)
walkingIsochroneGeom = mapboxTools.getWalkingIsochroneGeometry(targetLngLat, maxWalkingTimeMins)
# plt.plot(*Polygon(walkingIsochroneGeom).exterior.xy)
# mapboxTools.viewPolygonInBrowser(walkingIsochroneGeom)

publicTransportIsochroneGeom = travelTimeTools.getPublicTransportIsochroneGeometry(targetLngLat, maxPublicTransportTravelTimeMins)
publicTransportIsochroneGeom = multiPolygonTools.convertMultiToSingleWithJoiningLines(publicTransportIsochroneGeom)
# plt.plot(*Polygon(publicTransportIsochroneGeom).exterior.xy)
# mapboxTools.viewPolygonInBrowser(publicTransportIsochroneGeom)

combinedPolygon = multiPolygonTools.convertMultiToSingleWithJoiningLines([walkingIsochroneGeom, publicTransportIsochroneGeom])

# Simplify resulting polygon somewhat as URL can't be too long or Zoopla throws HTTP 414 error
combinedPolygon = combinedPolygon.simplify(0.001)

# Useful when debugging this to find the ideal simplification factor:
# print("Zoopla URL Length: " + str(len(zooplaTools.buildPropertyQueryURL(rental, minPrice, maxPrice, minBeds, maxBeds, sharedAccommodation, customKeywords, combinedPolygon))))

# Plot on mapbox leaflet map for easier debugging polygons
# mapboxTools.viewPolygonInBrowser(combinedPolygon)

# Plot on matplotlib graph for further debugging polygons
# plt.plot(*Polygon(combinedGeom).exterior.xy)
# plt.show()

zooplaTools.launchPropertyQueryInBrowser(rental, minPrice, maxPrice, minBeds, maxBeds, sharedAccommodation, customKeywords, combinedPolygon)
