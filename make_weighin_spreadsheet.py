import argparse
import logging
import copy
import csv
import sys

import jsonpath_ng

import tba_cache


jsonpath_cache = {}


def jsonpath_parse(json_expression_text):
    rv = jsonpath_cache.get(json_expression_text, None)
    if rv is None:
        jsonpath_cache[json_expression_text] = rv = jsonpath_ng.parse(json_expression_text)
    return rv


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

        team_dict = {}
        for team in team_array:
            team_dict[team['key']] = team

        match_array = tba.get_matches_for_event(args.event)

        for match in match_array:
            comp_level = match['comp_level']
            if comp_level != 'qm':
                continue

            json_find_results = (jsonpath_parse('*..team_keys').find(match))
            # print(json_find_results)
            match_number = match['match_number']
            for json_find_result in json_find_results:
                for team_key in json_find_result.value:
                    team = team_dict[team_key]
                    team['last_match'] = max(team.get('last_match', -1), match_number)

    teams = list(team_dict.values())
    teams.sort(key=lambda team: team['team_number'])
    with open(args.event + '_weighin.csv', 'w', newline='') as file:
        c = csv.DictWriter(file, fieldnames=['team_number','nickname', 'last_match'], extrasaction='ignore')
        c.writeheader()
        for team in teams:
            c.writerow(team)


if __name__ == '__main__':
    main(sys.argv[1:])
