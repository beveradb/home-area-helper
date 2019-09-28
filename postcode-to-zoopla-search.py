from mapbox import Geocoder
import json
import urllib.request
import os
import polyline
import webbrowser

geocoder = Geocoder()

targetLocationAddress = "69 Morrison Street, Edinburgh, UK"
maxWalkingTimeMins = "10"
rental = True
minPrice = ""
maxPrice = "1200"
minBeds = "2"
maxBeds = ""
customKeywords = ""

rentOrSaleString = "to-rent" if rental else "for-sale"
locationString = "UK"

targetLocationGeocode = geocoder.forward(targetLocationAddress)
targetLocationGeocodeFeature = targetLocationGeocode.geojson()['features'][0]
targetLocationLatLon = targetLocationGeocodeFeature['geometry']['coordinates']
targetLocationLatLonString = ','.join(map(str, targetLocationLatLon))
# print("targetLocationLatLonString: " + targetLocationLatLonString)

isochroneURL = "https://api.mapbox.com/isochrone/v1/mapbox/walking/" + targetLocationLatLonString + "?contours_minutes=" + maxWalkingTimeMins + "&access_token=" + os.environ['MAPBOX_ACCESS_TOKEN']
# print("isochroneURL: " + isochroneURL)
isochroneResponse = json.load(urllib.request.urlopen(isochroneURL))

isochroneGeometry = isochroneResponse['features'][0]['geometry']['coordinates']
isochronePolyline = polyline.encode(isochroneGeometry, 5, True)
isochronePolylineUrlencoded = urllib.parse.quote(isochronePolyline)
# print("isochronePolylineUrlencoded: " + isochronePolylineUrlencoded)

zooplaURL = "https://www.zoopla.co.uk/" + rentOrSaleString + "/map/property/"
zooplaURL += locationString + "/?q=" + locationString
zooplaURL += "&category=residential"
zooplaURL += "&country_code="
zooplaURL += "&include_shared_accommodation=true"
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
zooplaURL += "&include_shared_ownership=true"
zooplaURL += "&new_homes=include"
zooplaURL += "&polyenc=" + isochronePolylineUrlencoded
zooplaURL += "&search_source=refine"
# print("zooplaURL: " + zooplaURL)

webbrowser.open_new(zooplaURL)
