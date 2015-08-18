Feature: Travel command

  Scenario Outline: check for date range parsing

    Given a date range <drange>
    And a date parser
    Then check the parsed range matches a <spec>

    Examples:
    | drange                     | spec |
    | 26-27 jul 2013             | A    |
    | 26 Jul-27 Jul 2013         | A    |
    | 2013/07/26-2013/07/27      | A    |
    | 26 Jul 2013 to 27 Jul 2013 | A    |
    | 26 to 27 jul 2013          | A    |
    | 31 Jan to 2 feb 2014       | B    |
    | 20 Jan to 20 Jan 2015      | C    |
    | 20 Jan 2015                | C    |

  Scenario Outline: check for travel leg parsing

    Given a <leg>
    And a trip leg parser
    Then check it matches a <spec>

    Examples:
    | leg                                                   | spec |
    | lhr->dub 26-27 Jul 2013                               | A    |
    | lhr - dub 2013/07/26-2013/07/27                       | A    |
    | lhr->dub 26 Jul 2013 to 27 Jul 2013                   | A    |
    | 5 May 2014 to 7 May 2014 in Manchester                | B    |
    | 4-6 jun 2016 in Baltimore, MD, USA                    | C    |
    | 4-6 jun 2016 staying in wright-patterson afb, OH, USA | D    |


  Scenario Outline: check route parsing
    Given a <route>
    Then check it has the right <start>, <end>, and <mode>

    Examples:
    | route    | start | end | mode |
    | lhr->dub | LHR   | DUB | air  |
    | kgx-cbg  | KGX   | CBG | rail |


  Scenario Outline: check for airport table code lookup
    Given a dict from airport csv
    Then check that for <identifier> we get the right <locstring>

    Examples:
    | identifier | locstring              |
    | LHR        | London, United Kingdom |
    | IAD        | Washington, DC, USA    |


  Scenario: get days from leg
    Given leg "31 Jan 2015 to 2 Feb 2015 in Manchester"
    And a date range
    Then check days

  Scenario: get costs from leg
    Given a sample perdiem query
    And a date range
    And a sample cost
    And a sample adjusted cost
    And a sample trip leg
    Then check it matches sample costs
    And check adjusted costs match sample adjusted costs

  Scenario: check costs with failed perdiem lookups
    Given a failed perdiem query
    And a date range
    And a sample cost
    And a sample trip leg
    And sample failed calculated costs
    Then check the result reflects the data not found

  Scenario: check fake estimator
    Given a test estimator
    Then check a test flight can be estimated
