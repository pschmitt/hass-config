#!/usr/bin/env python

import os
import re
import yaml

basedir = os.path.realpath(os.path.dirname(__file__))

HASS_SECRETS_FILE = os.path.join(basedir, '../config/hass/secrets.yaml')
TRAVIS_SECRETS_FILE = os.path.join(
    basedir, '../config/hass/.travis/secrets.yaml')

TRAVIS_FLOAT = 0.0
TRAVIS_INT = 0
TRAVIS_STR = 'travis_secret_16'
TRAVIS_FILE = './config/hass/.travis/file'

with open(HASS_SECRETS_FILE, 'r') as stream:
    hass_config = yaml.load(stream)

travis_config = {}

mac_addr_re = re.compile(r'([0-9a-fA-F]{2}[:]){5}([0-9a-fA-F]{2})')
url_re = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|'
                     '(?:%[0-9a-fA-F][0-9a-fA-F]))+')

for k, v in hass_config.items():
    t = type(v)
    if t == float:
        travis_val = TRAVIS_FLOAT
    elif t == int:
        travis_val = TRAVIS_INT
    elif t == str:
        if v.startswith('/'):
            travis_val = TRAVIS_FILE
        elif re.match(mac_addr_re, v):
            travis_val = '00:01:02:03:04:05'
        elif re.match(url_re, v):
            travis_val = 'http://localhost:8080/index.html'
        else:
            travis_val = TRAVIS_STR
    travis_config[k] = travis_val

with open(TRAVIS_SECRETS_FILE, 'w') as outfile:
    yaml.dump(travis_config, outfile, default_flow_style=False)
    print('Wrote travis secret file to {}'.format(
        os.path.realpath(outfile.name)))
