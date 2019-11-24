#!/usr/bin/env python3
import json
import logging

import pandas as pd
from shapely.geometry import mapping

from run_server import transient_cache, static_cache
from src import google_maps
from src.multi_polygons import get_bounding_circle_for_point, join_multi_to_single_poly
from src.utils import timeit


@transient_cache.cached()
def get_target_cities(params: dict):
    target_cities_result = []

    country_code = str(params['countryCodeInput'])
    target_cities = get_country_cities_combined_data(country_code)

    for target_city in target_cities:
        # Filter by arbitrary user-given params
        if params['minPopulationInput']:
            if int(target_city['Population']["Population on the 1st of January, total"]) < int(
                    params['minPopulationInput']):
                continue

        city_center_coords = google_maps.get_centre_point_lng_lat_for_address(
            target_city['Name'] + ', ' + country_code
        )

        if city_center_coords is not None:
            city_polygon = get_bounding_circle_for_point(city_center_coords, 2)

            target_cities_result.append({
                'label': target_city['Name'],
                'coords': city_center_coords,
                'polygon': city_polygon,
                'data': target_city
            })

    return target_cities_result


@static_cache.cached()
def get_eurostat_countries():
    return [
        {"code": "AT", "label": "Austria"},
        {"code": "BE", "label": "Belgium"},
        {"code": "BG", "label": "Bulgaria"},
        {"code": "CH", "label": "Switzerland"},
        {"code": "CY", "label": "Cyprus"},
        {"code": "CZ", "label": "Czech Republic"},
        {"code": "DE", "label": "Germany"},
        {"code": "DK", "label": "Denmark"},
        {"code": "EE", "label": "Estonia"},
        {"code": "EL", "label": "Greece"},
        {"code": "ES", "label": "Spain"},
        {"code": "FI", "label": "Finland"},
        {"code": "FR", "label": "France"},
        {"code": "HR", "label": "Croatia"},
        {"code": "HU", "label": "Hungary"},
        {"code": "IE", "label": "Ireland"},
        {"code": "IS", "label": "Iceland"},
        {"code": "IT", "label": "Italy"},
        {"code": "LT", "label": "Lithuania"},
        {"code": "LU", "label": "Luxembourg"},
        {"code": "LV", "label": "Latvia"},
        {"code": "MT", "label": "Malta"},
        {"code": "NL", "label": "Netherlands"},
        {"code": "NO", "label": "Norway"},
        {"code": "PL", "label": "Poland"},
        {"code": "PT", "label": "Portugal"},
        {"code": "RO", "label": "Romania"},
        {"code": "SE", "label": "Sweden"},
        {"code": "SI", "label": "Slovenia"},
        {"code": "SK", "label": "Slovakia"},
        {"code": "TR", "label": "Turkey"},
        {"code": "UK", "label": "United Kingdom"}
    ]


@static_cache.cached()
def load_eurostat_metadata():
    eurostat_data_dir = 'datasets/europe/eurostat-cities-2019/'

    eurostat_meta_df = {
        'Indicator list': pd.read_excel(eurostat_data_dir + 'urb_esms_an1.xlsx'),
        'Validation rules': pd.read_excel(eurostat_data_dir + 'urb_esms_an2.xlsx'),
        'Variable list': pd.read_excel(eurostat_data_dir + 'urb_esms_an3.xls'),
        'List of cities': pd.read_excel(eurostat_data_dir + 'urb_esms_an4.xls'),
        'Perception Indicators': pd.read_csv(eurostat_data_dir + 'urb_percep_indicators.tsv', sep='\t', header=None,
                                             names=['Code', 'Label']),
    }

    # Columns:
    # List of cities: ["CODE", "NAME"]
    # Indicator list: ["CODE", "LABEL", "indicator calculation nominator", "indicator calculation denominator"]
    # Validation rules: ["Rule name", "New Rule Name",…]
    # Variable list: ["Domain", "Code", "Label", "To be collected by NSI included in Annex A of Grants 2014/2015",…]

    return eurostat_meta_df


@static_cache.cached()
def load_eurostat_data():
    eurostat_data_dir = 'datasets/europe/eurostat-cities-2019/'

    eurostat_df = {
        'Economy and finance':
            pd.read_csv(eurostat_data_dir + 'urb_cecfi.tsv.gz', sep='\t', header=0,
                        compression='gzip', error_bad_lines=False),
        'Environment':
            pd.read_csv(eurostat_data_dir + 'urb_cenv.tsv.gz', sep='\t', header=0,
                        compression='gzip', error_bad_lines=False),
        'Fertility and mortality':
            pd.read_csv(eurostat_data_dir + 'urb_cfermor.tsv.gz', sep='\t', header=0,
                        compression='gzip', error_bad_lines=False),
        'Education':
            pd.read_csv(eurostat_data_dir + 'urb_ceduc.tsv.gz', sep='\t', header=0,
                        compression='gzip', error_bad_lines=False),
        'Living conditions':
            pd.read_csv(eurostat_data_dir + 'urb_clivcon.tsv.gz', sep='\t', header=0,
                        compression='gzip', error_bad_lines=False),
        'Labour market':
            pd.read_csv(eurostat_data_dir + 'urb_clma.tsv.gz', sep='\t', header=0,
                        compression='gzip', error_bad_lines=False),
        'Population':
            pd.read_csv(eurostat_data_dir + 'urb_cpop1.tsv.gz', sep='\t', header=0,
                        compression='gzip', error_bad_lines=False),
        'Culture and tourism':
            pd.read_csv(eurostat_data_dir + 'urb_ctour.tsv.gz', sep='\t', header=0,
                        compression='gzip', error_bad_lines=False),
        'Transport':
            pd.read_csv(eurostat_data_dir + 'urb_ctran.tsv.gz', sep='\t', header=0,
                        compression='gzip', error_bad_lines=False),
        'Perception survey':
            pd.read_csv(eurostat_data_dir + 'urb_percep.tsv.gz', sep='\t', header=0,
                        compression='gzip', error_bad_lines=False),
    }

    # Columns:
    # Culture and tourism: ["indic_ur,cities\time", "2019 ", "2018 ", "2017 ", "2016 ", "2015 ", "2014 ", "2013 " ...]
    # Economy and finance: ["indic_ur,cities\time", "2018 ", "2017 ", "2016 ", "2015 ", "2014 ", "2013 ", "2012 "...]
    # Education: ["indic_ur,cities\time", "2019 ", "2018 ", "2017 ", "2016 ", "2015 ", "2014 ", "2013 ", "2012 " ...]
    # Environment: ["indic_ur,cities\time", "2019 ", "2018 ", "2017 ", "2016 ", "2015 ", "2014 ", "2013 ", "2012 " ...]
    # Fertility and mortality: ["indic_ur,cities\time", "2019 ", "2018 ", "2017 ", "2016 ", "2015 ", "2014 " ...]
    # Labour market: ["indic_ur,cities\time", "2019 ", "2018 ", "2017 ", "2016 ", "2015 ", "2014 ", "2013 ", ...]
    # Living conditions: ["indic_ur,cities\time", "2018 ", "2017 ", "2016 ", "2015 ", "2014 ", "2013 ", "2012 " ...]
    # Perception survey: ["indic_ur,unit,cities\time", "2015 ", "2012 ", "2009 ", "2006 ", "2004 "]
    # Population: ["indic_ur,cities\time", "2019 ", "2018 ", "2017 ", "2016 ", "2015 " ...]
    # Transport: ["indic_ur,cities\time", "2019 ", "2018 ", "2017 ", "2016 ", "2015 ", "2014 ", "2013 ", "2012 " ...]

    return eurostat_df


@static_cache.cached()
def get_country_cities_combined_data(country):
    eurostat_meta_df = load_eurostat_metadata()
    eurostat_df = load_eurostat_data()

    # Example CODE value for a UK city: UK007C1
    city_code_regex = '^' + country + '[0-9]+C[0-9]+$'

    cities_filtered_df = eurostat_meta_df['List of cities'][
        eurostat_meta_df['List of cities']['CODE'].str.contains(city_code_regex)
    ]

    indicators_map = eurostat_meta_df['Indicator list'].set_index('CODE').to_dict(orient='index')
    variables_map = eurostat_meta_df['Variable list'].set_index('Code').to_dict(orient='index')
    perception_map = eurostat_meta_df['Perception Indicators'].set_index('Code').to_dict(orient='index')

    result_cities_list = []

    for cities_idx, cities_row in cities_filtered_df.iterrows():
        city_code = cities_row['CODE']

        single_city_data = {
            'Code': city_code,
            'Name': cities_row['NAME']
        }

        city_data_regex = city_code + '$'

        for category_index, category_name in enumerate(eurostat_df):
            category_df = eurostat_df[category_name]
            first_col_name = category_df.columns[0]
            city_data_df = category_df[
                category_df[first_col_name].str.contains(city_data_regex)
            ]
            single_city_data[category_name] = {}

            for city_data_idx, city_data_row in city_data_df.iterrows():
                city_data_indicator = city_data_row[first_col_name]
                city_data_indicator = city_data_indicator.split(',')[0]

                if city_data_indicator in variables_map.keys():
                    city_data_indicator = variables_map[city_data_indicator]['Label']
                elif city_data_indicator in indicators_map.keys():
                    city_data_indicator = indicators_map[city_data_indicator]['LABEL']
                elif city_data_indicator in perception_map.keys():
                    city_data_indicator = perception_map[city_data_indicator]['Label']

                for city_data_col_idx, city_data_year in enumerate(category_df.columns):
                    if city_data_col_idx == 0:
                        continue

                    city_data_value = city_data_row[city_data_year]
                    if city_data_value != ': ':
                        single_city_data[category_name][city_data_indicator] = city_data_value
                        break

        result_cities_list.append(single_city_data)

    # Result object shape:
    # [
    #   {
    #       "Code": "UK002C1",
    #       "Name": "Birmingham",
    #       "Economy and finance": {
    #           "All companies": "34565 d"
    #       },
    #       "Population": {
    #           "Population on the 1st of January, total": "515855 "
    #       }
    #       ...
    #   }
    # ]

    return result_cities_list


@timeit
@transient_cache.cached()
def get_target_cities_data_json(params: dict):
    response_object = {
        'targets_results': [],
        'result_intersection': None
    }

    target_cities_polygons = []
    target_cities = get_target_cities(params)

    for target_city in target_cities:
        response_object['targets_results'].append({
            'target': {
                'label': target_city['label'],
                'coords': target_city['coords'],
                'polygon': mapping(target_city['polygon']),
                'data': target_city['data']
            }
        })
        target_cities_polygons.append(target_city['polygon'])

    if target_cities_polygons:
        logging.debug(target_cities_polygons)
        joined_cities = join_multi_to_single_poly(target_cities_polygons)

        response_object['results_combined'] = {
            'label': 'All Cities Combined',
            'bounds': joined_cities.bounds,
            'centroid': mapping(joined_cities.centroid)['coordinates']
        }

    return json.dumps(response_object)
