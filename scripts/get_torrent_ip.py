#!/usr/bin/env python
# coding: utf-8


import argparse
import re

# import GeoIP
import transmissionrpc


def parse_args():
    parser = argparse.ArgumentParser()
    # parser.add_argument('-g', '--geoip', action='store_true', default=False)
    parser.add_argument('-u', '--username', required=False)
    parser.add_argument('-p', '--password', required=False)
    parser.add_argument('-P', '--port', type=int, default=9091)
    parser.add_argument('HOSTNAME', nargs='?', default='localhost')
    return parser.parse_args()


def get_torrent_ip(hostname, port=9091, username=None, password=None):
    client = transmissionrpc.Client(hostname, port=port,
                                    user=username, password=password)
    torrents = [x for x in client.get_torrents() if x.name == 'checkmyiptorrent']
    if not torrents:
        raise RuntimeError(
            "No torrent named checkmyiptorrent found. Please "
            "visit https://torguard.net/checkmytorrentipaddress.php to get "
            "started")
    torrent = torrents[0]
    announcement = torrent.trackerStats[0].get('lastAnnounceResult')
    if not announcement:
        raise RuntimeError("The tracker has not determined our IP yet.")
    match = re.search('IP: (.*)', announcement)
    if match:
        return match.group(1)
    return announcement


# def geolocate_ip(ip_addr):
#     geoip = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)
#     return geoip.country_name_by_addr(ip_addr)


def main():
    args = parse_args()
    ip_addr = get_torrent_ip(
        hostname=args.HOSTNAME,
        port=args.port,
        username=args.username,
        password=args.password)
    print(ip_addr)
    # if args.geoip:
    #     print('{}: {}'.format(ip_addr, geolocate_ip(ip_addr)))
    # else:
    #     print(ip_addr)


if __name__ == '__main__':
    main()

# vim: set ft=python et ts=4 sw=4 :
