from abc import abstractmethod, ABCMeta
import csv
from pyparsing import *
import datetime
import logging

class RoutePointLookup(metaclass=ABCMeta):
    """
    A simple class for looking up start->end endpoints and providing
    a per diem matching string for them
    """

    def __init__():
        pass

    @abstractmethod
    def is_valid_endpoint(self, endpoint):
        return None

    def is_valid_route(self, start, end):
        return self.is_valid_endpoint(start) and self.is_valid_endpoint(end)

    @abstractmethod
    def per_diem_locstring(self, endpoint):
        return None

    @property
    @abstractmethod
    def mode(self):
        return None


class AirportLookup(RoutePointLookup):
    # openflight.org airports.dat file has columns
    # 0 : index
    # 1 : airport name
    # 2 : city
    # 3 : country
    # 4 : IATA 3-letter
    # 5 : ICAO 4-letter

    def __init__(self, filename=None, from_dict=None):
        self.airports = {}
        if filename is not None:
            self.add_airports_from_file(filename)
        if from_dict is not None:
            self.add_airports_from_dict(from_dict)

    @property
    def mode(self):
        return "air"

    def add_airports_from_dict(self, d):
        self.airports.update(d)

    def add_airports_from_file(self, filename):
        """uses CSV file cut/pasted from http://answers.google.com/answers/threadview?id=182498"""
        with open(filename) as f:
            r = csv.DictReader(f)
            for row in r:
                identifier = row['code']
                if identifier != '':
                    self.airports[identifier] = dict(
                        name=row['name'],
                        city=row['city'],
                        state=row['state'],
                        country=row['country']
                        )

    def is_valid_endpoint(self, endpoint):
        return endpoint in self.airports

    def per_diem_locstring(self, endpoint):
        assert self.is_valid_endpoint(endpoint)
        airport = self.airports[endpoint]
        if airport['country'] == 'USA':
            return ", ".join([airport['city'], airport['state'],
                              airport['country']])
        else:
            return ", ".join([airport['city'], airport['country']])


class TrainStationLookup(RoutePointLookup):
    # train stations--use LOC file from atoc, but there are
    # multiple records; we want the set of CRS codes
    # Location records have length

    def __init__(self, filename=None, from_dict=None):
        self.stations = {}
        if filename is not None:
            self.add_stations_from_file(filename)
        if from_dict is not None:
            self.add_stations_from_dict(from_dict)

    @property
    def mode(self):
        return "rail"

    def add_stations_from_dict(self, d):
        self.stations.update(d)

    def add_stations_from_file(self, filename):
        with open(filename) as f:
            for r in f.readlines():
                if len(r) == 290:
                    id = r[56:59].strip()
                    city = r[144:204]
                    if id != '':
                        self.stations[id] = dict(city=city,
                                                 name=city,
                                                 country="United Kingdom")

    def is_valid_endpoint(self, endpoint):
        return endpoint in self.stations

    def per_diem_locstring(self, endpoint):
        assert self.is_valid_endpoint(endpoint)
        station = self.stations(endpoint)
        return ", ".join(station.city, station.country)


TEST_AIRPORTS = dict(
    LHR=dict(city="London",
             name="London Heathrow",
             country="United Kingdom"),
    DUB=dict(city="Dublin",
             name="Dublin",
             country="Ireland"),
    IAD=dict(city="Washington",
             name="Dulles International",
             country="United States")
    )

TestAirportLookup=AirportLookup(from_dict=TEST_AIRPORTS)

TEST_TRAINS = dict(
    KGX=dict(city="London",
             name="Kings Cross",
             country="United Kingdom"),
    CBG=dict(city="Cambridge",
             name="Cambridge",
             country="United Kingdom"),
    PAD=dict(city="London",
             name="Paddington",
             country="United Kingdom"),
    OXF=dict(city="Oxford",
             name="Oxford",
             country="United Kingdom")
    )

TestTrainLookup=TrainStationLookup(from_dict=TEST_TRAINS)


###
# PyParsing code
def route_parser(lookups):
    # airport = oneOf(airports, caseless=True)
    # train_station = oneOf(trains, caseless=True)
    loc = Word(alphas, min=3, max=3)
    loc.setParseAction(lambda s, l, t:
                       [tok.upper() for tok in t])

    route_connector = oneOf("- ->")

    route = loc.setResultsName("start")\
      + Optional(route_connector).suppress() + loc.setResultsName("end")

    def route_mode(start, end):
        for lookup in lookups:
            if lookup.is_valid_route(start,end):
                return lookup.mode

    route.setParseAction(lambda s, l, t:
                             dict(
                                 start=t.start,
                                 end=t.end,
                                 mode=route_mode(t.start, t.end)))

    return route


def month_parser():
    monthLookup = {
        "jan": 1,
        "january": 1,
        "feb": 2,
        "february": 2,
        "mar": 3,
        "march": 3,
        "apr": 4,
        "april": 4,
        "may": 5,
        "jun": 6,
        "june": 6,
        "jul": 7,
        "july": 7,
        "aug": 8,
        "august": 8,
        "sep": 9,
        "september": 9,
        "oct": 10,
        "october": 10,
        "nov": 11,
        "november": 11,
        "dec": 12,
        "december": 12
        }

    def monthNumToMonth(s, l, t):
        m = t[0].lower()
        if m in monthLookup:
            return monthLookup[m]
        else:
            raise TypeError

    month = oneOf(list(monthLookup.keys()), caseless=True)
    month.setParseAction(monthNumToMonth)
    return month


def year_guess(today, guess_month, guess_day):
    # right now returns current year; we really want
    # the year of the next time the month comes round
    guess_with_current_year = datetime.date(today.year, guess_month, guess_day)

    if today <= guess_with_current_year:
        return today.year
    else:
        return today.year + 1


def year_guess_today(guess_month, guess_day):
    return year_guess(datetime.date.today(),
                      guess_month, guess_day)

datesep = oneOf("- /")


def strToInt(s, l, t):
    try:
        return int(t[0])
    except Exception as e:
        raise e


def date_parser():

    day = Word(nums).setParseAction(strToInt)
    year = Word(nums).setParseAction(strToInt)
    nummonth = Word(nums).setParseAction(strToInt)

    def dateToDate(s, l, t):
        try:
            year = t.year if 'year' in t else year_guess_today(t.month, t.day)
            return datetime.date(year, t.month, t.day)
        except TypeError as e:
            logging.error(repr(e))
            raise e

    date_v1 = year.setResultsName("year")\
      + Optional(datesep).suppress()\
      + nummonth.setResultsName("month")\
      + Optional(datesep).suppress()\
      + day.setResultsName("day")

    date_v2 = day.setResultsName("day")\
      + month_parser().setResultsName("month")\
      + Optional(year).setResultsName("year")

    date = date_v2 | date_v1
    date.setParseAction(dateToDate)
    return date


def date_range_parser():
    def date_range_v1_parse(s, l, t):
        end_date = t.end if t.end != '' else t.start
        return dict(start=t.start, end=end_date)

    dates_separator = oneOf("- to")

    date_range_v1 = date_parser().setResultsName("start") \
      + Optional((dates_separator).suppress()\
                 + date_parser().setResultsName("end"))
    date_range_v1.setParseAction(date_range_v1_parse)

    def date_range_v2_parse(s, l, t):
        try:
            # for date range v2, "1-2 jul [year]" we assume the same month for
            # both days
            start_month = t.start_month if t.start_month != "" else t.end_month
            end_day = t.end_day if t.end_day != '' else t.start_day
            year = t.year if t.year != "" else year_guess_today(t.end_month, end_day)
            return dict(start=datetime.date(year, start_month, t.start_day),
                        end=datetime.date(year, t.end_month, end_day))
        except Exception as e:
            raise e

    day = Word(nums).setParseAction(strToInt)
    year = Word(nums).setParseAction(strToInt)

    date_range_v2 = day.setResultsName("start_day")\
      + Optional(month_parser().setResultsName("start_month"))\
      + Optional(dates_separator).suppress()\
      + Optional(day).setResultsName("end_day")\
      + month_parser().setResultsName("end_month")\
      + Optional(year).setResultsName("year")

    date_range_v2.setParseAction(date_range_v2_parse)

    date_range = date_range_v2 | date_range_v1

    return date_range


def trip_leg_parser(lookups):
    anyloc = OneOrMore(Word(alphas)) \
      + Optional(OneOrMore(CaselessLiteral(",").suppress()
                           + OneOrMore(Word(alphas))))
    anyloc.setParseAction(lambda s, l, t: ", ".join(t))
    trip_leg = Optional(route_parser(lookups).setResultsName("route")) \
      + date_range_parser().setResultsName("dates") \
      + Optional(Optional("staying").suppress()
                 + CaselessLiteral("in").suppress()
                 + anyloc.setResultsName("staying_in"))

    def staying_in_location(route):
        for lookup in lookups:
            if route['mode'] == lookup.mode:
                return lookup.per_diem_locstring(route['end'])
        return None

    def legdict(s, l, t):
        result = {}
        if 'route' in t and t.route != '':
            result['route'] = t.route
        if 'dates' in t and t.dates != '':
            result['dates'] = t.dates
        if 'staying_in' in t and t.staying_in != '':
            result['staying_in'] = t.staying_in
        else:
            result['staying_in'] = staying_in_location(t.route)
        return result

    trip_leg.setParseAction(legdict)
    return trip_leg


def trip_parser(lookups):
    ParserElement.setDefaultWhitespaceChars(" \t")
    t = trip_leg_parser(lookups)

    trip_parser = t + ZeroOrMore(LineEnd().suppress() + t)
    return trip_parser

