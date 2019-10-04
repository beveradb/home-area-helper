#!/usr/bin/env python3
import matplotlib.pyplot as plt
from submodules import zooplaTools
from submodules import targetLocationTools

# This script requires you have environment variables set with your personal API keys:
# MAPBOX_ACCESS_TOKEN from https://docs.mapbox.com/help/how-mapbox-works/access-tokens/
# TRAVELTIME_APP_ID from https://docs.traveltimeplatform.com/overview/introduction
# TRAVELTIME_API_KEY from https://docs.traveltimeplatform.com/overview/introduction

# Parameters for where to search and what to search for!
targetLocationAddress = "WC1A 2TH, London, UK"
# targetLocationAddress = "69 Morrison Street, Edinburgh, UK"
# targetLocationAddress1 = "23 Turner St, Manchester, M4 1DY"
# targetLocationAddress2 = "Eildon House, Newtown St Boswells, Melrose, TD6 0PP"

maxWalkingTimeMins = 15
maxPublicTransportTravelTimeMins = 20
minDeprivationScore = 5
searchRadiusLimitMiles = 3

rental = True
sharedAccommodation = False
minPrice = ""
maxPrice = "1300"
minBeds = "1"
maxBeds = ""
customKeywords = ""

# Enable this to plot various polygons as matplotlib graph too for help understanding the results
plotDebugGraph = True

intersectionResults = targetLocationTools.getTargetLocationPolygons(
    targetLocationAddress,
    searchRadiusLimitMiles,
    maxWalkingTimeMins,
    maxPublicTransportTravelTimeMins,
    minDeprivationScore
)

print(zooplaTools.launchPropertyQueryInBrowser(
    rental, minPrice, maxPrice, minBeds, maxBeds, sharedAccommodation, customKeywords,
    intersectionResults['combinedIntersection']['polygon']
))

if plotDebugGraph:
    for key, value in intersectionResults.items():
        if 'polygon' in value:
            plt.plot(*value['polygon'].exterior.xy, label=value['label'])
    plt.plot(*intersectionResults['targetLngLat'], marker='*', label='Target: '+targetLocationAddress)
    plt.legend()
    plt.show()
