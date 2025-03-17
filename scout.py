import argparse
import copy
import csv
import logging
import sys

import oprcalc
import tba_cache

from collections import OrderedDict, defaultdict


def linkpoints_metric_extractor(match, color):
    return match['score_breakdown'][color]['linkPoints']


def rankingpoints_metric_extractor(match, color):
    return match['score_breakdown'][color]['rp']


def autochargestationpoints_metric_extractor(match, color):
    return match['score_breakdown'][color]['autoChargeStationPoints']


def teleopAmpNotePoints_metric_extractor(match, color):
    return match['score_breakdown'][color]['teleopAmpNotePoints']


def foulPoints_metric_extractor(match, color):
    return match['score_breakdown'][color]['foulPoints']


def other(color):
    if color == 'red':
        return 'blue'
    return 'red'


chargeStationMap = str.maketrans("DPN", "Xx.")


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


def rank_teams_at_event(teams_at_event, metric_name, descending_order=True):
    sorted_by = sorted(teams_at_event, key=lambda t: t['metrics'][metric_name], reverse=descending_order)
    for i, team in enumerate(sorted_by):
        team['metrics'][metric_name + "_ranking"] = f'{str(i+1)}/{str(len(sorted_by))}'


def process(tba, main_event_key=None):
    main_event = tba.get_event(main_event_key)
    year = main_event['year']
    start_date = main_event['start_date']

    competition_results = {}  # keyed by event_key
    teams = copy.deepcopy(tba.get_teams_at_event(main_event_key))
    teams.sort(key=lambda team: team['team_number'])
    for team in teams:
        team_key = team['key']

        team['metrics'] = { }
        events = tba.get_events_for_team(team_key, year)
        # find district events that start before the one we want to scout
        events = list(filter(lambda event: event['start_date'] < start_date, events))
        events.sort(key=lambda event: event['start_date'])
        for event in events:
            event_key = event['key']
            event_name = event['short_name']

            competition_result = competition_results.get(event_key, None)

            if competition_result is None:
                teams_at_event = tba.get_teams_at_event(event_key)

                all_matches = tba.get_matches_for_event(event_key=event_key)
                matches = [match for match in all_matches if match['comp_level'] == 'qm' and match['actual_time'] is not None]
                matches.sort(key=lambda match: match['match_number'])

                logging.info ("processing metrics for %s, %d teams, %d matches", event_key, len(teams_at_event), len(matches))

                metric_dict = {}
                for team_at_event in teams_at_event:
                    metric_dict[team_at_event['key']] = team_at_event['metrics'] = { 'event_name': event_name }

                if len(matches) > 0:
                    stuff_to_grab = [
                        (oprcalc.MetricExtractor('totalPoints'), True, 'opr', 'dpr')
                    ]
                    if year == 2023:
                        # needs work
                        oprcalc.calc(teams_at_event, matches, offense_metric_name='linkPoints_pr',
                                     metric_extractor=linkpoints_metric_extractor)
                        oprcalc.calc(teams_at_event, matches, offense_metric_name='autoChargeStationPoints_pr',
                                     metric_extractor=autochargestationpoints_metric_extractor)
                    elif year == 2024:
                        # needs work
                        oprcalc.calc(teams_at_event, matches, offense_metric_name='teleopAmpNotePoints_pr',
                                     metric_extractor=teleopAmpNotePoints_metric_extractor)
                        oprcalc.calc(teams_at_event, matches, offense_metric_name='foulPoints_pr',
                                     metric_extractor=foulPoints_metric_extractor)
                    elif year == 2025:
                        stuff_to_grab.extend([
                            (oprcalc.MetricExtractor('autoPoints'), True, 'autoPoints', None),
                            (oprcalc.MetricExtractor('teleopPoints'), True, 'teleopPoints', None),
                            (oprcalc.MetricExtractor('algaePoints'), True, 'algaePoints', None),
                            (oprcalc.MetricExtractor('autoCoralPoints'), True, 'autoCoralPoints', None),
                            (oprcalc.MetricExtractor('teleopCoralPoints'), True, 'teleopCoralPoints', None),
                            (oprcalc.MetricExtractor('autoBonusAchieved'), True, 'autoBonusAchieved', None),
                            (oprcalc.MetricExtractor('bargeBonusAchieved'), True, 'bargeBonusAchieved', None),
                            (oprcalc.MetricExtractor('coralBonusAchieved'), True, 'coralBonusAchieved', None),
                        ])

                    for me, descending_order, omn, dmn in stuff_to_grab:
                        # fill metrics into teams_at_event
                        oprcalc.calc(teams_at_event, matches, metric_extractor=me, offense_metric_name=omn, defense_metric_name=dmn)

                        if omn is not None:
                            # need to look for the ranking for the omn measure
                            rank_teams_at_event(teams_at_event, omn, descending_order=descending_order)

                        if dmn is not None:
                            # need to look for the ranking for the dmn measure
                            rank_teams_at_event(teams_at_event, dmn, descending_order=descending_order)

                competition_result = { team['key']: team['metrics'] for team in teams_at_event}

                # add more to competition_result[team_key] here
                if year == 2023:
                    for match in matches:
                        csr = fillInChargeStation(match)
                        for csr_team_key in csr.keys():
                            for name in csr[csr_team_key].keys():
                                v = competition_result[csr_team_key].get(name, '') + csr[csr_team_key][name]
                                competition_result[csr_team_key][name] = v

                # get info from team statuses
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

    return teams


def main(argv):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", help="event key", required=True)
    parser.add_argument("--offline", action='store_true', help="don't go to internet")
    parser.add_argument("--lazy", action='store_true', help="only go to internet if not in cache")
    args = parser.parse_args(argv)

    logging.info ("invoked with %s", args)

    with tba_cache.TBACache(offline=args.offline, lazy=args.lazy) as tba:
        teams = process(tba, args.event)

    field_names = OrderedDict()

    for field_name in ['team', 'name', 'event', 'event_name', 'overall_status_str']:
        field_names[field_name] = 1

    team_dict = OrderedDict()
    for team in teams:
        team_dict[team['key']] = team
        for metrics in team['metrics'].values():
            for field_name in metrics.keys():
                field_names[field_name] = 1

    with open(args.event + '_scout.csv', 'w', newline='', encoding='utf-8') as file:
        c = csv.DictWriter(file, fieldnames=field_names)
        c.writeheader()
        for i, team in enumerate(teams):
            if i > 0:
                c.writerow({})
            s = {'team': team['key'], 'name': team['nickname']}
            if len(team['metrics']) == 0:
                c.writerow(s)
            else:
                for event_key, metrics in team['metrics'].items():
                    s1 = { 'event': event_key }
                    s1.update(s)
                    s1.update(metrics)
                    c.writerow(s1)


if __name__ == '__main__':
    main(sys.argv[1:])
