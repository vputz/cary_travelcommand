Cary_travelcommand
------------------

A Cary command which accepts as the body a series of "travel legs"
in the form

```
lhr->dub 4-8 aug 2015 staying in Kilkenny, Ireland
dub->lhr 8 Aug 2015
```

The `staying in` clause is optional and Cary will attempt to use the destination
of that leg as the overnight stay.  It is fairly flexible on routing, but
still makes mistakes.  It attempts to return a travel estimate with leg
travel costs based on a configurable set of estimators and daily lodging and
other per diem costs based on DoD travel tables.

The airline travel costs are estimated via Google's QPX API, and requires a
developer API key.

Requirements
------------

Cary_travelcommand relies on `cary_perdiemcommand` to look up per diem tables.
It also relies on `jinja2` and `pyparsing`.

For the QPX estimator, the google API client is also required (`google-api-python-client`)

Configuration
-------------

In your Cary `local_conf.py` file, please include configuration similar to the following
(this repeats some data such as the locstring and db from Cary_perdiemcommand.
If `TEMPLATE_PATH` is omitted, the default templates from the module will be used.

```
QPX_API_KEY = "my_api_key"

from travel_costs import make_test_estimator, QPXCostEstimator
TRAVEL_CONFIG = dict(
    LOCSTRING_FILENAME=PERDIEM_CONFIG['LOCSTRING_FILENAME'],
    DB_FILENAME=PERDIEM_CONFIG['DB_FILENAME'],
    TEMPLATE_PATH="/home/vputz/cary/plugin_data/travel",  # optional!
    AIRPORT_DATA="/path/to/airports.csv",
    TRAIN_STATION_DATA="/path/to/train_locations.txt",
    cost_estimators=[QPXCostEstimator(QPX_API_KEY)]
    )
```
