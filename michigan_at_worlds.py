import argparse
import copy
import csv
import json
import logging
import sys

import tba_cache

from collections import OrderedDict, defaultdict


def record(d):
    return f"{d['wins']}-{d['losses']}-{d['ties']}"


def process_an_event(tba, district_team_dict, result_key, event):
    event_key = event['key']
    # get info from team statuses
    team_statuses: dict = tba.get_team_statuses_at_event(event_key)
    for team_key, team_status in team_statuses.items():
        # print (team_key, json.dumps(team_status))
        if team_key in district_team_dict.keys():
            stats = {
                'division': event_key,
                'alliance': team_status.get('alliance_status_str'),
            }

            quals = team_status['qual']
            if quals is not None:
                stats['quals'] = record(quals['ranking']['record'])
                stats['qual_wins'] = quals['ranking']['record']['wins']
                stats['ranking'] = quals['ranking']['rank']
                stats['ranking_str'] = f"{quals['ranking']['rank']}/{quals['num_teams']}"

            playoffs = team_status['playoff']
            if playoffs is not None:
                stats['playoffs'] = record(playoffs['record'])
                stats['playoff_wins'] = playoffs['record']['wins']

            district_team_dict[team_key][result_key] = stats


def process(tba, year=None):
    district_teams = copy.deepcopy(tba.get_district_teams_simple(f"{year}fim"))
    district_teams.sort(key=lambda team: team['team_number'])
    district_team_dict = {team['key']: team for team in district_teams}

    division_events = []
    cmp_event = None
    all_events = tba.get_events_simple(year)
    for event in all_events:
        event_type = event.get('event_type', None)
        if event_type == 3:
            division_events.append(event)
        elif event_type == 4:
            cmp_event = event

    for event in division_events:
        process_an_event(tba, district_team_dict, 'div', event)

    process_an_event(tba, district_team_dict, 'cmp', cmp_event)

    for team in district_teams:
        if team.get('div', None) is not None:
            print(team['key'], json.dumps(team['div']))

    for team in district_teams:
        if team.get('cmp', None) is not None:
            print(team['key'], json.dumps(team['cmp']))

    return district_teams

def main(argv):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, help="year to analyze")
    parser.add_argument("--offline", action='store_true', help="don't go to internet")
    parser.add_argument("--lazy", action='store_true', help="only go to internet if not in cache")
    args = parser.parse_args(argv)

    logging.info ("invoked with %s", args)

    with tba_cache.TBACache(offline=args.offline, lazy=args.lazy) as tba:
        teams = process(tba, args.year)

    field_names = OrderedDict()
    field_names['team_number'] = 1
    field_names['nickname'] = 1
    for team in teams:
        if team.get('div', None) is not None:
            for k, v in team['div'].items():
                team[f'div_{k}'] = v
                field_names[f'div_{k}'] = 1

    with open(str(args.year) + '_cmp_results.csv', 'w', newline='') as file:
        c = csv.DictWriter(file, fieldnames=field_names.keys(), extrasaction='ignore')
        c.writeheader()
        for team in teams:
            if team.get('div', None) is not None:
                c.writerow(team)


if __name__ == '__main__':
    main(sys.argv[1:])
