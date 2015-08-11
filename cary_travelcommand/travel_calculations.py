import datetime
import logging

def days_from_leg(leg):
    result = []
    date = leg['dates']['start']
    while date <= leg['dates']['end']:
        result.append(date)
        date = date + datetime.timedelta(days=1)
    return result


def season_for_day(day, seasons):
    cmpday = datetime.datetime(day.year, day.month, day.day)
    for season in seasons:
        eff_date = datetime.datetime.strptime(season['eff_date'], "%m/%d/%Y")
        exp_date = datetime.datetime.strptime(season['exp_date'], "%m/%d/%Y")
        if (cmpday >= eff_date) and (cmpday <= exp_date):
            return season
    return None


def cost_for_day(day, season):
    if season is not None:
        return dict(
            day=day,
            lodging=int(season['lodging']),
            lodging_multiplier=1.0,
            meals=int(season['meals']),
            incidentals=int(season['incidentals']),
            mie_multiplier=1.0
            )
    else:
        return None


def perdiem_costs_by_query(days, query):

    if not query['found']:
        result = dict(
            searched_location=query['original_search_location'],
            travel_cost=None,
            matched_location=None
            )
    else:
        topmatch = query['closest_matches'][0]
        result = dict(
            searched_location=query['original_search_location'],
            score=topmatch['score'],
            travel_cost=None,
            matched_location=topmatch['location'],
            dates=[cost_for_day(
                day,
                season_for_day(day, topmatch['seasons']))
                for day in days]
            )
    return result


def perdiem_costs(days, location, pd_db):
    return perdiem_costs_by_query(days, pd_db.perdiem_query(location))


def trip_costs_by_perdiems(trip, perdiems):
    """
    Takes a trip (list of legs, leg->(route, dates, staying_in))
    and a list of perdiem queries the
    same length as the number of legs,
    returns [leg->(route,costs,staying_in)]
    """
    assert(len(trip) == len(perdiems))

    def calc_legs(trip, perdiems):
        return [dict(route=leg['route'],
                     dates=leg['dates'],
                     staying_in=leg['staying_in'],
                     costs=perdiem_costs_by_query(days_from_leg(leg), perdiem))
                     for (leg, perdiem) in zip(trip, perdiems)]

    def set_last_day_lodging(legs):
        for leg in legs:
            costs = leg['costs']
            if costs['matched_location'] is not None:
                # you're not staying in lodging on the last day
                costs['dates'][-1]['lodging_multiplier'] = 0.0

    def set_travel_mie(leg, date_index):
        if leg['costs']['matched_location'] is not None:
            leg['costs']['dates'][date_index]['mie_multiplier'] = 0.75

    legs = calc_legs(trip, perdiems)
    set_last_day_lodging(legs)
    set_travel_mie(legs[0], 0)
    set_travel_mie(legs[-1], -1)
    return legs


def trip_costs(trip, pd_db, threshold):
    perdiems = [pd_db.perdiem_query(leg['staying_in'], threshold=threshold) 
                for leg in trip]
    for leg_pd in perdiems:
        logging.debug("Returned {0} matches, top being {1}".format(
            len(leg_pd['closest_matches']),
            leg_pd['closest_matches'][0] if leg_pd['found'] else "NO MATCH"
        ))
    legs = trip_costs_by_perdiems(
        trip,
        perdiems
        )
    return legs


def calculated_trip_costs(trip_costs, route_estimators=[]):
    result = trip_costs.copy()
    # walk through the trip and calculate

    def route_costs(leg, estimators):
        for est in estimators:
            route = leg['route']
            if est.services(route['mode']):
                return est.single_estimate(route['start'],
                                           route['end'],
                                           leg['dates']['start'])
        return None

    def set_route_cost(leg, estimators):
        leg['costs']['travel_cost'] = route_costs(leg, estimators)

    def set_actual_perdiem_costs(leg):
        if leg['costs']['matched_location'] is not None:
            for day in leg['costs']['dates']:
                day['lodging_actual'] = day['lodging']\
                  * day['lodging_multiplier']
                day['mie_actual'] = (day['meals'] + day['incidentals']) \
                  * day['mie_multiplier']

    for leg in result:
        set_route_cost(leg, route_estimators)
        set_actual_perdiem_costs(leg)

    return result


def adjusted_trip_costs(trip, pd_db, route_estimators=[], threshold=90):
    result = trip_costs(trip, pd_db, threshold=threshold)
    return calculated_trip_costs(result, route_estimators)
    return result
