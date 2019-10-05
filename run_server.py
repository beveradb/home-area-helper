#!/usr/bin/env python3
import os
import webbrowser

from flask import Flask, render_template, jsonify
from shapely.geometry import mapping

from src import target_area

app = Flask(__name__)


@app.route('/')
def index():
    # This script requires you have environment variables set with your personal API keys:
    # MAPBOX_ACCESS_TOKEN from https://docs.mapbox.com/help/how-mapbox-works/access-tokens/
    # TRAVELTIME_APP_ID from https://docs.traveltimeplatform.com/overview/introduction
    # TRAVELTIME_API_KEY from https://docs.traveltimeplatform.com/overview/introduction

    return render_template(
        'index.html',
        MAPBOX_ACCESS_TOKEN=os.environ['MAPBOX_ACCESS_TOKEN']
    )


@app.route('/target_area/<string:target>/<int:walking>/<int:pubtrans>/<int:driving>/<int:deprivation>')
def target_area_json(
        target: str,
        walking: int,
        pubtrans: int,
        driving: int,
        deprivation: int
):
    polygon_results = target_area.get_target_area_polygons(
        target_location_address=target,
        min_deprivation_score=deprivation,
        max_walking_time_mins=walking,
        max_public_transport_travel_time_mins=pubtrans,
        max_driving_time_mins=driving
    )
    for key, value in polygon_results.items():
        if 'polygon' in value:
            polygon_results[key]['polygon'] = mapping(value['polygon'])

    return jsonify(polygon_results)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80, use_evalex=False)
