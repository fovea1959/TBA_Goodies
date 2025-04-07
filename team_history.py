import argparse
import json
import logging
import sys

import jsonpath_ng

import tba_cache

class JsonpathCache(dict):
    def __missing__(self, key):
        return jsonpath_ng.parse(key)


jsonpath_cache = JsonpathCache()


def process(tba: tba_cache.TBACache, team_key=None):
    year_data = {}
    years = tba.get_team_years_participated(team_key=team_key)
    for year in years:
        this_year_data = {
            'year': year,
            'events': []
        }
        year_data[year] = this_year_data

        events = tba.get_team_events(team_key=team_key, year=year)

        events = sorted(events, key=lambda event: event['start_date'])

        for event in events:
            print("ev>", json.dumps(event, sort_keys=True))
            event_key = event['key']
            team_status_at_event = tba.get_team_status_at_event(team_key=team_key, event_key=event_key)
            print("t@>", json.dumps(team_status_at_event, sort_keys=True))
            print(f'team_key = {team_key}, event_key={event_key}, status={team_status_at_event}')
            qual_status = ""
            qual_record = {}
            if team_status_at_event is not None:
                q = team_status_at_event['qual']
                if q is not None:
                    num_teams = q['num_teams']
                    rank = q['ranking']['rank']
                    qual_status = f'Ranking: {rank}/{num_teams}'

                    qual_record = q['ranking']['record']
            else:
                team_status_at_event = {}

            playoff_record_j = jsonpath_cache['playoff.record'].find(team_status_at_event)
            if len(playoff_record_j) == 1:
                playoff_record = playoff_record_j[0].value
            elif len(playoff_record_j) == 0:
                playoff_record = {}
            else:
                raise Exception()

            print("qr>", json.dumps(qual_record, sort_keys=True))
            print("pr>", json.dumps(playoff_record, sort_keys=True))

            event_data = {
                'short_name': event['short_name'],
                'name': event['name'],
                'start_date': event['start_date'],
                'event_key': event.get('key'),
                'event_type': event.get('event_type'),
                'event_type_string': event.get('event_type_string'),
                "awards": [],
                "award_types" : [],
                "status": team_status_at_event.get('overall_status_str'),
                "alliance_status": team_status_at_event.get('alliance_status_str'),
                "playoff_status": team_status_at_event.get('playoff_status_str'),
                'qual_record': qual_record,
                'playoff_record': playoff_record,
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
        s = year_data[year]['district_size'] = len(rankings)
        standing = None
        for ranking in rankings:
            if ranking['team_key'] == team_key:
                standing = ranking['rank']
                break
        year_data[year]['district_ranking'] = standing
        year_data[year]['district_percentile'] = (1 - ((standing - 1) / s)) * 100.0

    with open(f'{team_key}_history.json', 'w') as f:
        json.dump(year_data, f, indent=1, sort_keys=True)



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
