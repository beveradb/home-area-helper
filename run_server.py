#!/usr/bin/env python3
import logging
import os

import requests_cache
# This import of shapely is to workaround a GEOS bug: https://github.com/Toblerity/Shapely/issues/553
# noinspection PyUnresolvedReferences
import shapely.geometry
import ucache
from flask import Flask, render_template, Response, request
from flask_sslify import SSLify

from src import target_area, utils
from src.utils import preload_files

app = Flask(__name__)
sslify = SSLify(app)
app_debug = "HOMEAREA_DEBUG" in os.environ

# Set up debug logging to console
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger().setLevel(logging.DEBUG if app_debug else logging.INFO)

# Download dataset files and pre-seeded API call / compute cache to reduce slug size
preload_files('https://github.com/beveradb/home-area-helper/releases/download/v0.6/', [
    {'dir': 'datasets/uk/', 'file': 'uk-wgs84-imd-shapefiles.zip'},
    {'dir': 'caches/', 'file': 'requests_cache.sqlite.zip'},
    {'dir': 'caches/', 'file': 'static_cache.sqlite'},
])

# Set up disk caching for HTTP requests (e.g. API calls), pre-seeded from above download file
requests_cache = requests_cache.core.CachedSession(
    cache_name='caches/requests_cache', backend="sqlite", allowable_methods=('GET', 'POST'))

# Set up disk caching for complex computations which should not need to change -
static_cache = ucache.SqliteCache(
    filename='caches/static_cache.sqlite', cache_size=5000, timeout=32000000, compression=True)

# Set up disk caching for complex computations, with max size 5GB, compression and 1 year expiry;
# this cache is transient and will be wiped whenever the Heroku dyno is redeployed
transient_cache = ucache.SqliteCache(
    filename='caches/transient_cache.sqlite', cache_size=5000, timeout=32000000, compression=True)


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
    logging.log(logging.INFO, "Request received: " + str(req_data))

    results = target_area.get_target_areas_polygons_json(req_data)

    utils.log_method_timings()

    return Response(results, mimetype='application/json')


if __name__ == '__main__':
    port = os.environ['PORT'] if 'PORT' in os.environ else 9876
    app.run(debug=app_debug, host='0.0.0.0', port=port, use_evalex=False)
