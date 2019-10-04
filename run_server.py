#!/usr/bin/env python3
import os

from flask import Flask, render_template, jsonify

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


@app.route('/target_area/<string:target>/<int:walking>/<int:transport>/<int:deprivation>/<int:radius>')
def target_area(
        target: str,
        walking: int,
        transport: int,
        deprivation: int,
        radius: int
):
    return jsonify(target_area.get_target_area_polygons(
        target_location_address=target,
        min_deprivation_score=deprivation,
        max_walking_time_mins=walking,
        max_public_transport_travel_time_mins=transport,
        search_radius_limit_miles=radius
    ))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
