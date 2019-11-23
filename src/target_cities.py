#!/usr/bin/env python3
import json
import logging

import pandas as pd
from shapely.geometry import mapping

from src import google_maps
from src.multi_polygons import get_bounding_circle_for_point, join_multi_to_single_poly
from src.utils import timeit


def get_target_cities(params: dict):
    city_center_coords = google_maps.get_centre_point_lng_lat_for_address(
        str(params['countryInput'])
    )

    city_polygon = get_bounding_circle_for_point(city_center_coords, 2)

    return [
        {
            'label': str(params['countryInput']),
            'coords': city_center_coords,
            'polygon': city_polygon
        }
    ]


def get_filtered_cities_combined_data_dict(country):
    eurostat_data_dir = 'datasets/europe/eurostat-cities-2019/'

    eurostat_df = {
        'Indicator list': pd.read_excel(eurostat_data_dir + 'urb_esms_an1.xlsx'),
        'Validation rules': pd.read_excel(eurostat_data_dir + 'urb_esms_an2.xlsx'),
        'Variable list': pd.read_excel(eurostat_data_dir + 'urb_esms_an3.xls'),
        'List of cities': pd.read_excel(eurostat_data_dir + 'urb_esms_an4.xls'),

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
    # List of cities: ["CODE", "NAME"]
    # Indicator list: ["CODE", "LABEL", "indicator calculation nominator", "indicator calculation denominator"]
    # Validation rules: ["Rule name", "New Rule Name",…]
    # Variable list: ["Domain", "Code", "Label", "To be collected by NSI included in Annex A of Grants 2014/2015",…]
    #
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

    # Example CODE value for a UK city: UK007C1
    city_code_regex = '^' + country + '[0-9]+C[0-9]+$'
    cities_filtered_df = eurostat_df['List of cities'][
        eurostat_df['List of cities']['CODE'].str.contains(city_code_regex)
    ]

    indicators_map = eurostat_df['Indicator list'].set_index('CODE').to_dict(orient='index')
    variables_map = eurostat_df['Variable list'].set_index('Code').to_dict(orient='index')
    print(indicators_map)
    print(variables_map)

    result_cities_list = []

    for cities_idx, cities_row in cities_filtered_df.iterrows():
        city_code = cities_row['CODE']

        single_city_data = {
            'Code': city_code,
            'Name': cities_row['NAME'],
            'Population Data': {}
        }

        city_data_regex = city_code + '$'

        first_col_name = eurostat_df['Population'].columns[0]
        city_data_df = eurostat_df['Population'][
            eurostat_df['Population'][first_col_name].str.contains(city_data_regex)
        ]

        for city_data_idx, city_data_row in city_data_df.iterrows():
            city_data_indicator = city_data_row[first_col_name]
            city_data_indicator = city_data_indicator.split(',')[0]
            city_data_indicator = variables_map[city_data_indicator]['Label']

            for city_data_col_idx, city_data_year in enumerate(eurostat_df['Population'].columns):
                if city_data_col_idx == 0:
                    continue

                city_data_value = city_data_row[city_data_year]
                if city_data_value != ': ':
                    single_city_data['Population Data'][city_data_indicator] = city_data_value
                    break

        result_cities_list.append(single_city_data)

    return json.dumps(result_cities_list)


@timeit
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
                'coords': target_city['coords']
            }
        })
        target_cities_polygons.append(target_city['polygon'])

    if target_cities_polygons:
        logging.debug(target_cities_polygons)
        joined_cities = join_multi_to_single_poly(target_cities_polygons)

        response_object['results_combined'] = {
            'label': 'All Cities Combined',
            'bounds': joined_cities.bounds,
            'centroid': mapping(joined_cities.centroid)['coordinates'],
            'polygon': mapping(joined_cities)
        }

    return json.dumps(response_object)
