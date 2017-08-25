#!/usr/bin/env python

import os
import yaml

HASS_SECRETS_FILE = '../config/secrets.yaml'
TRAVIS_SECRETS_FILE = '../config/.travis/secrets.yaml'

TRAVIS_FLOAT = 0.0
TRAVIS_INT = 0
TRAVIS_STR = 'travis_secret'
TRAVIS_FILE = './config/.travis/file'

with open(HASS_SECRETS_FILE, 'r') as stream:
    hass_config = yaml.load(stream)

travis_config = {}

for k, v in hass_config.items():
    t = type(v)
    if t == float:
        travis_val = TRAVIS_FLOAT
    elif t == int:
        travis_val = TRAVIS_INT
    elif t == str:
        if v.startswith('/'):
            travis_val = TRAVIS_FILE
        else:
            travis_val = TRAVIS_STR
    travis_config[k] = travis_val

with open(TRAVIS_SECRETS_FILE, 'w') as outfile:
    yaml.dump(travis_config, outfile, default_flow_style=False)
    print('Wrote travis secret file to {}'.format(
        os.path.realpath(outfile.name)))
