import argparse
import json
import logging
import sys

from collections import OrderedDict

import tba_cache


def process(tba: tba_cache.TBACache, team_key=None):
    year_data = {}
    years = tba.get_team_years_participated(team_key=team_key)
    for year in years:
        this_year_data = {
            'events': []
        }
        year_data[year] = this_year_data

        events = tba.get_team_events(team_key=team_key, year=year)

        events = sorted(events, key=lambda event: event['start_date'])

        for event in events:
            event_key = event['key']
            team_status_at_event = tba.get_team_status_at_event(team_key=team_key, event_key=event_key)
            print(f'team_key = {team_key}, event_key={event_key}, status={team_status_at_event}')
            qual_status = ""
            if team_status_at_event is not None:
                q = team_status_at_event['qual']
                if q is not None:
                    num_teams = q['num_teams']
                    rank = q['ranking']['rank']
                    qual_status = f'Ranking: {rank}/{num_teams}'

                    record_data = q['ranking']['record']
                    if record_data is not None:
                        qual_status = f'Record: {record_data["wins"]}-{record_data["losses"]}-{record_data["ties"]}, {qual_status}'
            else:
                team_status_at_event = {}


            event_data = {
                'name': event['name'],
                'start_date': event['start_date'],
                "awards": [],
                "award_types" : [],
                "status": team_status_at_event.get('overall_status_str'),
                "alliance_status": team_status_at_event.get('alliance_status_str'),
                "playoff_status": team_status_at_event.get('playoff_status_str'),
                "qual_status": qual_status
            }
            this_year_data['events'].append(event_data)

            for award in tba.get_team_awards_at_event(team_key=team_key, event_key=event_key):
                event_data['awards'].append(award['name'])
                event_data['award_types'].append(award['award_type'])

    districts = tba.get_team_districts(team_key=team_key)
    for district in districts:
        year = district['year']
        rankings = tba.get_district_rankings(district_key=district['key'])
        total = len(rankings)
        standing = None
        for ranking in rankings:
            if ranking['team_key'] == team_key:
                standing = ranking['rank']
                break
        year_data[year]['district ranking'] = f'{standing}/{total}'


    print (json.dumps(year_data, indent=1, sort_keys=True))




def main(argv):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    parser = argparse.ArgumentParser()
    parser.add_argument("--team", help="team key", required=True)
    parser.add_argument("--offline", action='store_true', help="don't go to internet")
    parser.add_argument("--lazy", action='store_true', help="only go to internet if not in cache")
    args = parser.parse_args(argv)

    logging.info ("invoked with %s", args)

    with tba_cache.TBACache(offline=args.offline, lazy=args.lazy) as tba:
        process(tba, args.team)

if __name__ == '__main__':
    main(sys.argv[1:])
