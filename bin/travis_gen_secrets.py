#!/usr/bin/env python
# coding: utf-8

import os
import re
import random
import string
import yaml

BASEDIR = os.path.realpath(os.path.dirname(__file__))

HASS_SECRETS_FILE = os.path.join(BASEDIR, '../config/hass/secrets.yaml')
TRAVIS_SECRETS_FILE = os.path.join(
    BASEDIR, '../config/hass/.travis/secrets.yaml')

TRAVIS_FLOAT = 0.0
TRAVIS_INT = 0
TRAVIS_STR = 'travis_secret_16'
TRAVIS_FILE = './config/hass/.travis/file'
TRAVIS_IP_ADDR = '127.0.0.1'
TRAVIS_MAC_ADDR = '00:01:02:03:04:05'
TRAVIS_URL = 'http://localhost:8080/index.html'

with open(HASS_SECRETS_FILE, 'r') as stream:
    HASS_CONFIG = yaml.load(stream)

TRAVIS_CONFIG = {}

MAC_ADDR_RE = re.compile(r'([0-9a-fA-F]{2}[:]){5}([0-9a-fA-F]{2})')
IP_ADDR_RE = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
URL_RE = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|'
                    r'[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')


def generate_random_token(length, token='trav1ss3cr3t'):
    return (token * (int(length / len(token)) + 1))[:length]


for k, v in HASS_CONFIG.items():
    t = type(v)
    if t == float:
        travis_val = TRAVIS_FLOAT
    elif t == int:
        travis_val = TRAVIS_INT
    elif t == str:
        if v.startswith('/'):
            travis_val = TRAVIS_FILE
        elif re.match(MAC_ADDR_RE, v):
            travis_val = TRAVIS_MAC_ADDR
        elif re.match(IP_ADDR_RE, v):
            travis_val = TRAVIS_IP_ADDR
        elif re.match(URL_RE, v):
            travis_val = TRAVIS_URL
        elif 'token' in k:
            travis_val = generate_random_token(len(v))
        else:
            travis_val = TRAVIS_STR
    TRAVIS_CONFIG[k] = travis_val

with open(TRAVIS_SECRETS_FILE, 'w') as outfile:
    yaml.dump(TRAVIS_CONFIG, outfile, default_flow_style=False)
    print('Wrote travis secret file to {}'.format(
        os.path.realpath(outfile.name)))
