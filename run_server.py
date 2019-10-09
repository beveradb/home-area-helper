#!/usr/bin/env python3
import json
import os

from flask import Flask, render_template, Response
from shapely.geometry import mapping

from src import target_area, timeit

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


target_area_route = '/target_area/<string:target>'
target_area_route += '/<int:walking>/<int:cycling>/<int:bus>'
target_area_route += '/<int:coach>/<int:train>/<int:driving>'
target_area_route += '/<int:deprivation>'


@app.route(target_area_route)
def target_area_json(
        target: str,
        walking: int,
        cycling: int,
        bus: int,
        coach: int,
        train: int,
        driving: int,
        deprivation: int
):
    timeit.clear_logfile()

    # yappi.start()

    def calculate_results():
        polygon_results = target_area.get_target_area_polygons(
            target_location_address=target,
            min_deprivation_score=deprivation,
            max_walking_time_mins=walking,
            max_cycling_time_mins=cycling,
            max_bus_time_mins=bus,
            max_coach_time_mins=coach,
            max_train_time_mins=train,
            max_driving_time_mins=driving
        )
        for key, value in polygon_results.items():
            if 'polygon' in value:
                polygon_results[key]['polygon'] = mapping(value['polygon'])

        return json.dumps(polygon_results)

    results = calculate_results()

    # func_stats = yappi.get_func_stats()
    # func_stats.save('callgrind.out.' + str(time.time()), 'CALLGRIND')
    # yappi.stop()
    # yappi.clear_stats()
    timeit.log_cumulatives()

    return Response(results, mimetype='application/json')


if __name__ == '__main__':
    port = os.environ['PORT'] if 'PORT' in os.environ else 9876
    app.run(debug=True, host='0.0.0.0', port=port, use_evalex=False)
