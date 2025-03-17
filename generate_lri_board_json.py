import argparse
import logging
import copy
import json
import sys

import tba_cache


def main(argv):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", help="event key", required=True)
    parser.add_argument("--offline", action='store_true', help="don't go to internet")
    parser.add_argument("--lazy", action='store_true', help="only go to internet if not in cache")
    args = parser.parse_args(argv)

    logging.info ("invoked with %s", args)

    with tba_cache.TBACache(offline=args.offline, lazy=args.lazy) as tba:
        team_array = copy.deepcopy(tba.get_teams_at_event(args.event))
        logging.info ("got %d teams", len(team_array))

        output_filename = f'{args.event}_teams.json'
        with open(output_filename, 'w') as f:
            json.dump(team_array, f, indent=2, sort_keys=True)


if __name__ == '__main__':
    main(sys.argv[1:])
