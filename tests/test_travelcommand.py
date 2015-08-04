from pytest_bdd import scenario, given, then, parsers
from cary_travelcommand.travel_parser import TestAirportLookup, TestTrainLookup, trip_leg_parser
from cary_travelcommand.travel_parser import route_parser, AirportLookup, date_range_parser
from cary_travelcommand.travel_calculations import days_from_leg, perdiem_costs_by_query
from cary_travelcommand.travel_calculations import calculated_trip_costs, trip_costs_by_perdiems
from cary_travelcommand.travel_costs import make_test_estimator
from cary_perdiemcommand.perdiem_database import PerdiemDatabase
import datetime


@scenario('travelcommand.feature', 'check for date range parsing')
def test_date_range():
    pass


@given('a date range <drange>')
def drange(drange):
    return drange


@given('a date parser')
def sample_date_parser():
    return date_range_parser()


@then('check the parsed range matches a <spec>')
def check_parsed_range(drange, sample_date_parser, spec):
    pr = sample_date_parser.parseString(drange)
    specs = {'A': {'start': datetime.date(2013, 7, 26),
                   'end': datetime.date(2013, 7, 27)},
            'B': {'start': datetime.date(2014, 1, 31),
                  'end': datetime.date(2014, 2, 2)}
                  }
    assert pr[0] == specs[spec]


@scenario('travelcommand.feature', 'check route parsing')
def test_route_parser():
    pass


@given('a <route>')
def route(route):
    return route


@then('check it has the right <start>, <end>, and <mode>')
def check_route(route, start, end, mode):
    parser = route_parser([TestAirportLookup, TestTrainLookup])
    p = parser.parseString(route)
    assert(p[0]['start'] == start)
    assert(p[0]['end'] == end)
    assert(p[0]['mode'] == mode)


@scenario('travelcommand.feature', 'check for travel leg parsing')
def test_travel_parser():
    pass


@given(parsers.parse('leg "{leg}"'))
@given('a <leg>')
def leg(leg):
    return leg


@given('a trip leg parser')
def trip_leg_test_parser():
    return trip_leg_parser([TestAirportLookup, TestTrainLookup])


@then('check it matches a <spec>')
def check_leg_matches_spec(trip_leg_test_parser, leg, spec):
    p = trip_leg_test_parser.parseString(leg)

    specs = {'A': {'route': {'start': 'LHR',
                             'end': 'DUB',
                             'mode': 'air'},
                    'dates': {'start': datetime.date(2013, 7, 26),
                              'end': datetime.date(2013, 7, 27)},
                    'staying_in': 'Dublin, Ireland'},
            'B': {'dates': {'start': datetime.date(2014, 5, 5),
                            'end': datetime.date(2014, 5, 7)},
                    'staying_in': 'Manchester'},
            'C': {'dates': {'start': datetime.date(2016, 6, 4),
                            'end': datetime.date(2016, 6, 6)},
                    'staying_in': 'Baltimore, MD, USA'}}

    assert p[0] == specs[spec]


@scenario('travelcommand.feature', 'check for airport table code lookup')
def test_airport_lookup():
    pass


@given('a dict from airport csv')
def airport_lookup():
    return AirportLookup(filename="plugin_data/travel/airports.csv")


@then('check that for <identifier> we get the right <locstring>')
def check_airport_lookup(airport_lookup, identifier, locstring):
    assert airport_lookup.per_diem_locstring(identifier) == locstring


@scenario('travelcommand.feature', 'get days from leg')
def test_days_from_leg():
    pass


@given('a date range')
def sample_date_range():
    return [datetime.date(2015, 1, 31),
            datetime.date(2015, 2, 1),
            datetime.date(2015, 2, 2)]


@then('check days')
def check_days(trip_leg_test_parser, sample_date_range, leg):
    days = days_from_leg(trip_leg_test_parser.parseString(leg)[0])
    assert days == sample_date_range


@given('a sample perdiem query')
def sample_perdiem_query():
    return {'found': True,
            'conus_url': 'http://www.defensetravel.dod.mil/Docs/perdiem/browse/Allowances/Per_Diem_Rates/Relational/CONUS/conusallhist2015.zip',
            'actual_queried_location': 'manchester, united kingdom',
            'original_search_location': 'manchester, united kingdom',
            'currency_check': {'conus_last': '01 April 2015',
                               'oconus_latest': '01 August 2015',
                               'is_current': False,
                               'oconus_last': '01 July 2015',
                               'conus_latest': '01 April 2015'},
            'oconus_url': 'http://www.defensetravel.dod.mil/Docs/perdiem/browse/Allowances/Per_Diem_Rates/Relational/OCONUS/ocallhist-15.zip',
            'closest_matches': [{'seasons': [{'incidentals': '24',
                                              'meals': '120',
                                              'eff_date': '10/01/2014',
                                              'exp_date': '01/31/2015',
                                              'lodging': '214',
                                              'prop_meals': '55'},
                                              {'incidentals': '23',
                                               'meals': '114',
                                               'eff_date': '02/01/2015',
                                               'exp_date': '06/30/2015',
                                               'lodging': '202',
                                              'prop_meals': '53'},
                                              {'incidentals': '23',
                                               'meals': '116',
                                              'eff_date': '07/01/2015',
                                              'exp_date': '12/31/2049',
                                              'lodging': '208',
                                              'prop_meals': '54'}],
                                              'score': 100,
                                              'location': 'MANCHESTER, GBR'}]}


@scenario('travelcommand.feature', 'get costs from leg')
def test_costs_from_leg():
    pass


@given('a sample cost')
def sample_costs():
    return {'matched_location': 'MANCHESTER, GBR',
            'dates': [
                {'meals': 120,
                 'incidentals': 24,
                 'lodging_multiplier': 1.0,
                'day': datetime.date(2015, 1, 31),
                'mie_multiplier': 1.0, 'lodging': 214},
                {'meals': 114,
                 'incidentals': 23,
                 'lodging_multiplier': 1.0,
                'day': datetime.date(2015, 2, 1),
                'mie_multiplier': 1.0,
                'lodging': 202},
                {'meals': 114,
                 'incidentals': 23,
                'lodging_multiplier': 1.0,
                'day': datetime.date(2015, 2, 2),
                'mie_multiplier': 1.0, 'lodging': 202}],
            'travel_cost': None}


@given('a sample adjusted cost')
def sample_adjusted_costs():
    return [{'staying_in': 'Manchester',
             'route': None,
             'dates': {'start': datetime.date(2015, 1, 31),
                       'end': datetime.date(2015, 2, 2)},
             'costs': {'dates':
                       [{'lodging': 214,
                         'meals': 120,
                         'mie_actual': 108.0,
                         'lodging_actual': 214.0,
                         'day': datetime.date(2015, 1, 31),
                         'incidentals': 24,
                         'lodging_multiplier': 1.0,
                         'mie_multiplier': 0.75},
                         {'lodging': 202,
                        'meals': 114,
                       'mie_actual': 137.0,
                       'lodging_actual': 202.0,
                         'day': datetime.date(2015, 2, 1),
                         'incidentals': 23,
                         'lodging_multiplier': 1.0,
                         'mie_multiplier': 1.0},
                       {'lodging': 202,
                        'meals': 114,
                       'mie_actual': 102.75,
                       'lodging_actual': 0.0,
                       'day': datetime.date(2015, 2, 2),
                       'incidentals': 23,
                       'lodging_multiplier': 0.0,
                       'mie_multiplier': 0.75}],
            'matched_location': 'MANCHESTER, GBR',
            'travel_cost': None}}]


@then('check it matches sample costs')
def check_sample_costs(sample_perdiem_query, sample_date_range, sample_costs):
    costs = perdiem_costs_by_query(sample_date_range, sample_perdiem_query)
    assert costs == sample_costs


@given('a sample trip leg')
def sample_trip_leg(sample_costs):
    return {'route': None,
            'dates': {'start': datetime.date(2015, 1, 31),
                      'end': datetime.date(2015, 2, 2)},
            'staying_in': "Manchester"}


@then('check adjusted costs match sample adjusted costs')
def check_adjusted_costs(sample_costs,
                         sample_adjusted_costs,
                         sample_trip_leg,
                         sample_perdiem_query):
    adjusted = calculated_trip_costs(
        trip_costs_by_perdiems([sample_trip_leg],
                               [sample_perdiem_query]))
    assert adjusted == sample_adjusted_costs


@scenario('travelcommand.feature', 'check costs with failed perdiem lookups')
def test_failed_perdiem_lookup():
    pass


@given('a failed perdiem query')
def failed_perdiem_query():
    return {'oconus_url': 'http://www.defensetravel.dod.mil/Docs/perdiem/browse/Allowances/Per_Diem_Rates/Relational/OCONUS/ocallhist-15.zip',
            'original_search_location': 'FROBNITZ, SNORDONIA',
            'found': False,
            'currency_check': {'is_current': False,
                               'conus_latest': '01 April 2015',
                               'oconus_last': '01 July 2015',
                               'oconus_latest': '01 August 2015',
                               'conus_last': '01 April 2015'},
            'actual_queried_location': '[other], SNORDONIA',
            'closest_matches': [],
            'conus_url': 'http://www.defensetravel.dod.mil/Docs/perdiem/browse/Allowances/Per_Diem_Rates/Relational/CONUS/conusallhist2015.zip'}


@given('sample failed calculated costs')
def sample_failed_calculated_costs():
    return [{'costs': {'matched_location': None,
                       'travel_cost': None},
            'route': None,
            'dates': {'end': datetime.date(2015, 2, 2),
                        'start': datetime.date(2015, 1, 31)},
            'staying_in': 'Manchester'}]


@then('check the result reflects the data not found')
def check_costs_for_not_found(failed_perdiem_query,
                              sample_costs,
                              sample_failed_calculated_costs,
                              sample_trip_leg):
    costs = calculated_trip_costs(
        trip_costs_by_perdiems([sample_trip_leg],
                               [failed_perdiem_query]))
    assert sample_failed_calculated_costs == costs


@scenario('travelcommand.feature', 'check fake estimator')
def test_fake_estimator():
    pass


@given('a test estimator')
def fake_estimator():
    return make_test_estimator()


@then('check a test flight can be estimated')
def check_test_estimator(fake_estimator):
    estimate = fake_estimator.single_estimate(
        "LHR",
        "DUB",
        datetime.date(2015, 8, 4))
    assert estimate['fares'][0] == 166.6
