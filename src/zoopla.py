#!/usr/bin/env python3
import webbrowser
from urllib import parse

import polyline


def launch_property_query_in_browser(rental, min_price, max_price, min_beds, max_beds, shared_accommodation,
                                     custom_keywords, area_polygon):
    # Useful when debugging this to find the ideal simplification factor:
    # print("Zoopla URL Length: " + str(len(zooplaTools.buildPropertyQueryURL(
    # rental, minPrice, maxPrice, minBeds, maxBeds, sharedAccommodation, customKeywords, combinedIntersectionPolygon))))

    zoopla_url = build_property_query_url(rental, min_price, max_price, min_beds, max_beds, shared_accommodation,
                                          custom_keywords, area_polygon)
    webbrowser.open_new(zoopla_url)


def build_property_query_url(rental, min_price, max_price, min_beds, max_beds, shared_accommodation, custom_keywords,
                             area_polygon):
    area_polygon_coords_list = []
    for coord in list(zip(*area_polygon.exterior.coords.xy)):
        area_polygon_coords_list.append([coord[0], coord[1]])

    area_encoded_polyline = polyline.encode(area_polygon_coords_list, 5, True)

    rent_or_sale_string = "to-rent" if rental else "for-sale"
    shared_accommodation_string = "true" if shared_accommodation else "false"
    broad_location = "UK"

    zoopla_url = "https://www.zoopla.co.uk/" + rent_or_sale_string + "/map/property/"
    zoopla_url += broad_location + "/?q=" + broad_location
    zoopla_url += "&category=residential"
    zoopla_url += "&country_code="
    zoopla_url += "&include_shared_accommodation=" + shared_accommodation_string
    zoopla_url += "&keywords=" + custom_keywords
    zoopla_url += "&radius=0"
    zoopla_url += "&added="
    zoopla_url += "&available_from="
    zoopla_url += "&price_frequency=per_month"
    zoopla_url += "&price_min=" + str(min_price)
    zoopla_url += "&price_max=" + str(max_price)
    zoopla_url += "&beds_min=" + str(min_beds)
    zoopla_url += "&beds_max=" + str(max_beds)
    zoopla_url += "&include_retirement_homes=true"
    zoopla_url += "&include_shared_ownership=" + shared_accommodation_string
    zoopla_url += "&new_homes=include"
    zoopla_url += "&polyenc=" + parse.quote(area_encoded_polyline)
    zoopla_url += "&search_source=refine"

    return zoopla_url
