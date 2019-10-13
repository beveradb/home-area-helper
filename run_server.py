#!/usr/bin/env python3
import logging
import os

import ucache
from flask import Flask, render_template, Response, request

from src import target_area, utils

app = Flask(__name__)

# Set up debug logging to console
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger().setLevel(logging.DEBUG)

# Set up disk caching for complex computations, with max size 5GB and 1 year expiry
cache = ucache.SqliteCache(filename='compute_cache.sqlite', cache_size=5000, timeout=32000000, compression=True)


@app.route('/')
def index():
    # This script requires you define environment variables with your personal API keys:
    # MAPBOX_ACCESS_TOKEN from https://docs.mapbox.com/help/how-mapbox-works/access-tokens/
    # TRAVELTIME_APP_ID from https://docs.traveltimeplatform.com/overview/introduction
    # TRAVELTIME_API_KEY from https://docs.traveltimeplatform.com/overview/introduction

    return render_template(
        'index.html',
        MAPBOX_ACCESS_TOKEN=os.environ['MAPBOX_ACCESS_TOKEN']
    )


@app.route('/target_area', methods=['POST'])
def target_area_json():
    req_data = request.get_json()
    # yappi.start()
    # cache.flush()

    logging.log(logging.INFO, "Request received: " + str(req_data))

    results = target_area.get_target_areas_polygons_json(req_data)

    # func_stats = yappi.get_func_stats()
    # func_stats.save('callgrind.out.' + str(time.time()), 'CALLGRIND')
    # yappi.stop()
    # yappi.clear_stats()
    utils.log_method_timings()

    return Response(results, mimetype='application/json')


if __name__ == '__main__':
    port = os.environ['PORT'] if 'PORT' in os.environ else 9876
    app.run(debug=True, host='0.0.0.0', port=port, use_evalex=False)
