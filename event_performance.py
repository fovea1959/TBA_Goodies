import argparse
import copy
import csv
import json
import logging
import sys

from collections import OrderedDict, defaultdict

import jsonpath_ng

import tba_cache


def main(argv):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", help="event key", required=True)
    parser.add_argument("--offline", action='store_true', help="don't go to internet")
    parser.add_argument("--lazy", action='store_true', help="only go to internet if not in cache")
    args = parser.parse_args(argv)

    logging.info ("invoked with %s", args)

    field_names = OrderedDict()
    for field_name in ('team', 'match', 'color'):
        field_names[field_name] = 1

    all_jsonpath_expr = jsonpath_ng.parse('$..*')
    team_keys_jsonpath_expr = jsonpath_ng.parse('team_keys')
    values = []
    match_summaries = []
    with tba_cache.TBACache(offline=args.offline, lazy=args.lazy) as tba:
        matches = tba.get_matches_for_event(event_key=args.event)
        for match in matches:
            for color in ('blue', 'red'):
                alliance_values = { 'match': match.get('key'), 'color': color, 'time': match.get('time') }
                for datum in all_jsonpath_expr.find(match['score_breakdown'][color]):
                    if type(datum.value) == dict:
                        continue

                    alliance_values[datum.full_path] = datum.value
                    field_names[datum.full_path] = 1
                for datum in team_keys_jsonpath_expr.find(match['alliances'][color]):
                    teams = datum.value
                    for team in teams:
                        team_values = copy.deepcopy(alliance_values)
                        team_values['team'] = team.removeprefix("frc")
                        values.append(team_values)
            if match['comp_level'] == 'qm':
                ms = []
                for color in ('blue', 'red'):
                    score = match['score_breakdown'][color]['total_points']
                    ms.append(score)
                all_match_scores.append(ms)

    values.sort(key = lambda x: x.get('time'))
    with open(args.event + '_event.csv', 'w', newline='', encoding='utf-8') as file:
        c = csv.DictWriter(file, fieldnames=field_names, extrasaction='ignore')
        c.writeheader()
        c.writerows(values)

    with open(args.event + '_event.json', 'w') as file:
        json.dump(all_match_scores, file, indent=1)


if __name__ == '__main__':
    main(sys.argv[1:])
