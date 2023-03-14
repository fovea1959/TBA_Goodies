import argparse
import csv
import json
import logging
import sys

import oprcalc
import tba_cache

from collections import OrderedDict, defaultdict

def linkpoints_metric_extractor(match, color):
    return match['score_breakdown'][color]['linkPoints']


def autochargestationpoints_metric_extractor(match, color):
    return match['score_breakdown'][color]['autoChargeStationPoints']


def other(color):
    if color == 'red':
        return 'blue'
    return 'red'


chargeStationMap = str.maketrans("DPN", "Xx.");


def fillInChargeStation(match):
    rv = defaultdict(dict)
    for color in ['red', 'blue']:
        alliance_array = match['alliances'][color]['team_keys']
        auto_states = [ match['score_breakdown'][color][f'autoChargeStationRobot{i}'][:1] for i in range(1, 4)]
        endgame_states = [ match['score_breakdown'][color][f'endGameChargeStationRobot{i}'][:1] for i in range(1, 4)]

        for team_key, a, e in zip(alliance_array, auto_states, endgame_states):
            rv[team_key]['autoCharge'] = a.translate(chargeStationMap)
            rv[team_key]['endGameCharge'] = e.translate(chargeStationMap)
    return rv


def main(argv):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", help="event key", required=True)
    parser.add_argument("--offline", action='store_true', help="don't go to internet")
    parser.add_argument("--lazy", action='store_true', help="only go to internet if not in cache")
    args = parser.parse_args(argv)

    with tba_cache.TBACache(offline=args.offline, lazy=args.lazy) as tba:
        main_event = tba.get_event(args.event)
        year = main_event['year']
        start_date = main_event['start_date']

        competition_results = {}  # keyed by event_key
        teams = tba.get_teams_at_event(args.event)
        for team in teams:
            team_key = team['key']
            team['metrics'] = {}
            events = tba.get_events_for_team(team_key, year)
            # find district events that start before the one we want to scout
            events = list(filter(lambda event: event['event_type_string'] == 'District' and event['start_date'] < start_date, events))
            events.sort(key=lambda event: event['start_date'])
            for event in events:
                event_key = event['key']

                competition_result = competition_results.get(event_key, None)

                if competition_result is None:
                    teams_at_event = tba.get_teams_at_event(event_key)
                    metric_dict = {}
                    for team_at_event in teams_at_event:
                        metric_dict[team_at_event['key']] = team_at_event['metrics'] = {}

                    all_matches = tba.get_matches_for_event(event_key=event_key)

                    matches = [match for match in all_matches if match['comp_level'] == 'qm']
                    matches.sort(key=lambda match: match['match_number'])

                    logging.info ("processing opt for %s, %d teams, %d matches", event_key, len(teams_at_event), len(matches))

                    try:
                        # fill metrics into teams_at_event
                        oprcalc.calc(teams_at_event, matches, offense_metric_name='opr')
                        #oprcalc.calc(teams_at_event, matches, offense_metric_name='linkPoints_pr',
                        #oprcalc.calc(teams_at_event, matches, offense_metric_name='opr', defense_metric_name='dpr')
                        #oprcalc.calc(teams_at_event, matches, offense_metric_name='linkPoints_pr',
                        #             metric_extractor=linkpoints_metric_extractor)
                        #oprcalc.calc(teams_at_event, matches, offense_metric_name='autoChargeStationPoints_pr',
                        #             metric_extractor=autochargestationpoints_metric_extractor)
                    except ZeroDivisionError:
                        logging.info("divide by zero, looks like %s has not played enough yet", event_key)

                    competition_result = { team['key']: team['metrics'] for team in teams_at_event}

                    # add more to competition_result[team_key] here
                    for match in matches:
                        csr = fillInChargeStation(match)
                        for csr_team_key in csr.keys():
                            for name in csr[csr_team_key].keys():
                                v = competition_result[csr_team_key].get(name, '') + csr[csr_team_key][name]
                                competition_result[csr_team_key][name] = v

                    # get info from match status
                    team_statuses: dict = tba.get_team_statuses_at_event(event_key)
                    for k, team_status in team_statuses.items():
                        if team_status is not None:
                            overall = team_status.get('overall_status_str', None)
                            if overall is not None:
                                competition_result[k]['overall_status_str'] = overall

                    competition_results[event_key] = competition_result

                cs = competition_result.get(team_key, None)
                if cs is not None:
                    team['metrics'][event_key] = cs

        field_names = OrderedDict()

        for field_name in ['team', 'event']:
            field_names[field_name] = 1

        for team in teams:
            for metrics in team['metrics'].values():
                for field_name in metrics.keys():
                    field_names[field_name] = 1

        with open('names.csv', 'w', newline='') as file:
            c = csv.DictWriter(file, fieldnames=field_names)
            c.writeheader()
            for team in teams:
                s = {'team': team['key'] }
                c.writerow(s)
                for event_key, metrics in team['metrics'].items():
                    s = {'event': event_key}
                    s.update(metrics)
                    c.writerow(s)


if __name__ == '__main__':
    main(sys.argv[1:])

