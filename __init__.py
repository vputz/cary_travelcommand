from cary.carycommand import CaryCommand, CaryAction
import os
from cary_perdiemcommand.perdiem_database import PerdiemDatabase
from jinja2 import Environment, FileSystemLoader, DebugUndefined
from cary_travelcommand.travel_parser import trip_parser, AirportLookup
from cary_travelcommand.travel_parser import TrainStationLookup
from cary_travelcommand.travel_calculations import adjusted_trip_costs
from cary_travelcommand import __path__ as MODULE_PATH


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


def dollars_filter(value):
    return "${0:0.2f}".format(value)


def mean_filter(value):
    return sum(value) / len(value)


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
        self.lookups = [AirportLookup(self.config['AIRPORT_DATA']),
                        TrainStationLookup(self.config['TRAIN_STATION_DATA'])]

        self.pd = PerdiemDatabase(self.config['LOCSTRING_FILENAME'],
                                  self.config['DB_FILENAME'])

        tp = trip_parser(self.lookups)
        self.trip = tp.parseString(self._message.body)
        self.costs = adjusted_trip_costs(self.trip, self.pd, self.estimators)
        self._output_filenames = []

        self._perdiem_text_plain = self.environment.get_template(
            'plaintext_template.txt'
            ).render(costs=self.costs)
        self._perdiem_text_html = self.environment.get_template(
            'html_template.html'
            ).render(costs=self.costs)

    @property
    def response_subject(self):
        return "Your travel estimate ({0})".format(self.trip[0]['staying_in'])

    @property
    def response_body(self):
        return self._perdiem_text_plain

    @property
    def response_body_html(self):
        return self._perdiem_text_html
