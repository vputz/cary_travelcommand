from cary.carycommand import CaryCommand, CaryAction
import os
from cary_perdiemcommand.perdiem_database import PerdiemDatabase
from jinja2 import Environment, FileSystemLoader, DebugUndefined
from cary_travelcommand.travel_parser import trip_parser, AirportLookup
from cary_travelcommand.travel_parser import TrainStationLookup
from cary_travelcommand.travel_calculations import adjusted_trip_costs
from cary_travelcommand import __path__ as MODULE_PATH
import logging

class TravelCommand(CaryCommand):

    @property
    def name(self):
        return "travel"

    @property
    def description(self):
        return "Attempt a travel quote"

    @property
    def required_attachments(self):
        return ["trip as lines of text in body of message"]

    def _create_action(self, parsed_message):
        return TravelAction(parsed_message)


def lodgingcost_filter(leg):
    return sum([day['lodging_actual'] for day in leg['costs']['dates']
                if leg['costs']['matched_location'] is not None])


def miecost_filter(leg):
    return sum([day['mie_actual'] for day in leg['costs']['dates']
                if leg['costs']['matched_location'] is not None])


def dollars_filter(value):
    return "${0:0.2f}".format(value)


def mean_filter(value):
    return sum(value) / len(value)


def trip_travel_cost(costs):
    def leg_travel_cost(leg):
        travel_cost = leg['costs']['travel_cost']
        return mean_filter(travel_cost['fares']) if travel_cost['found'] else 0
    return sum([leg_travel_cost(leg) for leg in costs])


def trip_lodging_cost(costs):
    return sum([lodgingcost_filter(leg) for leg in costs
                if leg['costs']['matched_location'] is not None])


def trip_mie_cost(costs):
    return sum([miecost_filter(leg) for leg in costs
                if leg['costs']['matched_location'] is not None])


def trip_total_cost(costs):
    return trip_travel_cost(costs) \
      + trip_lodging_cost(costs) \
      + trip_mie_cost(costs)


def poor_matches_exist(costs):
    return len(poor_matches(costs)) > 0


def poor_matches(costs):
    return [leg['costs']['searched_location'] for leg in costs
            if (leg['costs']['matched_location'] is None)
            or (leg['costs']['score'] < 90 if 'score' in leg['costs'] else False)]


class TravelAction(CaryAction):

    def __init__(self, parsed_message):
        super().__init__(parsed_message)

    def validate_command(self):
        """
        The echo command always succeeds.
        """
        self.command_is_valid = True

    @property
    def template_path(self):
        return self.config['TEMPLATE_PATH'] if 'TEMPLATE_PATH' in self.config \
          else os.path.join(MODULE_PATH[0], 'templates')

    @property
    def threshold(self):
        return self.config['PERDIEM_THRESHOLD'] \
            if 'PERDIEM_THRESHOLD' in self.config \
               else 90

    def execute_action(self):
        self.estimators = self.config['cost_estimators'] \
          if 'cost_estimators' in self.config else []
        self.environment = Environment(loader=FileSystemLoader(
            self.template_path
            ),
            undefined=DebugUndefined
            )
        self.environment.filters['dollars'] = dollars_filter
        self.environment.filters['mean'] = mean_filter
        self.environment.filters['lodgingcost'] = lodgingcost_filter
        self.environment.filters['miecost'] = miecost_filter
        self.environment.filters['trip_travel_cost'] = trip_travel_cost
        self.environment.filters['trip_lodging_cost'] = trip_lodging_cost
        self.environment.filters['trip_mie_cost'] = trip_mie_cost
        self.environment.filters['trip_total_cost'] = trip_total_cost
        self.lookups = [AirportLookup(self.config['AIRPORT_DATA']),
                        TrainStationLookup(self.config['TRAIN_STATION_DATA'])]

        self.pd = PerdiemDatabase(self.config['LOCSTRING_FILENAME'],
                                  self.config['DB_FILENAME'])

        tp = trip_parser(self.lookups)
        self.trip = tp.parseString(self._message.body)
        logging.debug("seeking adjusted trip costs with threshold {0}".format(
            self.threshold))
        self.costs = adjusted_trip_costs(self.trip, self.pd, self.estimators,
                                         self.threshold)
        self._output_filenames = []

        self._perdiem_text_plain = self.environment.get_template(
            'plaintext_template.txt'
            ).render(costs=self.costs,
                     poor_matches_exist=poor_matches_exist(self.costs),
                     poor_matches=poor_matches(self.costs)
                     )
        self._perdiem_text_html = self.environment.get_template(
            'html_template.html'
            ).render(costs=self.costs,
                     poor_matches_exist=poor_matches_exist(self.costs),
                     poor_matches=poor_matches(self.costs)
                     )

    @property
    def response_subject(self):
        return "Your travel estimate ({0})".format(self.trip[0]['staying_in'])

    @property
    def response_body(self):
        return self._perdiem_text_plain

    @property
    def response_body_html(self):
        return self._perdiem_text_html
