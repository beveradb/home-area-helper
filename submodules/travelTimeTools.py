#!/usr/bin/env python3
import os
import json
import urllib.request

def getPublicTransportIsochroneGeometry(targetLngLat, maxPublicTransportTravelTimeMins):
    publicTransportIsochroneRequestHeaders = {
        'Content-Type': 'application/json',
        "X-Application-Id": os.environ['TRAVELTIME_APP_ID'],
        "X-Api-Key": os.environ['TRAVELTIME_API_KEY'],
    }

    publicTransportIsochroneRequestBodyJSON = json.dumps({
        "departure_searches": [
            {
                "id": "first request",
                "coords": {"lng": targetLngLat[0], "lat": targetLngLat[1]},
                "transportation": {"type": "public_transport"},
                "departure_time": "2019-09-30T08:00:00+0000",
                "travel_time": int(maxPublicTransportTravelTimeMins) * int(60)
            }
        ],
        "arrival_searches": []
    })

    publicTransportIsochroneRequest = urllib.request.Request(
        'http://api.traveltimeapp.com/v4/time-map', 
        publicTransportIsochroneRequestBodyJSON.encode("utf-8"),
        publicTransportIsochroneRequestHeaders
    )

    publicTransportIsochroneResponseObject = json.load(
        urllib.request.urlopen(publicTransportIsochroneRequest)
    )

    publicTransportIsochroneShapes = publicTransportIsochroneResponseObject['results'][0]['shapes']

    return normaliseTravelTimeShapes(publicTransportIsochroneShapes)

def normaliseTravelTimeShapes(shapesList):
    shapesListNormalised = []

    for singleShape in shapesList:
        shapeCoordsArray = []
        
        for singleShellCoord in singleShape['shell']:        
            shapeCoordsArray.append([singleShellCoord['lng'], singleShellCoord['lat']])

        shapesListNormalised.append(shapeCoordsArray)

    return shapesListNormalised