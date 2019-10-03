#!/usr/bin/env python3
import os
import json
import time
import urllib.request
import webbrowser
import jinja2
from shapely.geometry import Polygon
from mapbox import Geocoder

def getCentrePointLngLatForAddress(addressString):
    geocoder = Geocoder()
    targetLocationGeocode = geocoder.forward(addressString)
    targetLocationGeocodeFeature = targetLocationGeocode.geojson()['features'][0]
    return targetLocationGeocodeFeature['geometry']['coordinates']

def getWalkingIsochroneGeometry(targetLngLat, maxWalkingTimeMins):
    walkingIsochroneURL = "https://api.mapbox.com/isochrone/v1/mapbox/walking/"
    walkingIsochroneURL += str(targetLngLat[0])+","+str(targetLngLat[1])
    walkingIsochroneURL +="?contours_minutes=" + str(maxWalkingTimeMins)
    walkingIsochroneURL +="&access_token=" + os.environ['MAPBOX_ACCESS_TOKEN']

    walkingIsochroneResponseObject = json.load(
        urllib.request.urlopen(walkingIsochroneURL)
    )

    return walkingIsochroneResponseObject['features'][0]['geometry']['coordinates']

def viewPolygonInBrowser(singlePolygon):
    if type(singlePolygon) is not Polygon: singlePolygon = Polygon(singlePolygon)
    
    singlePolygonExterior = singlePolygon.exterior
    
    if hasattr(singlePolygonExterior, 'coords'):
        # Debug polygon object by plotting on Leaflet map in web browser by rendering to an HTML file
        singlePolygonCoords = []
        for coord in list(zip(*singlePolygonExterior.coords.xy)):
            singlePolygonCoords.append([coord[0], coord[1]])

        singlePolygonRepPoint = singlePolygon.representative_point()

        tempMapPlotFilename = "mapbox-polygon-temp.html"
        jinja2.Template(open("src/mapbox-polygon-template.html").read()).stream(
            MAPBOX_ACCESS_TOKEN=os.environ['MAPBOX_ACCESS_TOKEN'],
            MAP_CENTER_POINT_COORD="[" + str(singlePolygonRepPoint.x) + "," + str(singlePolygonRepPoint.y) + "]",
            MAP_LAYER_GEOJSON=[singlePolygonCoords]
        ).dump(tempMapPlotFilename)

        webbrowser.open_new("file://" + os.getcwd() + "/" + tempMapPlotFilename)
        # time.sleep(3)
        # os.remove(tempMapPlotFilename)
