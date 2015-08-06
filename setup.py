from setuptools import setup
from os import path

here = path.abspath(path.dirname(__file__))

long_description = """
A Cary command for querying the US Government per diem tables
and Google QPX to get a full trip quote; query by sending an email
with the body of several lines describing the trip, such as
  lhr-dub 20-21 july staying in Kilkenny
  dub-cdg 21-23 july
  cdg-lhr 23 jul

the parser is fairly permissive but gets tripped up periodically.
"""

setup(
    name='cary_travelcommand',
    version='1.0.0',
    description='US gov per-diem lookup for Cary',
    long_description=long_description,
    url='https://github.com/vputz/cary_travelcommand',
    author='Victor Putz',
    author_email='vputz@nyx.net',

    license='MIT',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Communications :: Email',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        ],

    keywords='email',

    packages=['cary_travelcommand'],

    install_requires=[
        'cary',
        'jinja2',
        'pyparsing',
        'google-api-python-client',
        'cary-perdiemcommand'
        ],

    extras_require={},

    package_data={
        'cary_travelcommand': ['templates/*', 'fake_estimator/*']
        },

    data_files=[],

    entry_points={
            },
)
