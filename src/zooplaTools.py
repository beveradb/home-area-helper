#!/usr/bin/env python3
import urllib
import webbrowser
import polyline

def launchPropertyQueryInBrowser(rental, minPrice, maxPrice, minBeds, maxBeds, sharedAccommodation, customKeywords, areaPolygon):
    zooplaURL = buildPropertyQueryURL(rental, minPrice, maxPrice, minBeds, maxBeds, sharedAccommodation, customKeywords, areaPolygon)
    webbrowser.open_new(zooplaURL)

def buildPropertyQueryURL(rental, minPrice, maxPrice, minBeds, maxBeds, sharedAccommodation, customKeywords, areaPolygon):
    areaPolygonCoordsList = []
    for coord in list(zip(*areaPolygon.exterior.coords.xy)):
        areaPolygonCoordsList.append([coord[0], coord[1]])

    areaEncodedPolyline = polyline.encode(areaPolygonCoordsList, 5, True)

    rentOrSaleString = "to-rent" if rental else "for-sale"
    sharedAccommodationString = "true" if sharedAccommodation else "false"
    broadLocation = "UK"

    zooplaURL = "https://www.zoopla.co.uk/" + rentOrSaleString + "/map/property/"
    zooplaURL += broadLocation + "/?q=" + broadLocation
    zooplaURL += "&category=residential"
    zooplaURL += "&country_code="
    zooplaURL += "&include_shared_accommodation=" + sharedAccommodationString
    zooplaURL += "&keywords=" + customKeywords
    zooplaURL += "&radius=0"
    zooplaURL += "&added="
    zooplaURL += "&available_from="
    zooplaURL += "&price_frequency=per_month"
    zooplaURL += "&price_min=" + minPrice
    zooplaURL += "&price_max=" + maxPrice
    zooplaURL += "&beds_min=" + minBeds
    zooplaURL += "&beds_max=" + maxBeds
    zooplaURL += "&include_retirement_homes=true"
    zooplaURL += "&include_shared_ownership=" + sharedAccommodationString
    zooplaURL += "&new_homes=include"
    zooplaURL += "&polyenc=" + urllib.parse.quote(areaEncodedPolyline)
    zooplaURL += "&search_source=refine"

    return zooplaURL