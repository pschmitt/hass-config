#!/usr/bin/env python

import argparse
from pilight import pilight

PILIGHT_HOST='10.7.0.211'

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('DEST', help='')
    parser.add_argument('ACTION', choices=['on', 'off'], help='')
    return parser.parse_args()


def pilight_send(command):
    pilight_connection = pilight.Client(host=PILIGHT_HOST)
    print('Send command {}'.format(command))
    return pilight_connection.send_code(data=command)


def get_command(dest, on=True):
    if dest == 'tv':
        c = {'protocol': ['pollin'], 'unitcode': 1, 'systemcode': 1}
        if on:
            c['on'] = 1
        else:
            c['off'] = 1
    assert c, 'Unknown device'
    return c


def turn_on(dest):
    cmd = get_command(dest, True)
    return pilight_send(cmd)


def turn_off(dest):
    cmd = get_command(dest, False)
    return pilight_send(cmd)


if __name__ == '__main__':
    args = parse_args()
    if args.ACTION == 'on':
        turn_on(args.DEST)
    elif args.ACTION == 'off':
        turn_off(args.DEST)
