import argparse
import json
import logging
import sys

import oprcalc
import tba_cache

from collections import OrderedDict, defaultdict


def main(argv):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", help="event key", required=True)
    parser.add_argument("--offline", action='store_true', help="don't go to internet")
    parser.add_argument("--lazy", action='store_true', help="only go to internet if not in cache")
    args = parser.parse_args(argv)

    with tba_cache.TBACache(offline=args.offline, lazy=args.lazy) as tba:
        main_event = tba.get_event(args.event)
        print(main_event)
        year = main_event['year']
        start_date = main_event['start_date']

        team_results = defaultdict(OrderedDict) # keyed by team_key
        opr_calc_results = {}  # keyed by event_key
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

                opr_calc_result = opr_calc_results.get(event_key, None)

                if opr_calc_result is None:
                    teams_at_event = tba.get_teams_at_event(event_key)
                    for team_at_event in teams_at_event:
                        team_at_event['metrics'] = {}

                    all_matches = tba.get_matches_for_event(event_key=event_key)

                    matches = [match for match in all_matches if match['comp_level'] == 'qm']
                    matches.sort(key=lambda match: match['match_number'])

                    logging.info("processing opr for %s", event_key)

                    try:
                        oprcalc.calc(teams_at_event, matches, offense_metric_name='opr', defense_metric_name='dpr')
                    except ZeroDivisionError:
                        logging.info("divide by zero, looks like %s has not played enough yet", event_key)

                    # add more to team['metrics'] here

                    opr_calc_result = { team['key']: team['metrics'] for team in teams_at_event}
                    opr_calc_results[event_key] = opr_calc_result

                team['metrics'][event_key] = opr_calc_result[team_key]

        for team in teams:
            print(team['key'], json.dumps(team['metrics'], indent=1))



if __name__ == '__main__':
    main(sys.argv[1:])

