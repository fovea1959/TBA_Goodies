import argparse
import copy
import csv
import logging
import sys

import oprcalc
import tba_cache

from collections import OrderedDict, defaultdict


def process(tba, main_event_key=None, load_avatars=False):
    main_event = tba.get_event(main_event_key)
    year = main_event['year']

    teams = copy.deepcopy(tba.get_teams_at_event(main_event_key))
    for team in teams:
        team_key = team['key']
        tba.make_avatar(team_key=team_key, year=year)


def main(argv):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", help="event key", required=True)
    parser.add_argument("--offline", action='store_true', help="don't go to internet")
    parser.add_argument("--lazy", action='store_true', help="only go to internet if not in cache")
    args = parser.parse_args(argv)

    logging.info ("invoked with %s", args)

    with tba_cache.TBACache(offline=args.offline, lazy=args.lazy) as tba:
        process(tba, args.event)

if __name__ == '__main__':
    main(sys.argv[1:])
