from abc import abstractmethod, ABCMeta, abstractproperty
from apiclient.discovery import build
import logging
import json
from cary_travelcommand import __path__ as MODULE_PATH
import os

class RouteCostEstimator(metaclass=ABCMeta):

    @abstractmethod
    def single_estimate(self, start, end, date):
        """
        Basic cost estimate for one traveller
        """
        return None

    @abstractmethod
    def roundtrip_estimate(self, start, end, date_out, date_back):
        return None

    def services(self, mode):
        """
        whether or not this estimator services this mode of travel
        """
        return mode in self.travel_modes_serviced

    @abstractproperty
    def travel_modes_serviced(self):
        return []

    @abstractproperty
    def name(self):
        return "Base"

    @property
    def error_response(self):
        return dict(found=False)


class QPXCostEstimator(RouteCostEstimator):

    def __init__(self, api_key, max_solutions=20):
        self.service = build("qpxExpress", "v1", developerKey=api_key)
        self.trips = self.service.trips()
        self.max_solutions = max_solutions

    @property
    def name(self):
        return "Google QPX"

    @property
    def travel_modes_serviced(self):
        return ['air']

    def execute_request(self, body):
        self.last_request_body = body
        self.last_request = self.trips.search(body=self.last_request_body)
        self.last_response = self.last_request.execute()

    def single_estimate(self, start, end, date):
        body = {
            "request": {
                "slice": [
                    {
                        "origin": start,
                        "destination": end,
                    "date": date.strftime("%Y-%m-%d")
                    }
                    ],
                    "passengers": {
                        "adultCount": 1,
                        "infantInLapCount": 0,
                        "infantInSeatCount": 0,
                        "childCount": 0,
                        "seniorCount": 0
                        },
                        "saleCountry": "US",
                        "solutions": self.max_solutions,
                        "refundable": False
                        }
            }
        try:
            self.execute_request(body)
            return self.last_formatted_response()
        except Exception as e:
            logging.error(repr(e))
            return self.error_response

    def roundtrip_estimate(self, start, end, date_out, date_back):
        body = {
            "request": {
                "slice": [
                    {
                        "origin": start,
                        "destination": end,
                    "date": date_out.strftime("%Y-%m-%d")
                    },
                    {
                        "origin": end,
                        "destination": start,
                    "date": date_back.strftime("%Y-%m-%d")
                    },
                    ],
                    "passengers": {
                        "adultCount": 1,
                        "infantInLapCount": 0,
                        "infantInSeatCount": 0,
                        "childCount": 0,
                        "seniorCount": 0
                        },
                        "saleCountry": "US",
                        "solutions": self.max_solutions,
                        "refundable": False
                        }
            }
        try:
            self.execute_request(body)
            return self.last_formatted_response()
        except Exception as e:
            logging.error(repr(e))
            return self.error_response

    def last_formatted_response(self):
        """
        We're mostly interested in aggregate data, so just return a
        dictionary of
        {found:bool, fares: [float in dollars], supplemental_data: {response}
        """
        def usd_to_float(usd):
            return float(usd[3:])

        def option_price(option):
            return sum([usd_to_float(price['saleTotal']) for price in option['pricing']])

        def option_prices(resp):
            return [option_price(option) for option in resp['trips']['tripOption']]

        return dict(
            found=True,
            estimator=self.name,
            fares=option_prices(self.last_response),
            supplemental_data=self.last_response.copy()
            )


class FakeQPXCostEstimator(QPXCostEstimator):

    def __init__(self,
                 api_key,
                 single_request_filename,
                 roundtrip_request_filename,
                 single_response_filename,
                 roundtrip_response_filename):
        super().__init__(api_key)
        self.single_request = json.load(open(single_request_filename))
        self.roundtrip_request = json.load(open(roundtrip_request_filename))
        self.single_response = json.load(open(single_response_filename))
        self.roundtrip_response = json.load(open(roundtrip_response_filename))

    @property
    def name(self):
        return "FakeQPXCostEstimator"

    def single_estimate(self, start, end, date):
        slice = self.single_request['request']['slice'][0]
        if slice['origin']==start and slice['destination'] == end :
            self.last_response = self.single_response.copy()
            return self.last_formatted_response()
        else:
            return self.error_response

    def roundtrip_estimate(self, start, end, date_out, date_back):
        outslice = self.single_request['request']['slice'][0]
        backslice = self.single_request['request']['slice'][0]
        if outslice['origin'] == start and outslice['destination'] == end \
          and backslice['origin'] == end and backslice['destination'] == start :
            self.last_response = self.roundtrip_response.copy()
            return self.last_formatted_response()
        else:
            return self.error_response


def make_test_estimator():
    base = os.path.join(MODULE_PATH[0], "fake_estimator")

    def fakeFile(path):
        return os.path.join(base, path)

    print(base)
    return FakeQPXCostEstimator("nokey",
                                fakeFile("sample_single_request.json"),
                                fakeFile("sample_roundtrip_request.json"),
                                fakeFile("sample_single_response.json"),
                                fakeFile("sample_roundtrip_response.json"))
