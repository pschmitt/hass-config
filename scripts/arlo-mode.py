#!/usr/bin/env python
# coding: utf-8


import argparse
import sys
import yaml
from pyarlo import PyArlo


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', '-u')
    parser.add_argument('--password', '-p')
    parser.add_argument('--config', '-c',
                        type=argparse.FileType('r'),
                        default='/config/secrets.yaml')
    parser.add_argument('MODE')
    return parser.parse_args()


def arlo_mode(username, password, mode):
    arlo = PyArlo(username, password)
    base = arlo.base_stations[0]
    available_modes = base.available_modes
    if mode not in available_modes:
        raise RuntimeError("No such mode: {}\n"
                           "Available Modes: {}".format(
                               mode,
                               available_modes))
    base.mode = mode


if __name__ == '__main__':
    ARGS = parse_args()
    USERNAME = ARGS.username
    PASSWORD = ARGS.password
    if not PASSWORD:
        CONFIG = yaml.load(ARGS.config)
        USERNAME = CONFIG.get('arlo_username')
        PASSWORD = CONFIG.get('arlo_password')
    if not PASSWORD:
        print("Credentials are required, set them either via -u "
              "and -p or a secrets file (-c)", file=sys.stderr)
    else:
        arlo_mode(USERNAME, PASSWORD, ARGS.MODE)
