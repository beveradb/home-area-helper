#!/usr/bin/env python3
from src import target_area
from src import zoopla

# This script requires you have environment variables set with your personal API keys:
# MAPBOX_ACCESS_TOKEN from https://docs.mapbox.com/help/how-mapbox-works/access-tokens/
# TRAVELTIME_APP_ID from https://docs.traveltimeplatform.com/overview/introduction
# TRAVELTIME_API_KEY from https://docs.traveltimeplatform.com/overview/introduction

intersection_results = target_area.get_target_location_polygons(
    target_location_address="WC1A 2TH, London, UK",
    min_deprivation_score=5,
    max_walking_time_mins=15,
    max_public_transport_travel_time_mins=20,
    search_radius_limit_miles=3
)

zoopla.launch_property_query_in_browser(
    rental=True,
    shared_accommodation=False,
    min_price=0,
    max_price=1300,
    min_beds=1,
    max_beds=4,
    custom_keywords="",
    area_polygon=intersection_results['combinedIntersection']['polygon']
)

# Enable this to plot various polygons as matplotlib graph too for help understanding the results
target_area.plot_target_area_polygons_mpl(intersection_results)
